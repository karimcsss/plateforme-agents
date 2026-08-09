from fastapi import FastAPI
from pydantic import BaseModel

from app.llm.factory import get_llm_provider

app = FastAPI(title="Plateforme Multi-Agents — API")


class EchoRequest(BaseModel):
    text: str


class EchoResult(BaseModel):
    received: str
    word_count: int
    detected_language: str


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/test-llm", response_model=EchoResult)
async def test_llm(req: EchoRequest):
    """Endpoint jetable : valide que la sortie structurée fonctionne
    avant de construire le Planificateur dessus."""
    provider = get_llm_provider()
    result = await provider.complete_structured(
        system_prompt=(
            "Tu analyses un texte et retournes des métadonnées structurées "
            "en appelant l'outil emit_result. Ne réponds jamais en texte libre."
        ),
        user_prompt=req.text,
        response_model=EchoResult,
    )
    return result