from pydantic import BaseModel, Field


class Report(BaseModel):
    summary: str = Field(description="Résumé exécutif de 2-4 phrases répondant directement à la question posée")
    key_findings: list[str] = Field(description="Les faits marquants retenus, entre 2 et 6")
    recommendations: list[str] = Field(default_factory=list, description="Recommandations actionnables, si applicable au type de question")
    risks: list[str] = Field(default_factory=list, description="Limites, incertitudes ou risques identifiés")
    sources: list[str] = Field(default_factory=list, description="URLs des sources les plus pertinentes utilisées")