from __future__ import annotations
from typing import List, Any
from pydantic import BaseModel, Field, ValidationError


class AnalysisResponse(BaseModel):
    summary: str = Field(..., description="Brief summary of findings")
    rootCause: str = Field(..., description="Identified root cause of the issue")
    recommendedActions: List[str] = Field(..., description="Suggested next steps")
    confidenceScore: float = Field(..., ge=0.0, le=1.0, description="Confidence as 0‑1 float")

    from pydantic import field_validator

    @field_validator("recommendedActions")
    def actions_non_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("recommendedActions must contain at least one item")
        return v


class AnalysisRequest(BaseModel):
    userQuery: str = Field(..., description="Investigation query from the caller")
    toolResults: Any = Field(..., description="Results of previous tool executions")


def validate_analysis_response(raw: Any) -> AnalysisResponse:
    try:
        return AnalysisResponse.parse_obj(raw)
    except ValidationError as e:
        raise e
