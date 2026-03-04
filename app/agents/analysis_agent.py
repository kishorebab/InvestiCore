import json
from typing import Any

from ..llm.llm_client import LLMClient
from ..validators.schema_validator import SchemaValidator
from ..models.analysis_models import AnalysisRequest, AnalysisResponse


class AnalysisAgent:
    MAX_RETRIES = 3

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def load_prompt(self, user_query: str, tool_results: Any) -> str:
        from pathlib import Path

        base = Path(__file__).parent.parent / "prompts" / "analysis_prompt.txt"
        template = base.read_text(encoding="utf-8")
        return template.format(user_query=user_query, tool_results=tool_results)

    def generate_analysis(self, request: AnalysisRequest) -> AnalysisResponse:
        prompt = self.load_prompt(request.userQuery, request.toolResults)
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
                validated = SchemaValidator.validate_analysis(data)
            except Exception as e:
                last_error = f"Schema validation error: {e}"
                prompt = (
                    "Your previous response did not conform to schema. "
                    "Fix and return ONLY valid JSON.\n" + prompt
                )
                continue
            return validated
        raise RuntimeError(f"Failed to generate valid analysis after retries: {last_error}")
