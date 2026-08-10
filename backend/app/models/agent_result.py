from typing import Literal
from pydantic import BaseModel, Field


class Finding(BaseModel):
    claim: str = Field(description="Affirmation factuelle et vérifiable")
    evidence: list[str] = Field(description="URLs ou sources soutenant l'affirmation")
    confidence: float = Field(ge=0.0, le=1.0)


class AgentResult(BaseModel):
    agent_id: str
    status: Literal["completed", "failed", "needs_review"]
    findings: list[Finding]
    errors: list[str] = Field(default_factory=list)
    tokens_used: int = 0
    duration_ms: int = 0