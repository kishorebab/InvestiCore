import uuid
from fastapi import Header, HTTPException, Depends
from typing import List, Optional

from .llm.llm_client import LLMClient
from .llm.ollama_client import OllamaClient          # real Phi-3 client
from .agents.planning_agent import PlanningAgent
from .agents.analysis_agent import AnalysisAgent
from .config import settings


async def get_correlation_id(
    x_correlation_id: Optional[str] = Header(None)
) -> str:
    """
    Reads X-Correlation-ID from the request header.
    If absent, generates a new UUID so every request is always traceable.
    The middleware in main.py echoes this back in the response header.
    """
    return x_correlation_id or str(uuid.uuid4())


def get_llm_client() -> LLMClient:
    """
    Factory for the LLM client based on settings.llm_provider.
    Add new providers here as elif branches — nothing else needs to change.

    Currently supported:
      - "ollama"  →  OllamaClient (Phi-3 running locally)

    Future:
      - "azure"   →  AzureOpenAIClient
      - "openai"  →  OpenAIClient
    """
    if settings.llm_provider == "ollama":
        return OllamaClient(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
        )

    raise HTTPException(
        status_code=500,
        detail=f"Unsupported LLM provider: '{settings.llm_provider}'. "
               f"Check LLM_PROVIDER in your .env file.",
    )


def get_planning_agent(
    llm: LLMClient = Depends(get_llm_client),
) -> PlanningAgent:
    """
    Injects a PlanningAgent with its LLM dependency already resolved.
    Using Depends here means FastAPI manages the lifecycle — the agent
    is not re-instantiated manually inside each endpoint.
    """
    return PlanningAgent(llm)


def get_analysis_agent(
    llm: LLMClient = Depends(get_llm_client),
) -> AnalysisAgent:
    """
    Injects an AnalysisAgent with its LLM dependency already resolved.
    """
    return AnalysisAgent(llm)


async def validate_tool_registry(tool_registry: List[str]) -> List[str]:
    """Validates that toolRegistry is a non-empty list."""
    if not isinstance(tool_registry, list) or len(tool_registry) == 0:
        raise HTTPException(
            status_code=400,
            detail="toolRegistry must be a non-empty list of tool name strings.",
        )
    return tool_registry