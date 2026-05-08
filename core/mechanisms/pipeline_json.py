"""JSON serialization helpers for the read-only mechanism pipeline."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from core.mechanisms.pipeline import MechanismPipelineResult


def mechanism_pipeline_to_json_dict(
    pipeline: MechanismPipelineResult,
) -> dict[str, Any]:
    """Convert a MechanismPipelineResult into a JSON-serializable dict."""
    return {
        "effects": [_to_json_dict(item) for item in pipeline.effects],
        "candidates": [_to_json_dict(item) for item in pipeline.candidates],
        "arbitration_results": [
            _to_json_dict(item)
            for item in pipeline.arbitration_results
        ],
        "policy_results": [
            _to_json_dict(item)
            for item in pipeline.policy_results
        ],
        "scored_concerns": [
            _to_json_dict(item)
            for item in pipeline.scored_concerns
        ],
        "severity_annotations": [
            _to_json_dict(item)
            for item in pipeline.severity_annotations
        ],
        "aggregate_concerns": [
            _aggregate_to_json_dict(item)
            for item in pipeline.aggregate_concerns
        ],
    }


def _aggregate_to_json_dict(item) -> dict[str, Any]:
    data = _to_json_dict(item)
    data["members"] = [_to_json_dict(member) for member in item.members]
    return data


def _to_json_dict(item) -> dict[str, Any]:
    data = asdict(item)
    return _normalize_json_value(data)


def _normalize_json_value(value):
    if isinstance(value, dict):
        return {
            key: _normalize_json_value(item)
            for key, item in value.items()
        }

    if isinstance(value, tuple):
        return [_normalize_json_value(item) for item in value]

    if isinstance(value, list):
        return [_normalize_json_value(item) for item in value]

    return value
