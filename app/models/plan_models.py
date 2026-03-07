from pydantic import BaseModel, Field, field_validator
from typing import Literal
import uuid

class PlanStep(BaseModel):
    stepNumber: int = Field(..., ge=1)
    toolName: str = Field(..., min_length=1)
    arguments: dict = Field(default_factory=dict)
    reasoning: str = Field(..., min_length=1)
    dependsOn: list[int] = Field(default_factory=list)

    @field_validator('toolName')
    @classmethod
    def normalize_tool_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('toolName cannot be blank')
        return v.strip().lower()

class PlanningRequest(BaseModel):
    userQuery: str = Field(..., min_length=1)
    toolRegistry: list[str] = Field(..., min_length=1)

class PlanningResponse(BaseModel):
    planId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    steps: list[PlanStep] = Field(..., min_length=1)
    overallReasoning: str
    estimatedComplexity: Literal["low", "medium", "high"] = "medium"
    confidence: float = Field(..., ge=0.0, le=1.0)