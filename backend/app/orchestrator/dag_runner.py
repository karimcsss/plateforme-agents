import asyncio
from app.agents.worker import run_agent
from app.db.client import get_supabase
from app.models.plan import Plan, RequiredAgent
from app.models.agent_result import AgentResult


def _topological_batches(agents: list[RequiredAgent]) -> list[list[RequiredAgent]]:
    """Groupe les agents en 'vagues' exécutables en parallèle.
    Vague 0 = agents sans dépendance. Vague 1 = agents dont toutes les
    dépendances sont dans les vagues précédentes. Etc.
    C'est ce qui transforme le DAG déclaratif du Plan en un vrai plan
    d'exécution parallèle, plutôt qu'une boucle séquentielle déguisée."""
    remaining = {a.id: a for a in agents}
    done: set[str] = set()
    batches: list[list[RequiredAgent]] = []

    while remaining:
        batch = [
            a for a in remaining.values()
            if all(dep in done for dep in a.depends_on)
        ]
        if not batch:
            # Ne devrait jamais arriver : le Plan est déjà validé sans
            # dépendance circulaire à l'Étape 2. Filet de sécurité.
            raise ValueError("Dépendance circulaire détectée dans le plan — devrait être impossible")
        batches.append(batch)
        for a in batch:
            done.add(a.id)
            del remaining[a.id]

    return batches


async def _persist_execution(run_id: str, result: AgentResult, role: str) -> None:
    supabase = get_supabase()
    supabase.table("agent_executions").insert({
        "run_id": run_id,
        "agent_id": result.agent_id,
        "role": role,
        "status": result.status,
        "result": result.model_dump(),
        "tokens_used": result.tokens_used,
        "duration_ms": result.duration_ms,
    }).execute()


async def _run_and_persist(run_id: str, agent: RequiredAgent, context: str) -> AgentResult:
    result = await run_agent(agent, context)
    await _persist_execution(run_id, result, agent.role)
    return result


async def execute_plan(run_id: str, plan: Plan) -> list[AgentResult]:
    """Exécute tout le plan : vague par vague, agents d'une même vague
    en parallèle via asyncio.gather. Retourne tous les AgentResult, dans
    l'ordre d'exécution (pas nécessairement l'ordre du plan d'origine)."""
    batches = _topological_batches(plan.required_agents)
    all_results: list[AgentResult] = []

    supabase = get_supabase()
    supabase.table("runs").update({"status": "running"}).eq("id", run_id).execute()

    for batch in batches:
        batch_results = await asyncio.gather(
            *[_run_and_persist(run_id, agent, plan.objective) for agent in batch]
        )
        all_results.extend(batch_results)

    final_status = "completed" if all(r.status == "completed" for r in all_results) else "failed"
    supabase.table("runs").update({"status": final_status}).eq("id", run_id).execute()

    return all_results