import logging
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings
from .logging_config import configure_logging
from .dependencies import get_correlation_id, get_llm_client
from .llm.llm_client import LLMClient
from .agents.planning_agent import PlanningAgent
from .agents.analysis_agent import AnalysisAgent
from .models.plan_models import PlanningRequest
from .models.analysis_models import AnalysisRequest

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(title=settings.app_name)


class ExceptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Unhandled exception")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"},
            )


app.add_middleware(ExceptionMiddleware)


@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    cid = request.headers.get("X-Correlation-ID") or "-"
    request.state.correlation_id = cid
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = cid
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/plan")
async def plan(
    payload: PlanningRequest,
    llm: LLMClient = Depends(get_llm_client),
    correlation_id: str = Depends(get_correlation_id),
):
    logger.info("/plan request received", extra={"correlation_id": correlation_id})
    agent = PlanningAgent(llm)
    try:
        result = agent.generate_plan(payload)
        return result
    except ValueError as ve:
        logger.warning("Validation error during planning", extra={"correlation_id": correlation_id})
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:
        logger.error("Planning agent failed", extra={"correlation_id": correlation_id})
        raise HTTPException(status_code=500, detail=str(re))


@app.post("/analyze")
async def analyze(
    payload: AnalysisRequest,
    llm: LLMClient = Depends(get_llm_client),
    correlation_id: str = Depends(get_correlation_id),
):
    logger.info("/analyze request received", extra={"correlation_id": correlation_id})
    agent = AnalysisAgent(llm)
    try:
        result = agent.generate_analysis(payload)
        return result
    except ValueError as ve:
        logger.warning("Validation error during analysis", extra={"correlation_id": correlation_id})
        raise HTTPException(status_code=400, detail=str(ve))
    except RuntimeError as re:
        logger.error("Analysis agent failed", extra={"correlation_id": correlation_id})
        raise HTTPException(status_code=500, detail=str(re))
