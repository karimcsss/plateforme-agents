import time
from app.llm.factory import get_llm_provider
from app.models.agent_result import AgentResult
from app.models.plan import RequiredAgent
from app.tools.web_search import web_search
from app.observability.logger import log_event

WORKER_SYSTEM_PROMPT = """Tu es un agent de recherche spécialisé, membre d'une équipe
d'agents IA. On te donne un rôle, un objectif, et des résultats de recherche web réels.

Ta mission : à partir UNIQUEMENT des résultats de recherche fournis, produis une liste
de "findings" — chacun étant une affirmation factuelle (claim), les sources qui la
soutiennent (evidence, une liste d'URLs tirées des résultats), et un niveau de confiance
entre 0.0 et 1.0.

Règles strictes :
- N'invente jamais un fait qui n'est pas présent dans les résultats de recherche.
- Si les résultats sont insuffisants ou contradictoires pour répondre à l'objectif,
  produis un finding avec une confidence basse (< 0.5) qui le signale explicitement.
- Chaque evidence doit être une URL réellement présente dans les résultats fournis.
- Entre 1 et 4 findings, pas plus.
- Réponds UNIQUEMENT via l'outil emit_result.
"""


async def run_agent(agent: RequiredAgent, context: str, run_id: str | None = None) -> AgentResult:
    start = time.monotonic()

    search_start = time.monotonic()
    try:
        search_results = web_search(agent.goal)
        search_latency = int((time.monotonic() - search_start) * 1000)
        if run_id:
            await log_event(
                run_id=run_id,
                event_type="tool_call",
                agent_id=agent.id,
                payload={"tool": "web_search", "query": agent.goal, "results_count": len(search_results)},
                latency_ms=search_latency,
            )
    except Exception as e:
        search_latency = int((time.monotonic() - search_start) * 1000)
        if run_id:
            await log_event(
                run_id=run_id,
                event_type="error",
                agent_id=agent.id,
                payload={"stage": "web_search", "error": str(e)},
                latency_ms=search_latency,
            )
        return AgentResult(
            agent_id=agent.id,
            status="failed",
            findings=[],
            errors=[f"Échec de la recherche web : {str(e)}"],
            duration_ms=int((time.monotonic() - start) * 1000),
        )

    if not search_results:
        return AgentResult(
            agent_id=agent.id,
            status="needs_review",
            findings=[],
            errors=["Aucun résultat de recherche trouvé pour cet objectif"],
            duration_ms=int((time.monotonic() - start) * 1000),
        )

    results_text = "\n\n".join(
        f"[{r['title']}]({r['url']})\n{r['content']}" for r in search_results
    )

    user_prompt = f"""Contexte global du problème : {context}

Ton rôle : {agent.role}
Ton objectif : {agent.goal}

Résultats de recherche web :
{results_text}
"""

    provider = get_llm_provider()
    llm_start = time.monotonic()

    try:
        raw_result = await provider.complete_structured(
            system_prompt=WORKER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=AgentResult,
        )
    except Exception as first_error:
        try:
            raw_result = await provider.complete_structured(
                system_prompt=WORKER_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_model=AgentResult,
            )
        except Exception as second_error:
            llm_latency = int((time.monotonic() - llm_start) * 1000)
            if run_id:
                await log_event(
                    run_id=run_id,
                    event_type="error",
                    agent_id=agent.id,
                    payload={
                        "stage": "llm_generation",
                        "error_attempt_1": str(first_error),
                        "error_attempt_2": str(second_error),
                    },
                    latency_ms=llm_latency,
                )
            return AgentResult(
                agent_id=agent.id,
                status="failed",
                findings=[],
                errors=[f"Échec de la génération structurée (après retry) : {str(second_error)}"],
                duration_ms=int((time.monotonic() - start) * 1000),
            )

    llm_latency = int((time.monotonic() - llm_start) * 1000)
    if run_id:
        await log_event(
            run_id=run_id,
            event_type="llm_call",
            agent_id=agent.id,
            payload={"model": provider.model},
            latency_ms=llm_latency,
            tokens_used=provider.last_usage_tokens,
        )

    raw_result.agent_id = agent.id
    raw_result.tokens_used = provider.last_usage_tokens
    raw_result.duration_ms = int((time.monotonic() - start) * 1000)
    return raw_result