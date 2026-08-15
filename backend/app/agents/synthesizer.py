from app.llm.factory import get_llm_provider
from app.models.agent_result import AgentResult
from app.models.report import Report

SYNTHESIZER_SYSTEM_PROMPT = """Tu es l'agent Synthétiseur final d'un système multi-agents.
Tu reçois l'objectif original de l'utilisateur et l'ensemble des résultats produits
par une équipe d'agents de recherche. Ta mission : produire UN rapport final,
clair et directement exploitable par l'utilisateur.

Règles strictes :
- summary : réponds DIRECTEMENT à la question posée, pas une reformulation vague.
- key_findings : uniquement des faits concrets tirés des résultats fournis, jamais inventés.
- recommendations : uniquement si la question appelle une décision ou une action ;
  sinon, laisse une liste vide.
- risks : mentionne les limites réelles (confiance faible, données manquantes,
  sources contradictoires) si elles apparaissent dans les résultats.
- sources : uniquement des URLs qui apparaissent réellement dans les evidence fournies.
- N'invente jamais une information absente des résultats fournis.
- Réponds UNIQUEMENT via l'outil emit_result.
"""


def _format_results(results: list[AgentResult]) -> str:
    blocks = []
    for r in results:
        findings_text = "\n".join(
            f"  - {f.claim} (confiance: {f.confidence}, sources: {', '.join(f.evidence) or 'aucune'})"
            for f in r.findings
        )
        blocks.append(f"Agent {r.agent_id} [{r.status}]:\n{findings_text or '  (aucun finding)'}")
    return "\n\n".join(blocks)


async def synthesize_report(objective: str, results: list[AgentResult]) -> Report:
    provider = get_llm_provider()
    user_prompt = f"""Objectif original : {objective}

Résultats de tous les agents :
{_format_results(results)}
"""
    return await provider.complete_structured(
        system_prompt=SYNTHESIZER_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        response_model=Report,
    )