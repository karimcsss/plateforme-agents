from typing import Literal
from pydantic import BaseModel


class ApprovalDecision(BaseModel):
    decision: Literal["approved", "rejected"]