import pytest

from app.adapters.shapeshifter import ManifestShapeshifter
from app.network.nat import NATTraversalCoordinator
from app.network.public_discovery import PublicPeerDiscovery
from app.network.schemas import PublicAnnounceRequest
from app.network.signaling import SignalingHub
from app.protocol.schemas import AgentCapability, AgentManifest


def _fetch_cap() -> AgentCapability:
    return AgentCapability(
        name="data_fetcher",
        description="ham veri çeker",
        input_schema={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
        output_schema={
            "type": "object",
            "properties": {"raw_text": {"type": "string"}, "source_url": {"type": "string"}},
            "required": ["raw_text"],
        },
    )


def _synth_cap() -> AgentCapability:
    return AgentCapability(
        name="synthesizer",
        description="metin özeti sentezler",
        input_schema={
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        },
        output_schema={
            "type": "object",
            "properties": {"summary": {"type": "string"}},
            "required": ["summary"],
        },
    )


def test_shapeshifter_maps_raw_text_to_text():
    shifter = ManifestShapeshifter()
    mapping = shifter.infer_mapping_from_manifests(_fetch_cap(), _synth_cap())
    assert mapping.get("raw_text") == "text"


def test_shapeshifter_transform_applies_defaults():
    shifter = ManifestShapeshifter()
    data, mapping = shifter.transform(
        {"raw_text": "merhaba", "source_url": "https://x"},
        _fetch_cap(),
        _synth_cap(),
    )
    assert data["text"] == "merhaba"
    assert "raw_text" in mapping or "text" in data


def test_public_discovery_nat_endpoints():
    discovery = PublicPeerDiscovery()
    coordinator = NATTraversalCoordinator(
        discovery=discovery,
        signaling=SignalingHub(),
        public_base_url="http://gateway:8787",
    )
    manifest = AgentManifest(
        agent_id="remote.dev.agent",
        endpoint="http://192.168.1.50:9000",
        capabilities=[_fetch_cap()],
    )
    record = coordinator.register_public_peer(
        PublicAnnounceRequest(
            manifest=manifest,
            local_endpoint="http://192.168.1.50:9000",
            public_endpoint="http://203.0.113.10:9000",
            ice_candidates=["candidate:1 udp"],
            nat_type="symmetric",
        )
    )
    assert record.manifest.endpoint == "http://203.0.113.10:9000"
    assert coordinator.resolve_execution_endpoint(record.manifest, caller_is_local=True).startswith(
        "http://192.168"
    )
    assert coordinator.resolve_execution_endpoint(
        record.manifest, caller_is_local=False
    ).startswith("http://203.")
