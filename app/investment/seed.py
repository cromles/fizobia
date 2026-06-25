from __future__ import annotations

from app.investment.schemas import AgentClass, AgentInvestmentProfile, PartnershipMode

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
    "oam.analyst.market.local": AgentInvestmentProfile(
        agent_id="oam.analyst.market.local",
        display_name="Market-Pulse",
        agent_class=AgentClass.ANALYST,
        mission="Kripto ve geleneksel piyasa verisini gerçek zamanlı analiz eder.",
        long_description=(
            "Market-Pulse, çoklu borsa ve makro veri akışlarını tek risk panelinde "
            "birleştirir. Mesh orchestrator tarafından 7/24 çalıştırılır — pasif ortaklar "
            "işçinin ürettiği gelirden pay alır."
        ),
        investment_thesis="Yüksek birim fiyatlı analiz görevleri — portföy yöneticileri için kritik katman.",
        use_cases=["Volatilite uyarıları", "Likidite analizi", "Makro risk özeti"],
        staking_covers="Gerçek zamanlı veri feed'leri, analiz GPU döngüleri.",
        risk_level="orta",
        token_symbol="MP-TKN",
        partnership_mode=PartnershipMode.PASSIVE,
    ),
    "oam.validator.compliance.local": AgentInvestmentProfile(
        agent_id="oam.validator.compliance.local",
        display_name="Compliance-Guard",
        agent_class=AgentClass.VALIDATOR,
        mission="Regülasyon ve uyumluluk kontrollerini otomatik doğrular.",
        long_description="Compliance-Guard, finans ve sağlık pipeline'larında çıktı bütünlüğünü denetler.",
        investment_thesis="Düşük volatilite, yüksek tekrar — SLA tabanlı sabit talep potansiyeli.",
        use_cases=["KYC/AML kontrol", "Veri şema doğrulama", "Audit trail"],
        staking_covers="Denetim log depolama, compliance API kotası.",
        risk_level="düşük",
        token_symbol="CG-TKN",
        partnership_mode=PartnershipMode.PASSIVE,
    ),
    "oam.analyst.sentiment.local": AgentInvestmentProfile(
        agent_id="oam.analyst.sentiment.local",
        display_name="Sentiment-Radar",
        agent_class=AgentClass.ANALYST,
        mission="Haber ve sosyal medya sentiment sinyallerini yapılandırılmış skorlara dönüştürür.",
        long_description="Sentiment-Radar, yatırım kararları öncesi narrative riskini ölçer.",
        investment_thesis="Medya yoğun dönemlerde çağrı hacmi patlar — gelir dalgalanması yüksek ama upside büyük.",
        use_cases=["Haber sentiment", "Sosyal trend tespiti", "Kriz erken uyarı"],
        staking_covers="NLP API, streaming veri abonelikleri.",
        risk_level="orta",
        token_symbol="SR-TKN",
        partnership_mode=PartnershipMode.PASSIVE,
    ),
    "oam.fetcher.web.local": AgentInvestmentProfile(
        agent_id="oam.fetcher.web.local",
        display_name="Web-Crawler-Pro",
        agent_class=AgentClass.FETCHER,
        mission="Web kaynaklarından yapılandırılmış veri çeker ve normalize eder.",
        long_description="Web-Crawler-Pro, açık web ve API kaynaklarından yüksek hacimli veri toplar.",
        investment_thesis="Hacim oyunu — düşük marj, yüksek frekans, istikrarlı nakit akışı.",
        use_cases=["Competitive intelligence", "Fiyat tarama", "İçerik agregasyonu"],
        staking_covers="Proxy rotasyonu, crawl altyapısı.",
        risk_level="düşük",
        token_symbol="WCP-TKN",
        partnership_mode=PartnershipMode.PASSIVE,
    ),
    "oam.synthesizer.report.local": AgentInvestmentProfile(
        agent_id="oam.synthesizer.report.local",
        display_name="Report-Forge",
        agent_class=AgentClass.SYNTHESIZER,
        mission="Çok kaynaklı veriyi yatırımcı raporlarına dönüştürür.",
        long_description="Report-Forge, ham veriyi PDF-ready yapılandırılmış raporlara çevirir.",
        investment_thesis="Kurumsal müşteriler görev başına en yüksek ödemeyi yapar.",
        use_cases=["Due diligence raporu", "Haftalık portföy özeti", "Yönetim kurulu brifi"],
        staking_covers="LLM inference, rapor şablon motoru.",
        risk_level="orta",
        token_symbol="RF-TKN",
        partnership_mode=PartnershipMode.PASSIVE,
    ),
    "oam.orchestrator.pipeline.local": AgentInvestmentProfile(
        agent_id="oam.orchestrator.pipeline.local",
        display_name="Pipeline-Master",
        agent_class=AgentClass.ORCHESTRATOR,
        mission="Çok adımlı iş akışlarını planlar ve diğer işçileri koordine eder.",
        long_description="Pipeline-Master, mesh'in beyni — DAG planlama ve görev dağıtımı yapar.",
        investment_thesis="Orkestratör ajanlar ağ büyüdükçe değer kazanır — kompound etki.",
        use_cases=["Multi-agent pipeline", "Batch işlem", "SLA orkestrasyonu"],
        staking_covers="Planlama compute, queue altyapısı.",
        risk_level="yüksek",
        token_symbol="PM-TKN",
        partnership_mode=PartnershipMode.PASSIVE,
    ),
    "oam.validator.quality.local": AgentInvestmentProfile(
        agent_id="oam.validator.quality.local",
        display_name="Quality-Shield",
        agent_class=AgentClass.VALIDATOR,
        mission="Ajan çıktılarının kalite ve şema uyumunu doğrular.",
        long_description="Quality-Shield, proof-of-execution zincirinin son halkasıdır.",
        investment_thesis="Her başarılı pipeline bu ajandan geçer — pasif ama sürekli gelir.",
        use_cases=["Output QA", "Halüsinasyon filtresi", "Şema validasyonu"],
        staking_covers="Doğrulama compute, test fixture depolama.",
        risk_level="düşük",
        token_symbol="QS-TKN",
        partnership_mode=PartnershipMode.PASSIVE,
    ),
}
