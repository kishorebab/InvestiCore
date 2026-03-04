import uuid
from fastapi import Header, HTTPException, Depends
from typing import List, Optional

from .llm.llm_client import LLMClient, LocalLLMClient
from .config import settings


async def get_correlation_id(x_correlation_id: Optional[str] = Header(None)) -> str:
    """Reads or generates a correlation ID for tracing requests."""
    return x_correlation_id or str(uuid.uuid4())


def get_llm_client() -> LLMClient:
    """Factory for the LLM client depending on configuration."""
    # Future: inspect settings.llm_provider to decide
    if settings.llm_provider == "local":
        return LocalLLMClient()
    # stub: add other providers as needed
    raise HTTPException(status_code=500, detail="Unsupported LLM provider")


async def validate_tool_registry(tool_registry: List[str]) -> List[str]:
    if not isinstance(tool_registry, list):
        raise HTTPException(status_code=400, detail="toolRegistry must be a list")
    return tool_registry