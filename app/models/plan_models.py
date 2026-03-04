from __future__ import annotations
from typing import Any, Dict, List
from pydantic import BaseModel, Field, ValidationError, validator


class PlanStep(BaseModel):
    stepId: int = Field(..., description="The sequential identifier of the step")
    toolName: str = Field(..., description="The name of the tool to invoke")
    parameters: Dict[str, Any] = Field(..., description="Arguments for the tool")


class PlanningResponse(BaseModel):
    steps: List[PlanStep] = Field(..., description="Ordered list of execution steps")

    @validator("steps")
    def non_empty(cls, v: List[PlanStep]) -> List[PlanStep]:
        if not v:
            raise ValueError("steps list must contain at least one step")
        return v


class PlanningRequest(BaseModel):
    userQuery: str = Field(..., description="Investigation query from the caller")
    toolRegistry: List[str] = Field(..., description="List of available tool names")


# helper to validate arbitrary data against the response schema

def validate_planning_response(raw: Any) -> PlanningResponse:
    try:
        return PlanningResponse.parse_obj(raw)
    except ValidationError as e:
        raise e
