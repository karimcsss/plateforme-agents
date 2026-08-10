from typing import Literal, Optional
from pydantic import BaseModel

from app.models.plan import Plan

RunStatus = Literal["planning", "plan_failed", "planned", "running", "completed", "failed"]


class Run(BaseModel):
    id: str
    problem_statement: str
    status: RunStatus
    plan: Optional[Plan] = None
    error_detail: Optional[dict] = None