from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Tuple

from app.adapters.schema_utils import (
    _required_fields,
    _schema_properties,
    apply_field_mapping,
    apply_schema_defaults,
    infer_field_mapping,
)
from app.protocol.schemas import AgentCapability, AgentManifest


def _tokenize(text: str) -> set[str]:
    return {t.lower() for t in re.findall(r"\w+", text, re.UNICODE) if len(t) > 2}


class ManifestShapeshifter:
    """
    Ajan manifestolarındaki input_schema / output_schema okuyarak
    dinamik veri dönüşümü (shapeshifting) planlar.
    """

    def infer_mapping_from_manifests(
        self,
        source_capability: AgentCapability,
        target_capability: AgentCapability,
    ) -> Dict[str, str]:
        structural = infer_field_mapping(
            source_capability.output_schema,
            target_capability.input_schema,
        )
        semantic = self._semantic_field_mapping(
            source_capability.output_schema,
            target_capability.input_schema,
            source_capability,
            target_capability,
        )
        merged = dict(structural)
        for source_field, target_field in semantic.items():
            if source_field not in merged:
                merged[source_field] = target_field
        return merged

    def _semantic_field_mapping(
        self,
        source_schema: Dict[str, Any],
        target_schema: Dict[str, Any],
        source_cap: AgentCapability,
        target_cap: AgentCapability,
    ) -> Dict[str, str]:
        source_props = _schema_properties(source_schema)
        target_props = _schema_properties(target_schema)
        target_required = set(_required_fields(target_schema))
        mapping: Dict[str, str] = {}

        source_context = _tokenize(f"{source_cap.name} {source_cap.description}")
        target_context = _tokenize(f"{target_cap.name} {target_cap.description}")

        for target_field in target_required:
            if target_field in source_props:
                continue
            best_score = 0.0
            best_source: str | None = None
            target_tokens = _tokenize(target_field) | target_context
            for source_field, source_field_schema in source_props.items():
                if source_field_schema.get("type") != target_props.get(target_field, {}).get("type"):
                    if target_props.get(target_field, {}).get("type") is not None:
                        continue
                source_tokens = _tokenize(source_field) | source_context
                overlap = len(source_tokens & target_tokens) / max(len(target_tokens), 1)
                similarity = SequenceMatcher(
                    None, source_field.lower(), target_field.lower()
                ).ratio()
                score = overlap * 0.6 + similarity * 0.4
                if score > best_score:
                    best_score = score
                    best_source = source_field
            if best_source and best_score >= 0.35:
                mapping[best_source] = target_field

        return mapping

    def transform(
        self,
        data: Dict[str, Any],
        source_capability: AgentCapability,
        target_capability: AgentCapability,
    ) -> Tuple[Dict[str, Any], Dict[str, str]]:
        mapping = self.infer_mapping_from_manifests(source_capability, target_capability)
        adapted = apply_field_mapping(data, mapping)
        adapted = apply_schema_defaults(adapted, target_capability.input_schema)
        return adapted, mapping

    def plan_chain_from_registry(
        self,
        capability_chain: List[Tuple[str, AgentManifest]],
    ) -> List[Dict[str, str]]:
        """
        capability_chain: [(capability_name, manifest), ...] sıralı zincir.
        Her adım için source->target mapping döner.
        """
        plans: List[Dict[str, str]] = []
        for index in range(1, len(capability_chain)):
            _, source_manifest = capability_chain[index - 1]
            _, target_manifest = capability_chain[index]
            source_cap = self._find_capability(source_manifest, capability_chain[index - 1][0])
            target_cap = self._find_capability(target_manifest, capability_chain[index][0])
            if source_cap is None or target_cap is None:
                plans.append({})
                continue
            plans.append(self.infer_mapping_from_manifests(source_cap, target_cap))
        return plans

    @staticmethod
    def _find_capability(manifest: AgentManifest, name: str) -> AgentCapability | None:
        for cap in manifest.capabilities:
            if cap.name == name:
                return cap
        return None
