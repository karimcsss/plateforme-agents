from abc import ABC, abstractmethod
from typing import Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMProvider(ABC):
    """Contrat commun à tous les fournisseurs LLM.
    N'importe quel provider (Groq, OpenRouter, OpenAI, Anthropic)
    doit implémenter cette interface. Rien dans le reste du système
    ne doit connaître le provider concret."""

    @abstractmethod
    async def complete_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
    ) -> T:
        """Force le LLM à répondre selon le schéma Pydantic donné."""
        ...