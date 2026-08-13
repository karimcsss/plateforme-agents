from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ValidationError

from app.agents.planner import generate_plan
from app.db.client import get_supabase
from app.llm.factory import get_llm_provider
from app.models.run import Run
from app.orchestrator.dag_runner import execute_plan

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


class RunRequest(BaseModel):
    problem_statement: str


@app.post("/runs", response_model=Run)
async def create_run(req: RunRequest):
    supabase = get_supabase()

    insert_result = (
        supabase.table("runs")
        .insert({"problem_statement": req.problem_statement, "status": "planning"})
        .execute()
    )

    if not insert_result.data:
        raise HTTPException(status_code=500, detail="Impossible de créer le run")

    run_row = insert_result.data[0]
    run_id = run_row["id"]

    try:
        plan = await generate_plan(req.problem_statement)
    except ValidationError as e:
        clean_errors = [
            {"type": err["type"], "loc": err["loc"], "msg": err["msg"]}
            for err in e.errors()
        ]
        update_result = (
            supabase.table("runs")
            .update(
                {
                    "status": "plan_failed",
                    "error_detail": {"errors": clean_errors},
                }
            )
            .eq("id", run_id)
            .execute()
        )
        return update_result.data[0]

    supabase.table("runs").update(
        {"status": "planned", "plan": plan.model_dump()}
    ).eq("id", run_id).execute()

    await execute_plan(run_id, plan)

    final_result = supabase.table("runs").select("*").eq("id", run_id).execute()
    if not final_result.data:
        raise HTTPException(status_code=404, detail="Run introuvable")
    return final_result.data[0]


@app.get("/runs/{run_id}", response_model=Run)
async def get_run(run_id: str):
    supabase = get_supabase()
    result = supabase.table("runs").select("*").eq("id", run_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Run introuvable")
    return result.data[0]

@app.get("/runs/{run_id}/logs")
async def get_run_logs(run_id: str):
    supabase = get_supabase()
    result = (
        supabase.table("execution_logs")
        .select("*")
        .eq("run_id", run_id)
        .order("created_at")
        .execute()
    )
    return result.data