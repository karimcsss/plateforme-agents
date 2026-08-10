import json
from typing import Type, TypeVar
from openai import AsyncOpenAI
from pydantic import BaseModel

from app.config import GROQ_API_KEY, GROQ_MODEL
from app.llm.base import LLMProvider

T = TypeVar("T", bound=BaseModel)


class GroqProvider(LLMProvider):
    def __init__(self, model: str = GROQ_MODEL):
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY manquante — vérifie ton .env")
        self.client = AsyncOpenAI(
            api_key=GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
        )
        self.model = model
        self.last_usage_tokens = 0

    async def complete_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[T],
    ) -> T:
        schema = response_model.model_json_schema()

        tool = {
            "type": "function",
            "function": {
                "name": "emit_result",
                "description": "Retourne le résultat structuré demandé",
                "parameters": schema,
            },
        }

        resp = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            tools=[tool],
            tool_choice={"type": "function", "function": {"name": "emit_result"}},
            temperature=0,
        )

        if resp.usage:
            self.last_usage_tokens = resp.usage.total_tokens

        tool_call = resp.choices[0].message.tool_calls[0]
        raw_args = json.loads(tool_call.function.arguments)
        return response_model.model_validate(raw_args)