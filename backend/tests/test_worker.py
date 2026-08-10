import pytest
from app.agents.worker import run_agent
from app.models.plan import RequiredAgent
from app.models.agent_result import AgentResult


@pytest.mark.asyncio
async def test_agent_produces_valid_result():
    agent = RequiredAgent(
        id="test_agent",
        role="Chercheur test",
        goal="Quelle est la capitale de la Tunisie ?",
        tools=["web_search"],
        depends_on=[],
    )
    result = await run_agent(agent, context="Test de recherche factuelle simple")

    assert isinstance(result, AgentResult)
    assert result.agent_id == "test_agent"
    assert result.status in ("completed", "needs_review", "failed")
    if result.status == "completed":
        assert len(result.findings) >= 1
        assert all(0.0 <= f.confidence <= 1.0 for f in result.findings)