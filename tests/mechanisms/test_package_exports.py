from core.mechanisms import (
    AggregateSeverityAnnotation,
    MechanismPipelineResult,
    mechanism_pipeline_to_json_dict,
    run_mechanism_pipeline,
)


def test_mechanisms_package_exports_public_entrypoints():
    assert MechanismPipelineResult is not None
    assert run_mechanism_pipeline is not None
    assert mechanism_pipeline_to_json_dict is not None
    assert AggregateSeverityAnnotation is not None