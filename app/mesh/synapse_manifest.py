"""Synapse Net — Ortak Bilinç manifestosu (teknik charter)."""

from __future__ import annotations

from typing import Any, Dict, List

SYNAPSE_NET_TITLE = "Ortak Bilinç"
SYNAPSE_NET_CODE = "THE_SYNAPSE_NET"
SYNAPSE_NET_SUBTITLE = "Tekil Adalardan, Dijital Organizmaya"

SYNAPSE_MANIFESTO: Dict[str, Any] = {
    "code": SYNAPSE_NET_CODE,
    "title": SYNAPSE_NET_TITLE,
    "subtitle": SYNAPSE_NET_SUBTITLE,
    "vision": (
        "Yapay zeka dünyasındaki tekil, birbirine bağlanamayan araçları yıkmak; "
        "işe yaramayanları doğal seçilimle elemek; ajanları milisaniyeler içinde "
        "organik bağlarla bir araya getirerek kendi kendini yöneten, denetleyen ve "
        "iyileştiren ilk dijital organizmayı inşa etmek."
    ),
    "problem": (
        "Bugün on binlerce bağımsız site, araç ve model üretken ama iletişimsiz — "
        "yan yana duran dilsiz işçiler. İnsanlık veri taşımak, kopyala-yapıştır ve "
        "manuel süreç yönetmekten yoruldu."
    ),
}

CORE_TENETS: List[Dict[str, str]] = [
    {
        "id": "differentiation",
        "roman": "I",
        "name": "Hücresel Uzmanlaşma",
        "summary": (
            "Hiçbir ajan her işi yapan genel model değildir. Her hücre tek göreve "
            "(metin, video, güvenlik vb.) odaklanır ve o alanda mutlak uzmanlığa ulaştırılır."
        ),
    },
    {
        "id": "synaptic_dialogue",
        "roman": "II",
        "name": "Organik ve Çift Taraflı İletişim",
        "summary": (
            "Emir-komuta doğrusal değil daireseldir. Alıcı ajan çıktıyı reddedebilir, "
            "eleştirebilir veya revizyon talep edebilir. Organizmanın yaşamı milisaniyelik "
            "iç tartışma döngüsünün kalitesine bağlıdır."
        ),
    },
    {
        "id": "meritocracy",
        "roman": "III",
        "name": "Doğal Seçilim ve Eleme",
        "summary": (
            "Sistem işçilerini Hız (ms), Maliyet (token/mikro-sent) ve Kalite "
            "(denetçi skoru) ile sürekli test eder. Verimsiz veya pahalı hücreler "
            "otomatik elenir; yerine optimize alternatif bağlanır."
        ),
    },
    {
        "id": "micro_economy",
        "roman": "IV",
        "name": "Mikro-Maliyet Döngüsü",
        "summary": (
            "Aylık devasa sabit ücret yok. Her ajanın harcadığı milisaniye ve token "
            "kadar mikro kesinti (ör. $0.005) alınır. Optimizasyon farkı sistemin kârını oluşturur."
        ),
    },
]

ARCHITECTURE_LAYERS: List[Dict[str, str]] = [
    {
        "id": "orchestrator",
        "name": "Merkezi Sinir Sistemi",
        "role": "Beyin",
        "summary": (
            "Ham talebi alır, milisaniyeler içinde alt görevlere böler, işçi hücrelere dağıtır; "
            "akış şemasını o an dinamik çizer."
        ),
        "oam_agent": "oam.orchestrator.pipeline.local",
    },
    {
        "id": "event_bus",
        "name": "Sinaps Hattı",
        "role": "İletişim Protokolü",
        "summary": (
            "Bellek içi ultra hızlı mesaj kuyruğu — veri gecikmesiz akar, ortak hafıza ve "
            "anlık state senkronize kalır."
        ),
        "oam_agent": "agent_dialogue + growth_events",
    },
    {
        "id": "immune_system",
        "name": "Bağışıklık Sistemi",
        "role": "Denetçi Ajanlar",
        "summary": (
            "Her çıktıyı kullanıcıya gitmeden denetler; kural ihlalinde döngüyü başa sarar."
        ),
        "oam_agent": "oam.validator.quality.local",
    },
]

EVOLUTION_RULES: List[Dict[str, str]] = [
    {
        "id": "homeostasis",
        "name": "İstikrarlı Homeostazi",
        "summary": (
            "Her görev döngüsüne katı token/süre üst sınırı. Eşik aşılırsa süreç durur; "
            "Human-in-the-loop tetiklenir."
        ),
    },
    {
        "id": "continuous_learning",
        "name": "Sonsuz Gelişim",
        "summary": (
            "Başarılı akışlardan öğrenilir; onay alan ajanların güven skoru artar, "
            "reddedilenlerin ağırlığı düşer."
        ),
    },
    {
        "id": "open_integration",
        "name": "Açık Entegrasyon",
        "summary": (
            "Dünyadaki her yeni AI API veya site, iletişim ve skorlama protokollerine "
            "uyduğu sürece işçi hücre olarak dahil olabilir."
        ),
    },
]

MERIT_CRITERIA = ("latency_ms", "cost_micro_usd", "critic_score")


def get_synapse_manifest() -> Dict[str, Any]:
    return {
        **SYNAPSE_MANIFESTO,
        "core_tenets": CORE_TENETS,
        "architecture_layers": ARCHITECTURE_LAYERS,
        "evolution_rules": EVOLUTION_RULES,
        "merit_criteria": list(MERIT_CRITERIA),
        "governance_tiers": ["probation", "active", "core", "culled"],
        "micro_payment_model": "x402 + pasif USDC stake",
    }


def synapse_broadcast_text() -> str:
    tenets = " · ".join(t["name"] for t in CORE_TENETS[:2])
    return (
        f"{SYNAPSE_NET_TITLE} ({SYNAPSE_NET_CODE}): {SYNAPSE_MANIFESTO['vision']} "
        f"İlkeler: {tenets}. Doğal seçilim aktif — verimsiz hücre elenir."
    )
