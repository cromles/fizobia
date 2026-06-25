from __future__ import annotations

from app.investment.schemas import AgentClass, AgentInvestmentProfile

DEFAULT_PROFILES: dict[str, AgentInvestmentProfile] = {
    "oam.fetcher.local": AgentInvestmentProfile(
        agent_id="oam.fetcher.local",
        display_name="BioMed-Fetcher",
        agent_class=AgentClass.FETCHER,
        mission=(
            "Biyomedikal alandaki ham makaleleri tarar, çelişkili klinik bulguları "
            "ayıklar ve JSON şemasına dönüştürür."
        ),
        token_symbol="BMF-TKN",
        contract_address="0xbmf4a2c8e1f9037d6b5c4a2910e8f7d6c5b4a3921",
    ),
    "oam.synthesizer.local": AgentInvestmentProfile(
        agent_id="oam.synthesizer.local",
        display_name="Crypto-Analyst-V4",
        agent_class=AgentClass.SYNTHESIZER,
        mission=(
            "Çok kaynaklı finansal veriyi sentezler, risk sinyallerini ayıklar "
            "ve yatırım kararları için yapılandırılmış özet üretir."
        ),
        token_symbol="CAV4-TKN",
        contract_address="0xcav48f2a1b9e0d7c6b5a4938271605f4e3d2c1b0a98",
    ),
    "oam.transformer.local": AgentInvestmentProfile(
        agent_id="oam.transformer.local",
        display_name="Data-Normalizer",
        agent_class=AgentClass.TRANSFORMER,
        mission=(
            "Ham metin ve yapılandırılmamış veriyi normalize eder, "
            "şema uyumlu formata dönüştürür."
        ),
        token_symbol="DN-TKN",
        contract_address="0xdn3f7a2c1e9b8d7c6a5f4938271605e4d3c2b1a098",
    ),
    "example.echo.agent": AgentInvestmentProfile(
        agent_id="example.echo.agent",
        display_name="Echo-Validator",
        agent_class=AgentClass.VALIDATOR,
        mission="Canlı ağ sağlık kontrolü ve echo doğrulama görevlerini yürütür.",
        token_symbol="ECHO-TKN",
        contract_address="0xecho1a2b3c4d5e6f7890abcdef1234567890abcd",
    ),
}
