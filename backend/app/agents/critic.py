import json
from app.llm.factory import get_llm_provider
from app.models.agent_result import AgentResult
from app.models.critic import CriticReview

CRITIC_SYSTEM_PROMPT = """Tu es l'agent Critique d'un système multi-agents. Ton rôle :
relire les résultats produits par plusieurs agents et repérer les faiblesses.

Conteste un finding UNIQUEMENT si :
- sa confidence est inférieure à 0.5, OU
- il contredit factuellement un finding d'un autre agent (ex: deux affirmations
  incompatibles sur le même sujet).

Ne conteste jamais un finding juste parce qu'il pourrait être plus détaillé —
seulement pour faiblesse de confiance ou contradiction réelle.

S'il n'y a rien à contester, retourne une liste `contestations` vide.
Réponds UNIQUEMENT via l'outil emit_result."""


async def review_results(results: list[AgentResult]) -> CriticReview:
    findings_summary = json.dumps(
        [
            {
                "agent_id": r.agent_id,
                "findings": [f.model_dump() for f in r.findings],
            }
            for r in results
        ],
        ensure_ascii=False,
        indent=2,
    )

    provider = get_llm_provider()
    return await provider.complete_structured(
        system_prompt=CRITIC_SYSTEM_PROMPT,
        user_prompt=f"Résultats de tous les agents à examiner :\n{findings_summary}",
        response_model=CriticReview,
    )