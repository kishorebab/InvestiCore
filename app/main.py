import logging
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings
from .logging_config import configure_logging
from .dependencies import (
    get_correlation_id,
    get_planning_agent,
    get_analysis_agent,
)
from .agents.planning_agent import PlanningAgent
from .agents.analysis_agent import AnalysisAgent
from .models.plan_models import PlanningRequest
from .models.analysis_models import AnalysisRequest

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)


# ---------------------------------------------------------------------------
# Middleware 1: Unhandled exception safety net
# Catches anything that escapes the endpoint try/except blocks.
# ---------------------------------------------------------------------------
class ExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except HTTPException:
            raise
        except Exception:
            logger.exception("Unhandled exception")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"},
            )


app.add_middleware(ExceptionMiddleware)


# ---------------------------------------------------------------------------
# Middleware 2: Correlation ID propagation
#
# Reads X-Correlation-ID from the incoming request header.
# Generates a new UUID if the header is absent — every request is traceable.
# Stores it on request.state so endpoints can access it without re-reading
# the header, and echoes it back in the response header so the .NET
# orchestrator can correlate its own logs with ours.
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    import uuid
    cid = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request.state.correlation_id = cid          # available via request.state
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = cid  # echo back to caller
    return response


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@app.get("/health")
def health():
    return {
        "status": "ok",
        "provider": settings.llm_provider,
        "model": settings.ollama_model,
    }


# ---------------------------------------------------------------------------
# /plan
#
# The PlanningAgent and correlation_id are both injected via Depends.
# The agent is NOT instantiated here — dependencies.py owns that.
# correlation_id is passed into the agent so its internal logs carry the
# same ID, making the full request traceable across both services.
# ---------------------------------------------------------------------------
@app.post("/plan")
async def plan(
    payload: PlanningRequest,
    agent: PlanningAgent = Depends(get_planning_agent),
    correlation_id: str = Depends(get_correlation_id),
):
    logger.info(
        "/plan request received",
        extra={"correlation_id": correlation_id, "query": payload.userQuery[:80]},
    )

    try:
        result = await agent.generate_plan(payload, correlation_id=correlation_id)
        logger.info(
            "/plan completed",
            extra={"correlation_id": correlation_id, "steps": len(result.steps)},
        )
        return result

    except ValueError as ve:
        logger.warning(
            "Validation error during planning",
            extra={"correlation_id": correlation_id, "error": str(ve)},
        )
        raise HTTPException(status_code=400, detail=str(ve))

    except RuntimeError as re:
        logger.error(
            "Planning agent failed",
            extra={"correlation_id": correlation_id, "error": str(re)},
        )
        raise HTTPException(status_code=500, detail=str(re))


# ---------------------------------------------------------------------------
# /analyze
#
# Same pattern as /plan — agent injected, correlation_id threaded through.
# ---------------------------------------------------------------------------
@app.post("/analyze")
async def analyze(
    payload: AnalysisRequest,
    agent: AnalysisAgent = Depends(get_analysis_agent),
    correlation_id: str = Depends(get_correlation_id),
):
    logger.info(
        "/analyze request received",
        extra={"correlation_id": correlation_id, "query": payload.userQuery[:80]},
    )

    try:
        result = await agent.generate_analysis(payload, correlation_id=correlation_id)
        logger.info(
            "/analyze completed",
            extra={"correlation_id": correlation_id},
        )
        return result

    except ValueError as ve:
        logger.warning(
            "Validation error during analysis",
            extra={"correlation_id": correlation_id, "error": str(ve)},
        )
        raise HTTPException(status_code=400, detail=str(ve))

    except RuntimeError as re:
        logger.error(
            "Analysis agent failed",
            extra={"correlation_id": correlation_id, "error": str(re)},
        )
        raise HTTPException(status_code=500, detail=str(re))