import time
from app.llm.factory import get_llm_provider
from app.models.agent_result import AgentResult
from app.models.plan import RequiredAgent
from app.tools.web_search import web_search

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


async def run_agent(agent: RequiredAgent, context: str) -> AgentResult:
    """Exécute un agent : recherche web puis synthèse structurée.
    `context` = l'objectif global du problème, pour que l'agent garde
    en tête le fil du problème initial, pas seulement son propre `goal`."""
    start = time.monotonic()

    try:
        search_results = web_search(agent.goal)
    except Exception as e:
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

    class WorkerOutput(AgentResult):
        pass  # même schéma, réutilisé tel quel pour le tool calling

    try:
        raw_result = await provider.complete_structured(
            system_prompt=WORKER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=AgentResult,
        )
    except Exception as e:
        return AgentResult(
            agent_id=agent.id,
            status="failed",
            findings=[],
            errors=[f"Échec de la génération structurée : {str(e)}"],
            duration_ms=int((time.monotonic() - start) * 1000),
        )

    raw_result.agent_id = agent.id
    raw_result.tokens_used = provider.last_usage_tokens  # écrase la valeur hallucinée par la vraie
    raw_result.duration_ms = int((time.monotonic() - start) * 1000)
    return raw_result
