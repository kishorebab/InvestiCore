from typing import Any

from ..models.plan_models import PlanningResponse, validate_planning_response
from ..models.analysis_models import AnalysisResponse, validate_analysis_response


class SchemaValidator:
    @staticmethod
    def validate_planning(raw: Any) -> PlanningResponse:
        return validate_planning_response(raw)

    @staticmethod
    def validate_analysis(raw: Any) -> AnalysisResponse:
        return validate_analysis_response(raw)