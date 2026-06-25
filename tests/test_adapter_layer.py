import pytest

from app.adapters.layer import DataAdapterLayer
from app.adapters.schema_utils import analyze_schema_compatibility, infer_field_mapping


FETCH_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "raw_text": {"type": "string"},
        "source_url": {"type": "string"},
    },
    "required": ["raw_text"],
}

SYNTH_INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "metadata": {"type": "object"},
    },
    "required": ["text"],
}


@pytest.mark.asyncio
async def test_adapter_bridges_alias_fields():
    layer = DataAdapterLayer()
    result = await layer.bridge(
        source_data={"raw_text": "merhaba dünya", "source_url": "https://example.com"},
        source_output_schema=FETCH_OUTPUT_SCHEMA,
        target_input_schema=SYNTH_INPUT_SCHEMA,
        source_capability="data_fetcher",
        target_capability="synthesizer",
    )
    assert result.success is True
    assert result.data["text"] == "merhaba dünya"


@pytest.mark.asyncio
async def test_adapter_reports_missing_fields():
    layer = DataAdapterLayer()
    incompatible_target = {
        "type": "object",
        "properties": {
            "embedding_vector": {"type": "array"},
        },
        "required": ["embedding_vector"],
    }
    result = await layer.bridge(
        source_data={"raw_text": "veri"},
        source_output_schema=FETCH_OUTPUT_SCHEMA,
        target_input_schema=incompatible_target,
    )
    assert result.success is False
    assert result.error is not None


def test_schema_compatibility_detects_missing_required():
    compatible, mismatches = analyze_schema_compatibility(
        FETCH_OUTPUT_SCHEMA,
        SYNTH_INPUT_SCHEMA,
    )
    assert compatible is False
    assert any(m.field_path == "text" for m in mismatches)


def test_infer_field_mapping_raw_text_to_text():
    mapping = infer_field_mapping(FETCH_OUTPUT_SCHEMA, SYNTH_INPUT_SCHEMA)
    assert mapping.get("raw_text") == "text"
