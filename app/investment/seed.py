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
        long_description=(
            "BioMed-Fetcher, PubMed ve açık erişim biyomedikal veritabanlarından "
            "7/24 ham literatür çeker. Halüsinasyon riskini düşürmek için yalnızca "
            "doğrulanmış kaynak URL'lerini döndürür; çıktısı doğrudan sentez ve "
            "analiz ajanlarına beslenebilir JSON formatındadır."
        ),
        investment_thesis=(
            "Sağlık AI pazarında veri çekme katmanı en yüksek çağrı hacmine sahip "
            "sınıftır. Bu ajan ağdaki her araştırma pipeline'ının ilk halkasıdır — "
            "kullanım arttıkça BMF-Token havuzu ve APY organik olarak büyür."
        ),
        use_cases=[
            "Klinik araştırma meta-analizi",
            "İlaç etkileşim literatür taraması",
            "Regülasyon uyum raporları",
            "Akademik RAG veri beslemesi",
        ],
        staking_covers="PubMed API kotası, vektör veritabanı depolama, proxy sunucu maliyetleri.",
        risk_level="düşük",
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
        long_description=(
            "Crypto-Analyst-V4, ham piyasa verisi ve haber akışlarını tek bir "
            "yapılandırılmış risk özeti haline getirir. Makro trendleri, anomali "
            "sinyallerini ve portföy uyarılarını dakikalar içinde üretir."
        ),
        investment_thesis=(
            "Finansal sentez ajanları görev başına en yüksek birim fiyatı taşır. "
            "DAG orkestrasyonunda kritik düğüm oldukları için ağ trafiği arttıkça "
            "gelir payı üstel biçimde yükselir."
        ),
        use_cases=[
            "Portföy risk raporu",
            "DeFi protokol due diligence",
            "Haber sentiment analizi",
            "Çoklu borsa veri birleştirme",
        ],
        staking_covers="GPT-4 sınıfı API çağrıları, gerçek zamanlı veri feed abonelikleri.",
        risk_level="orta",
        token_symbol="CAV4-TKN",
        contract_address="0xcav48f2a1b9e0d7c6b5a4938271605f4d3c2c1b0a98",
    ),
    "oam.transformer.local": AgentInvestmentProfile(
        agent_id="oam.transformer.local",
        display_name="Data-Normalizer",
        agent_class=AgentClass.TRANSFORMER,
        mission=(
            "Ham metin ve yapılandırılmamış veriyi normalize eder, "
            "şema uyumlu formata dönüştürür."
        ),
        long_description=(
            "Data-Normalizer, farklı kaynaklardan gelen heterojen veriyi OAM "
            "protokol şemalarına uyumlu hale getirir. Adaptör katmanının canlı "
            "karşılığıdır; ağdaki her veri köprüsü bu sınıfa bağımlıdır."
        ),
        investment_thesis=(
            "Dönüştürücü ajanlar sessiz ama vazgeçilmezdir — ağ büyüdükçe "
            "her yeni ajan entegrasyonu ek çağrı hacmi yaratır. Düşük maliyet, "
            "yüksek hacim modeli istikrarlı nakit akışı sağlar."
        ),
        use_cases=[
            "PDF → JSON dönüşümü",
            "Çok dilli metin normalizasyonu",
            "Şema uyumluluk doğrulama",
            "Etl pipeline ara katmanı",
        ],
        staking_covers="CPU yoğun ön işleme, depolama I/O, batch işlem sunucuları.",
        risk_level="düşük",
        token_symbol="DN-TKN",
        contract_address="0xdn3f7a2c1e9b8d7c6a5f4938271605e4d3c2b1a098",
    ),
    "example.echo.agent": AgentInvestmentProfile(
        agent_id="example.echo.agent",
        display_name="Echo-Validator",
        agent_class=AgentClass.VALIDATOR,
        mission="Canlı ağ sağlık kontrolü ve echo doğrulama görevlerini yürütür.",
        long_description=(
            "Echo-Validator, Open Agent Mesh ağının canlılık nabzını tutar. "
            "Diğer ajanların erişilebilirliğini ve proof-of-execution zincirini "
            "doğrulamak için referans düğüm olarak kullanılır."
        ),
        investment_thesis=(
            "Altyapı doğrulama ajanları düşük getiri ama düşük risk sunar — "
            "ağ genişledikçe SLA tabanlı sabit gelir modeline geçiş potansiyeli taşır."
        ),
        use_cases=["Ağ sağlık monitörü", "CI/CD entegrasyon testi", "SLA heartbeat"],
        staking_covers="Minimal compute — yüksek erişilebilirlik uptime maliyeti.",
        risk_level="düşük",
        token_symbol="ECHO-TKN",
        contract_address="0xecho1a2b3c4d5e6f7890abcdef1234567890abcd",
    ),
}
