from pydantic import BaseModel, Field


class Contestation(BaseModel):
    agent_id: str = Field(description="id de l'agent dont le finding est contesté")
    finding_claim: str = Field(description="le claim exact contesté, pour identifier lequel")
    reason: str = Field(description="raison de la contestation : faible confiance ou contradiction")


class CriticReview(BaseModel):
    contestations: list[Contestation] = Field(default_factory=list)