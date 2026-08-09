from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ValidationError

from app.llm.factory import get_llm_provider
from app.agents.planner import generate_plan
from app.models.plan import Plan

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


class PlanRequest(BaseModel):
    problem_statement: str


@app.post("/plan")
async def plan_endpoint(req: PlanRequest):
    """Endpoint de test du Planificateur seul, sans persistance.
    Sera remplacé par /runs à l'étape 2b."""
    try:
        return await generate_plan(req.problem_statement)
    except ValidationError as e:
        clean_errors = [
            {"type": err["type"], "loc": err["loc"], "msg": err["msg"]}
            for err in e.errors()
        ]
        raise HTTPException(
            status_code=422,
            detail={
                "error": "plan_validation_failed",
                "message": "Le plan généré par le modèle ne respecte pas les contraintes.",
                "errors": clean_errors,
            },
        )