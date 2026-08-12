import pytest
from app.agents.critic import review_results
from app.models.agent_result import AgentResult, Finding
from app.models.critic import CriticReview


@pytest.mark.asyncio
async def test_critic_contests_low_confidence_finding():
    results = [
        AgentResult(
            agent_id="agent_a",
            status="completed",
            findings=[Finding(claim="Fait solide bien documenté", evidence=["https://ex.com"], confidence=0.95)],
        ),
        AgentResult(
            agent_id="agent_b",
            status="needs_review",
            findings=[Finding(claim="Information incertaine et peu fiable", evidence=[], confidence=0.2)],
        ),
    ]
    review = await review_results(results)
    assert isinstance(review, CriticReview)
    contested_ids = [c.agent_id for c in review.contestations]
    assert "agent_b" in contested_ids


@pytest.mark.asyncio
async def test_critic_no_contestation_when_all_solid():
    results = [
        AgentResult(
            agent_id="agent_a",
            status="completed",
            findings=[Finding(claim="Paris est la capitale de la France", evidence=["https://ex.com"], confidence=0.98)],
        ),
    ]
    review = await review_results(results)
    assert isinstance(review, CriticReview)