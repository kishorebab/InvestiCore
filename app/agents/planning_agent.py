import json
from typing import Any, List

from ..llm.llm_client import LLMClient
from ..validators.schema_validator import SchemaValidator
from ..validators.tool_validator import ToolValidator
from ..models.plan_models import PlanningResponse, PlanningRequest


class PlanningAgent:
    MAX_RETRIES = 3

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def load_prompt(self, user_query: str, tool_registry: List[str]) -> str:
        from pathlib import Path

        base = Path(__file__).parent.parent / "prompts" / "planning_prompt.txt"
        template = base.read_text(encoding="utf-8")
        return template.format(user_query=user_query, tool_registry=tool_registry)

    def generate_plan(self, request: PlanningRequest) -> PlanningResponse:
        prompt = self.load_prompt(request.userQuery, request.toolRegistry)
        last_error: str | None = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            raw = self.llm.generate(prompt)
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as e:
                last_error = f"JSON decode error: {e}"
                prompt = (
                    "Your previous response was invalid JSON. "
                    "Fix and return ONLY valid JSON.\n" + prompt
                )
                continue
            try:
                validated = SchemaValidator.validate_planning(data)
            except Exception as e:
                last_error = f"Schema validation error: {e}"
                prompt = (
                    "Your previous response did not conform to schema. "
                    "Fix and return ONLY valid JSON.\n" + prompt
                )
                continue
            # verify tool names against registry
            try:
                ToolValidator.verify_tools_exist(
                    [step.model_dump() for step in validated.steps], request.toolRegistry
                )
            except Exception as e:
                raise ValueError(f"Tool validation failed: {e}")
            return validated
        raise RuntimeError(f"Failed to generate valid plan after retries: {last_error}")
