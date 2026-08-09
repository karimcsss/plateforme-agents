import pytest
from app.agents.planner import generate_plan
from app.models.plan import Plan


@pytest.mark.asyncio
async def test_plan_has_valid_agent_count():
    plan = await generate_plan(
        "Faut-il que ma startup se lance sur le marché tunisien ou marocain en premier ?"
    )
    assert isinstance(plan, Plan)
    assert 3 <= len(plan.required_agents) <= 5
    assert plan.workflow in ("dag", "sequential")


@pytest.mark.asyncio
async def test_plan_dependencies_are_valid():
    plan = await generate_plan(
        "Compare les politiques climatiques de la France, de l'Allemagne et de l'Espagne."
    )
    ids = {a.id for a in plan.required_agents}
    for agent in plan.required_agents:
        for dep in agent.depends_on:
            assert dep in ids, f"{dep} référencé mais absent du plan"


@pytest.mark.asyncio
async def test_plan_rejects_malformed_output_gracefully():
    """Ce test ne force pas une erreur, il documente juste le comportement attendu :
    si le modèle produisait un plan avec 8 agents, Pydantic doit lever ValueError
    avant que ce plan n'atteigne l'orchestrateur."""
    from pydantic import ValidationError
    from app.models.plan import Plan

    bad_data = {
        "objective": "test",
        "required_agents": [
            {"id": f"a{i}", "role": "x", "goal": "y", "tools": ["web_search"], "depends_on": []}
            for i in range(8)
        ],
        "workflow": "dag",
        "requires_human_approval": False,
        "approval_triggers": [],
    }
    with pytest.raises(ValidationError):
        Plan.model_validate(bad_data)
        