from typing import Any
from pydantic import ValidationError

from ..models.plan_models import PlanningResponse
from ..models.analysis_models import AnalysisResponse


class SchemaValidator:

    @staticmethod
    def validate_planning(raw: Any) -> PlanningResponse:
        try:
            return PlanningResponse(**raw)
        except ValidationError as e:
            raise ValueError(f"Invalid planning response schema: {e}")

    @staticmethod
    def validate_analysis(raw: Any) -> AnalysisResponse:
        try:
            return AnalysisResponse(**raw)
        except ValidationError as e:
            raise ValueError(f"Invalid analysis response schema: {e}")