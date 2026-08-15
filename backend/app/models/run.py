from typing import Literal, Optional
from pydantic import BaseModel

from app.models.plan import Plan
from app.models.report import Report

RunStatus = Literal[
    "planning", "plan_failed", "planned", "pending_approval",
    "running", "completed", "failed", "rejected"
]


class Run(BaseModel):
    id: str
    problem_statement: str
    status: RunStatus
    plan: Optional[Plan] = None
    report: Optional[Report] = None
    error_detail: Optional[dict] = None