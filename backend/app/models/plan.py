from typing import Literal, Union
from pydantic import BaseModel, Field, field_validator


class RequiredAgent(BaseModel):
    id: str = Field(description="Identifiant court unique, ex: 'researcher_market'")
    role: str = Field(description="Titre du rôle, ex: 'Analyste de marché'")
    goal: str = Field(description="Objectif précis et actionnable de cet agent")
    tools: list[Literal["web_search"]]
    depends_on: list[str] = Field(default_factory=list)


ApprovalTrigger = Literal["high_cost", "low_confidence", "high_ambiguity"]


class Plan(BaseModel):
    objective: str = Field(description="Reformulation claire de l'objectif global")
    required_agents: list[RequiredAgent]
    workflow: Literal["dag", "sequential"]
    requires_human_approval: Union[bool, str]
    approval_triggers: list[ApprovalTrigger] = Field(default_factory=list)

    @field_validator("requires_human_approval", mode="before")
    @classmethod
    def coerce_bool(cls, v):
        if isinstance(v, str):
            return v.strip().lower() == "true"
        return v

    @field_validator("required_agents")
    @classmethod
    def validate_agent_count(cls, v: list[RequiredAgent]) -> list[RequiredAgent]:
        if not (3 <= len(v) <= 5):
            raise ValueError(
                f"Le plan doit contenir entre 3 et 5 agents (MVP), reçu : {len(v)}"
            )
        return v

    @field_validator("required_agents")
    @classmethod
    def validate_dependencies_exist(cls, v: list[RequiredAgent]) -> list[RequiredAgent]:
        ids = {a.id for a in v}
        for agent in v:
            for dep in agent.depends_on:
                if dep not in ids:
                    raise ValueError(
                        f"L'agent '{agent.id}' dépend de '{dep}' qui n'existe pas dans le plan"
                    )
                if dep == agent.id:
                    raise ValueError(f"L'agent '{agent.id}' ne peut pas dépendre de lui-même")
        return v

    @field_validator("required_agents")
    @classmethod
    def validate_max_dependency_depth(cls, v: list[RequiredAgent]) -> list[RequiredAgent]:
        agents_by_id = {a.id: a for a in v}

        def depth(agent_id: str, seen: set[str]) -> int:
            agent = agents_by_id[agent_id]
            if not agent.depends_on:
                return 0
            if agent_id in seen:
                raise ValueError(f"Dépendance circulaire détectée impliquant '{agent_id}'")
            return 1 + max(depth(dep, seen | {agent_id}) for dep in agent.depends_on)

        for agent in v:
            if depth(agent.id, set()) > 2:
                raise ValueError(
                    f"Chaîne de dépendances trop profonde pour '{agent.id}' (max 2 niveaux en MVP)"
                )
        return v