class ToolResultItem(BaseModel):
    toolName: str
    status: Literal["success", "failed", "timeout"]
    output: dict | None = None
    errorMessage: str | None = None
    durationMs: int

class AnalysisRequest(BaseModel):
    userQuery: str
    toolResults: list[ToolResultItem]  # TYPED, not just dict

class AnalysisResponse(BaseModel):
    rootCause: str
    evidence: list[str] = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    recommendedActions: list[str]
    toolsUsed: list[str]
    analysisNotes: str | None = None