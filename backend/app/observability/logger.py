from typing import Literal, Optional
from app.db.client import get_supabase

EventType = Literal["llm_call", "tool_call", "error", "status_change"]

# Coût par 1M tokens — 0 pour les fournisseurs gratuits actuels (Groq).
# Structure prête pour un futur fournisseur payant (OpenAI/Anthropic) sans
# changer l'appelant : seul ce dictionnaire évoluerait.
COST_PER_1M_TOKENS = {
    "groq": 0.0,
}


def estimate_cost(tokens_used: int, provider: str = "groq") -> float:
    rate = COST_PER_1M_TOKENS.get(provider, 0.0)
    return round((tokens_used / 1_000_000) * rate, 6)


async def log_event(
    run_id: str,
    event_type: EventType,
    agent_id: Optional[str] = None,
    payload: Optional[dict] = None,
    latency_ms: Optional[int] = None,
    tokens_used: int = 0,
    provider: str = "groq",
) -> None:
    """Logger centralise. Ne fait JAMAIS echouer l'appelant : une erreur de
    logging ne doit pas casser l'execution d'un agent. On avale l'exception
    et on l'affiche en console plutot que de la laisser remonter."""
    try:
        supabase = get_supabase()
        supabase.table("execution_logs").insert({
            "run_id": run_id,
            "agent_id": agent_id,
            "event_type": event_type,
            "payload": payload or {},
            "latency_ms": latency_ms,
            "tokens_used": tokens_used,
            "cost_estimate": estimate_cost(tokens_used, provider),
        }).execute()
    except Exception as e:
        print(f"[observability] echec du log (non bloquant) : {e}")