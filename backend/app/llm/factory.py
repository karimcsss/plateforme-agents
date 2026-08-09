from app.config import LLM_PROVIDER
from app.llm.base import LLMProvider
from app.llm.groq_provider import GroqProvider


def get_llm_provider() -> LLMProvider:
    if LLM_PROVIDER == "groq":
        return GroqProvider()
    # futur : elif LLM_PROVIDER == "openrouter": return OpenRouterProvider()
    raise ValueError(f"Fournisseur LLM inconnu : {LLM_PROVIDER}")