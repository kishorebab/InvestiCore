import json
import uuid
import logging
from pathlib import Path
from app.llm.llm_client import LLMClient
from app.models.plan_models import PlanningRequest, PlanningResponse, PlanStep

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "planning_prompt.txt"
MAX_RETRIES = 3

class PlanningAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.system_prompt_template = PROMPT_PATH.read_text()

    async def plan(self, request: PlanningRequest) -> PlanningResponse:
        tool_list = "\n".join(f"- {t}" for t in request.toolRegistry)
        system_prompt = self.system_prompt_template.format(tool_list=tool_list)
        user_prompt = f"Investigation Query: {request.userQuery}"

        last_error = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                logger.info(f"Planning attempt {attempt}/3")
                llm_resp = await self.llm.complete(system_prompt, user_prompt)
                plan = self._parse(llm_resp.content, request.toolRegistry)
                logger.info(f"Plan OK: {len(plan.steps)} steps, confidence={plan.confidence}")
                return plan

            except (json.JSONDecodeError, ValueError, KeyError) as e:
                last_error = e
                logger.warning(f"Attempt {attempt} failed: {e}")

                if attempt < MAX_RETRIES:
                    # Feed the error back to LLM so it can self-correct
                    user_prompt = (
                        f"Your previous response had an error: {e}\n"
                        f"Fix it and return valid JSON.\n"
                        f"Original query: {request.userQuery}"
                    )

        raise RuntimeError(
            f"Could not generate valid plan after {MAX_RETRIES} attempts. "
            f"Last error: {last_error}"
        )

    def _parse(self, raw: str, tool_registry: list[str]) -> PlanningResponse:
        # Strip markdown fences — small LLMs often add them even when told not to
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            parts = cleaned.split("```")
            cleaned = parts[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()

        data = json.loads(cleaned)

        # Ensure planId exists
        if not data.get("planId"):
            data["planId"] = str(uuid.uuid4())

        plan = PlanningResponse(**data)

        # Validate every tool name is in the registry
        for step in plan.steps:
            if step.toolName not in tool_registry:
                raise ValueError(
                    f"Tool '{step.toolName}' is not in the registry. "
                    f"Valid tools: {tool_registry}"
                )

        return plan