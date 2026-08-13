import asyncio
from app.agents.worker import run_agent
from app.agents.critic import review_results
from app.db.client import get_supabase
from app.models.plan import Plan, RequiredAgent
from app.models.agent_result import AgentResult
from app.models.critic import CriticReview
from app.observability.logger import log_event

RETRY_BUDGET_PER_RUN = 1  # global, pas par agent


def _topological_batches(agents: list[RequiredAgent]) -> list[list[RequiredAgent]]:
    """Groupe les agents en 'vagues' executables en parallele.
    Vague 0 = agents sans dependance. Vague 1 = agents dont toutes les
    dependances sont dans les vagues precedentes. Etc."""
    remaining = {a.id: a for a in agents}
    done: set[str] = set()
    batches: list[list[RequiredAgent]] = []

    while remaining:
        batch = [
            a for a in remaining.values()
            if all(dep in done for dep in a.depends_on)
        ]
        if not batch:
            raise ValueError("Dependance circulaire detectee dans le plan - devrait etre impossible")
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
    result = await run_agent(agent, context, run_id=run_id)
    await _persist_execution(run_id, result, agent.role)
    return result


async def _handle_contestations(
    run_id: str, plan: Plan, results: list[AgentResult]
) -> list[AgentResult]:
    """Fait relire les resultats par le Critique. Si conteste, re-execute
    au plus RETRY_BUDGET_PER_RUN agents (les plus faibles en confiance
    en premier), remplace leur resultat, enregistre la contestation."""
    review: CriticReview = await review_results(results)

    if not review.contestations:
        return results

    supabase = get_supabase()
    agents_by_id = {a.id: a for a in plan.required_agents}
    results_by_id = {r.agent_id: r for r in results}

    def min_confidence(agent_id: str) -> float:
        r = results_by_id.get(agent_id)
        if not r or not r.findings:
            return 1.0
        return min(f.confidence for f in r.findings)

    sorted_contestations = sorted(
        review.contestations, key=lambda c: min_confidence(c.agent_id)
    )

    retries_used = 0
    for contestation in sorted_contestations:
        if retries_used >= RETRY_BUDGET_PER_RUN:
            break
        agent = agents_by_id.get(contestation.agent_id)
        if not agent:
            continue

        context_with_contestation = (
            f"{plan.objective}\n\n"
            f"ATTENTION : ton resultat precedent a ete conteste par l'agent Critique.\n"
            f"Raison : {contestation.reason}\n"
            f"Corrige ou renforce ton finding en consequence."
        )
        new_result = await run_agent(agent, context_with_contestation, run_id=run_id)
        results_by_id[agent.id] = new_result

        supabase.table("agent_executions").update({
            "result": new_result.model_dump(),
            "status": new_result.status,
            "tokens_used": new_result.tokens_used,
            "duration_ms": new_result.duration_ms,
            "attempt": 2,
        }).eq("run_id", run_id).eq("agent_id", agent.id).execute()

        supabase.table("contestations").insert({
            "run_id": run_id,
            "agent_id": agent.id,
            "reason": contestation.reason,
            "resolved": True,
        }).execute()

        await log_event(
            run_id=run_id,
            event_type="status_change",
            agent_id=agent.id,
            payload={"event": "contestation_retry", "reason": contestation.reason},
        )

        retries_used += 1

    for contestation in sorted_contestations[retries_used:]:
        supabase.table("contestations").insert({
            "run_id": run_id,
            "agent_id": contestation.agent_id,
            "reason": contestation.reason,
            "resolved": False,
        }).execute()

    return list(results_by_id.values())


async def execute_plan(run_id: str, plan: Plan) -> list[AgentResult]:
    """Execute tout le plan : vague par vague, agents d'une meme vague
    en parallele via asyncio.gather. Puis fait relire par le Critique."""
    batches = _topological_batches(plan.required_agents)
    all_results: list[AgentResult] = []

    supabase = get_supabase()
    supabase.table("runs").update({"status": "running"}).eq("id", run_id).execute()
    await log_event(run_id=run_id, event_type="status_change", payload={"new_status": "running"})

    for batch in batches:
        batch_results = await asyncio.gather(
            *[_run_and_persist(run_id, agent, plan.objective) for agent in batch]
        )
        all_results.extend(batch_results)

    all_results = await _handle_contestations(run_id, plan, all_results)

    final_status = "completed" if all(r.status == "completed" for r in all_results) else "failed"
    supabase.table("runs").update({"status": final_status}).eq("id", run_id).execute()
    await log_event(run_id=run_id, event_type="status_change", payload={"new_status": final_status})

    return all_results