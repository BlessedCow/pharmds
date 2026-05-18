"""Public entrypoints for the mechanism inference package."""

from __future__ import annotations

from core.mechanisms.aggregate_evidence import AggregateEvidenceSummary
from core.mechanisms.aggregate_severity import AggregateSeverityAnnotation
from core.mechanisms.pipeline import (
    MechanismPipelineResult,
    run_mechanism_pipeline,
)
from core.mechanisms.pipeline_json import mechanism_pipeline_to_json_dict

__all__ = [
    "MechanismPipelineResult",
    "mechanism_pipeline_to_json_dict",
    "run_mechanism_pipeline",
    "AggregateSeverityAnnotation",
    "AggregateEvidenceSummary",
]