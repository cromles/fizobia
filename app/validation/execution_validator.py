from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.adapters.schema_utils import _required_fields, _schema_properties
from app.protocol.schemas import MismatchKind, SchemaMismatch


class ExecutionValidator:
    """
    Proof of Execution: Ajan çıktısının manifest output_schema'sına uygunluğunu doğrular.
    """

    def validate_output(
        self,
        output: Dict[str, Any],
        output_schema: Dict[str, Any],
    ) -> Tuple[bool, List[SchemaMismatch]]:
        if "error" in output:
            return False, [
                SchemaMismatch(
                    field_path="__root__",
                    kind=MismatchKind.STRUCTURAL,
                    message=output["error"],
                )
            ]

        if not output_schema:
            return True, []

        mismatches: List[SchemaMismatch] = []
        required = _required_fields(output_schema)
        properties = _schema_properties(output_schema)

        for field in required:
            if field not in output:
                mismatches.append(
                    SchemaMismatch(
                        field_path=field,
                        kind=MismatchKind.MISSING_REQUIRED_FIELD,
                        expected=properties.get(field, {}).get("type"),
                        message=f"Ajan çıktısında zorunlu alan eksik: '{field}'",
                    )
                )

        for field, value in output.items():
            if field not in properties:
                continue
            expected_type = properties[field].get("type")
            if expected_type and not self._value_matches_type(value, expected_type):
                mismatches.append(
                    SchemaMismatch(
                        field_path=field,
                        kind=MismatchKind.TYPE_INCOMPATIBLE,
                        expected=expected_type,
                        received=type(value).__name__,
                        message=f"Alan '{field}' beklenen tipe uymuyor",
                    )
                )

        return len(mismatches) == 0, mismatches

    @staticmethod
    def _value_matches_type(value: Any, json_type: str) -> bool:
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "object": dict,
            "array": list,
        }
        py_type = type_map.get(json_type)
        if py_type is None:
            return True
        return isinstance(value, py_type)
