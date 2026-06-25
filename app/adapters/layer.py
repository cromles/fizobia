from __future__ import annotations

import logging
from app.protocol.schemas import AgentCapability

from app.adapters.shapeshifter import ManifestShapeshifter
from app.adapters.schema_utils import (
    analyze_schema_compatibility,
    apply_field_mapping,
    apply_schema_defaults,
    infer_field_mapping,
)
from app.protocol.schemas import AdaptationResult, MismatchKind, SchemaMismatch

logger = logging.getLogger(__name__)


class DataAdapterLayer:
    """
    İki uyumsuz ajan arasına giren dinamik veri adaptör katmanı.

    OAM protokolü gereği:
    - Manifest şemalarına dayanır (kod seviyesi değil, JSON Schema seviyesi)
    - Deterministik dönüşüm önceliklidir (LLM tahmini değil, alan eşlemesi)
    - Hata durumunda fault-tolerant yapılandırılmış sonuç döner
    """

    def __init__(self, custom_mappings: Optional[Dict[str, Dict[str, str]]] = None):
        self._custom_mappings = custom_mappings or {}
        self._shapeshifter = ManifestShapeshifter()

    def register_mapping(
        self,
        source_capability: str,
        target_capability: str,
        mapping: Dict[str, str],
    ) -> None:
        key = self._pair_key(source_capability, target_capability)
        self._custom_mappings[key] = mapping

    @staticmethod
    def _pair_key(source_capability: str, target_capability: str) -> str:
        return f"{source_capability}->{target_capability}"

    async def bridge(
        self,
        source_data: Dict[str, Any],
        source_output_schema: Dict[str, Any],
        target_input_schema: Dict[str, Any],
        source_capability: str = "",
        target_capability: str = "",
        source_cap: Optional[AgentCapability] = None,
        target_cap: Optional[AgentCapability] = None,
    ) -> AdaptationResult:
        compatible, mismatches = analyze_schema_compatibility(
            source_output_schema,
            target_input_schema,
        )

        if compatible:
            normalized = apply_schema_defaults(source_data, target_input_schema)
            return AdaptationResult(
                success=True,
                data=normalized,
                applied_mappings={k: k for k in source_data.keys()},
                mismatches=mismatches,
            )

        pair_key = self._pair_key(source_capability, target_capability)
        mapping = self._custom_mappings.get(pair_key)
        if not mapping and source_cap is not None and target_cap is not None:
            mapping = self._shapeshifter.infer_mapping_from_manifests(
                source_cap, target_cap
            )
        if not mapping:
            mapping = infer_field_mapping(source_output_schema, target_input_schema)

        if not mapping:
            return AdaptationResult(
                success=False,
                data=source_data,
                mismatches=mismatches,
                error="Alan eşlemesi çıkarılamadı; adaptör köprüsü kurulamadı.",
            )

        adapted = apply_field_mapping(source_data, mapping)
        adapted = apply_schema_defaults(adapted, target_input_schema)

        remaining = self._remaining_required_gaps(adapted, target_input_schema)
        if remaining:
            return AdaptationResult(
                success=False,
                data=adapted,
                applied_mappings=mapping,
                mismatches=mismatches + remaining,
                error="Dönüşüm sonrası zorunlu alanlar hâlâ eksik.",
            )

        logger.info(
            "Adaptör köprüsü kuruldu: %s -> %s (mapping=%s)",
            source_capability,
            target_capability,
            mapping,
        )
        return AdaptationResult(
            success=True,
            data=adapted,
            applied_mappings=mapping,
            mismatches=mismatches,
        )

    async def bridge_chain(
        self,
        segments: List[Dict[str, Any]],
    ) -> AdaptationResult:
        """
        Birden fazla ara dönüşümü zincirler.
        Her segment: {data, source_output_schema, target_input_schema, source_capability, target_capability}
        """
        current_data: Dict[str, Any] = {}
        all_mappings: Dict[str, str] = {}
        all_mismatches: List[SchemaMismatch] = []

        for index, segment in enumerate(segments):
            if index == 0:
                current_data = segment["data"]
            result = await self.bridge(
                source_data=current_data,
                source_output_schema=segment["source_output_schema"],
                target_input_schema=segment["target_input_schema"],
                source_capability=segment.get("source_capability", ""),
                target_capability=segment.get("target_capability", ""),
            )
            all_mappings.update(result.applied_mappings)
            all_mismatches.extend(result.mismatches)

            if not result.success:
                return AdaptationResult(
                    success=False,
                    data=result.data,
                    applied_mappings=all_mappings,
                    mismatches=all_mismatches,
                    error=f"Zincir adaptasyonu adım {index} başarısız: {result.error}",
                )
            current_data = result.data

        return AdaptationResult(
            success=True,
            data=current_data,
            applied_mappings=all_mappings,
            mismatches=all_mismatches,
        )

    @staticmethod
    def _remaining_required_gaps(
        data: Dict[str, Any],
        target_schema: Dict[str, Any],
    ) -> List[SchemaMismatch]:
        required = target_schema.get("required", [])
        gaps: List[SchemaMismatch] = []
        for field in required:
            if field not in data:
                gaps.append(
                    SchemaMismatch(
                        field_path=field,
                        kind=MismatchKind.MISSING_REQUIRED_FIELD,
                        message=f"Dönüşüm sonrası zorunlu alan eksik: '{field}'",
                    )
                )
        return gaps
