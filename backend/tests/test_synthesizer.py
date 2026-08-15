import pytest
from app.agents.synthesizer import synthesize_report
from app.models.agent_result import AgentResult, Finding
from app.models.report import Report


@pytest.mark.asyncio
async def test_synthesizer_produces_structured_report():
    results = [
        AgentResult(
            agent_id="researcher_a",
            status="completed",
            findings=[
                Finding(
                    claim="Paris est la capitale de la France",
                    evidence=["https://fr.wikipedia.org/wiki/Paris"],
                    confidence=0.99,
                )
            ],
        ),
        AgentResult(
            agent_id="researcher_b",
            status="completed",
            findings=[
                Finding(
                    claim="La France compte environ 68 millions d'habitants",
                    evidence=["https://insee.fr"],
                    confidence=0.9,
                )
            ],
        ),
    ]
    report = await synthesize_report("Donne des informations clés sur la France", results)

    assert isinstance(report, Report)
    assert len(report.summary) > 0
    assert len(report.key_findings) >= 1