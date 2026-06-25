from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from app.protocol.schemas import MismatchKind, SchemaMismatch

_JSON_SCHEMA_TYPE_MAP = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "object": dict,
    "array": list,
}


def _schema_properties(schema: Dict[str, Any]) -> Dict[str, Any]:
    if schema.get("type") == "object":
        return schema.get("properties", {})
    return {}


def _required_fields(schema: Dict[str, Any]) -> List[str]:
    return list(schema.get("required", []))


def _field_type(schema: Dict[str, Any], field: str) -> Optional[str]:
    props = _schema_properties(schema)
    field_schema = props.get(field, {})
    return field_schema.get("type")


def _is_type_compatible(source_type: Optional[str], target_type: Optional[str]) -> bool:
    if source_type is None or target_type is None:
        return True
    if source_type == target_type:
        return True
    if source_type == "integer" and target_type == "number":
        return True
    return False


def extract_field_names(schema: Dict[str, Any]) -> Set[str]:
    return set(_schema_properties(schema).keys())


def analyze_schema_compatibility(
    source_schema: Dict[str, Any],
    target_schema: Dict[str, Any],
) -> Tuple[bool, List[SchemaMismatch]]:
    """Kaynak çıktı şemasının hedef girdi şemasını karşılayıp karşılamadığını analiz eder."""
    mismatches: List[SchemaMismatch] = []
    source_fields = extract_field_names(source_schema)
    target_required = _required_fields(target_schema)
    target_props = _schema_properties(target_schema)

    for field in target_required:
        if field not in source_fields:
            mismatches.append(
                SchemaMismatch(
                    field_path=field,
                    kind=MismatchKind.MISSING_REQUIRED_FIELD,
                    expected=_field_type(target_schema, field),
                    received=None,
                    message=f"Hedef şema zorunlu alan bekliyor: '{field}'",
                )
            )
            continue

        source_type = _field_type(source_schema, field)
        target_type = _field_type(target_schema, field)
        if not _is_type_compatible(source_type, target_type):
            mismatches.append(
                SchemaMismatch(
                    field_path=field,
                    kind=MismatchKind.TYPE_INCOMPATIBLE,
                    expected=target_type,
                    received=source_type,
                    message=(
                        f"Alan '{field}' tip uyumsuzluğu: "
                        f"kaynak={source_type}, hedef={target_type}"
                    ),
                )
            )

    for field, field_schema in target_props.items():
        if field in source_fields:
            continue
        if field in target_required:
            continue
        if field_schema.get("default") is not None:
            continue

    compatible = not any(
        m.kind in (MismatchKind.MISSING_REQUIRED_FIELD, MismatchKind.TYPE_INCOMPATIBLE)
        for m in mismatches
    )
    return compatible, mismatches


def infer_field_mapping(
    source_schema: Dict[str, Any],
    target_schema: Dict[str, Any],
) -> Dict[str, str]:
    """
    Aynı isimli alanları eşleştirir; semantik alias tablosu ile genişletilebilir.
    Dönüş: {kaynak_alan: hedef_alan}
    """
    source_fields = extract_field_names(source_schema)
    target_fields = extract_field_names(target_schema)
    mapping: Dict[str, str] = {}

    for field in source_fields & target_fields:
        mapping[field] = field

    alias_table = {
        "text": "content",
        "content": "text",
        "payload": "data",
        "data": "payload",
        "result": "output",
        "output": "result",
        "raw_text": "text",
        "extracted_text": "text",
    }

    for source_field in source_fields - target_fields:
        alias = alias_table.get(source_field)
        if alias and alias in target_fields:
            mapping[source_field] = alias

    return mapping


def apply_field_mapping(data: Dict[str, Any], mapping: Dict[str, str]) -> Dict[str, Any]:
    adapted: Dict[str, Any] = {}
    for source_key, target_key in mapping.items():
        if source_key in data:
            adapted[target_key] = data[source_key]

    target_keys = set(mapping.values())
    for key, value in data.items():
        if key not in mapping and key not in target_keys:
            adapted[key] = value

    return adapted


def apply_schema_defaults(data: Dict[str, Any], target_schema: Dict[str, Any]) -> Dict[str, Any]:
    result = data.copy()
    for field, field_schema in _schema_properties(target_schema).items():
        if field not in result and "default" in field_schema:
            result[field] = field_schema["default"]
    return result


def data_satisfies_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Verilen verinin şemanın zorunlu alanlarını karşılayıp karşılamadığını kontrol eder."""
    if not schema:
        return True
    required = _required_fields(schema)
    return all(field in data for field in required)


def can_bridge_schemas(
    source_schema: Dict[str, Any],
    target_schema: Dict[str, Any],
) -> bool:
    compatible, _ = analyze_schema_compatibility(source_schema, target_schema)
    if compatible:
        return True
    return bool(infer_field_mapping(source_schema, target_schema))
