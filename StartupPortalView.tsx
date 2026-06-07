import React, { useState, useEffect } from "react";
import {
  Coins,
  Plus,
  Flame,
  CheckCircle2,
  Lock,
  Unlock,
  AlertCircle,
  TrendingUp,
  Sliders,
  RotateCcw,
  Users,
  Award,
  Wallet,
  Activity,
  ArrowUpRight,
  PlusCircle,
  User,
  ShieldAlert,
  ChevronUp,
  Wand2,
  Cpu,
  Layers,
  Settings,
  Trash2,
  PlayCircle,
  Image as ImageIcon,
  Video,
  FileCode,
  CheckSquare,
  HelpCircle,
  Sparkles,
  ArrowRight,
  Rocket
} from "lucide-react";

interface ProofOfWorkLog {
  id: string;
  date: string;
  type: "prototype" | "simulation" | "media" | "test";
  title: string;
  description: string;
  proofUrl?: string;
  votesCount: number;
  approvedBy: string[];
}

interface MockProject {
  id: string;
  title: string;
  category: string;
  problemSolved: string;
  strategyDescription: string;
  creatorName: string;
  creatorIdentity: string;
  fundingTarget: number;
  fundingRaised: number;
  equityOffer: number;
  isBoosted: boolean;
  backersList: { investorName: string; investedAmount: number; equityShare: number }[];
  publishDate: string;
  
  // Custom loop parameters
  isDraft: boolean;
  stage: "Idea" | "TheoryVerified" | "SimulationVerified" | "PrototypeVerified" | "GlobalMarket";
  league: "Incubation" | "Prototype" | "Enterprise";
  valuationMultiplier: number;
  proofOfWorkLogs: ProofOfWorkLog[];

  // FZB EXPERT VERIFICATION AND PHYSICAL METRIC CONTROLS
  materialsRequired?: string;
  isFzbApproved?: boolean;
  fzbApprovalsCount?: number;
  isRetracted?: boolean;
  retractionReason?: string;
  vaporwareFlags: number;
  dynamismScore: number;
}

interface UserProfile {
  id: string;
  fullName: string;
  identityNo: string;
  role: "developer" | "investor" | "both";
  fzbBalance: number;
  isVerified: boolean;
}

interface StartupPortalViewProps {
  addLog: (msg: string) => void;
  userEmail: string;
}

export default function StartupPortalView({ addLog, userEmail }: StartupPortalViewProps) {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [startups, setStartups] = useState<MockProject[]>([]);
  const [drafts, setDrafts] = useState<MockProject[]>([]);
  
  // Pricing configuration from backend API
  const [publishFeeNormal, setPublishFeeNormal] = useState<number>(80);
  const [publishFeeVerified, setPublishFeeVerified] = useState<number>(30);
  const [boostFee, setBoostFee] = useState<number>(50);

  // States
  const [isProfileLoading, setIsProfileLoading] = useState<boolean>(true);
  const [isSubmittingRegister, setIsSubmittingRegister] = useState<boolean>(false);
  const [errorText, setErrorText] = useState<string | null>(null);
  const [successText, setSuccessText] = useState<string | null>(null);

  // Register Fields
  const [regName, setRegName] = useState<string>("");
  const [regId, setRegId] = useState<string>("");
  const [regRole, setRegRole] = useState<"developer" | "investor" | "both">("both");

  // Filter & Search
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedFilter, setSelectedFilter] = useState<string>("all");

  // Simulating coin shop
  const [showTokenShop, setShowTokenShop] = useState<boolean>(false);
  const [shopCardName, setShopCardName] = useState<string>("");
  const [shopCardNo, setShopCardNo] = useState<string>("");
  const [shopAmount, setShopAmount] = useState<number>(1000);
  const [isBuyingTokens, setIsBuyingTokens] = useState<boolean>(false);

  // Draft Edit Workspace Space State
  const [selectedDraftId, setSelectedDraftId] = useState<string | null>(null);
  const [draftTitle, setDraftTitle] = useState<string>("");
  const [draftCategory, setDraftCategory] = useState<string>("");
  const [draftProblem, setDraftProblem] = useState<string>("");
  const [draftStrategy, setDraftStrategy] = useState<string>("");
  const [draftFundingTarget, setDraftFundingTarget] = useState<string>("2000");
  const [draftEquity, setDraftEquity] = useState<string>("10");
  const [draftStage, setDraftStage] = useState<"Idea" | "TheoryVerified" | "SimulationVerified">("Idea");
  const [draftMaterialsRequired, setDraftMaterialsRequired] = useState<string>("Genel Sensörler, ESP32, Servo Motor");
  
  const [isSavingDraft, setIsSavingDraft] = useState<boolean>(false);
  const [isDeletingDraft, setIsDeletingDraft] = useState<boolean>(false);
  const [isOptimizingWithAI, setIsOptimizingWithAI] = useState<boolean>(false);

  // Draft Live Publishing step fields
  const [activePublishProjId, setActivePublishProjId] = useState<string | null>(null);
  const [pubProofTitle, setPubProofTitle] = useState<string>("");
  const [pubProofType, setPubProofType] = useState<"simulation" | "prototype" | "media" | "test">("simulation");
  const [pubProofDesc, setPubProofDesc] = useState<string>("");
  const [pubProofUrl, setPubProofUrl] = useState<string>("");
  const [isPublishing, setIsPublishing] = useState<boolean>(false);

  // Feedbacks & Evidence submitting pane on ACTIVE, PUBLISHED Startups
  const [addProofProjId, setAddProofProjId] = useState<string | null>(null);
  const [newProofTitle, setNewProofTitle] = useState<string>("");
  const [newProofType, setNewProofType] = useState<"simulation" | "prototype" | "media" | "test">("prototype");
  const [newProofDesc, setNewProofDesc] = useState<string>("");
  const [newProofUrl, setNewProofUrl] = useState<string>("");
  const [isSubmittingProof, setIsSubmittingProof] = useState<boolean>(false);

  // Direct Invest states
  const [activeInvestProjId, setActiveInvestProjId] = useState<string | null>(null);
  const [investAmount, setInvestAmount] = useState<number>(200);
  const [isInvesting, setIsInvesting] = useState<boolean>(false);

  useEffect(() => {
    fetchProfile();
    fetchStartups();
    fetchDrafts();
  }, [userEmail]);

  const fetchProfile = async () => {
    try {
      setIsProfileLoading(true);
      const res = await fetch("/api/startups/profile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: userEmail })
      });
      const data = await res.json();
      if (res.ok && data.profile) {
        setProfile(data.profile);
      } else {
        setProfile(null);
      }
    } catch (e: any) {
      console.error(e);
      addLog("STARTUP_PORTAL_ERR: Profil verileri yüklenemedi.");
    } finally {
      setIsProfileLoading(false);
    }
  };

  const fetchStartups = async () => {
    try {
      const res = await fetch("/api/startups/list");
      const data = await res.json();
      if (res.ok) {
        setStartups(data.startups);
        setPublishFeeNormal(data.publishFeeNormal);
        setPublishFeeVerified(data.publishFeeVerified);
        setBoostFee(data.boostFee);
      }
    } catch (e) {
      console.error("Listing fetched err:", e);
    }
  };

  const fetchDrafts = async () => {
    try {
      const res = await fetch("/api/startups/drafts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: userEmail })
      });
      const data = await res.json();
      if (res.ok && data.drafts) {
        setDrafts(data.drafts);
      }
    } catch (e) {
      console.error("Draft listing err:", e);
    }
  };

  // Secure Sign-Up KYC registration
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorText(null);
    setSuccessText(null);

    if (!regName.trim() || !regId.trim()) {
      setErrorText("Lütfen tüm alanları doldurun.");
      return;
    }

    if (regId.length < 8 || isNaN(Number(regId))) {
      setErrorText("T.C. Kimlik / Pasaport numarası en az 8 haneli ve sayısal olmalıdır.");
      return;
    }

    if (regName.trim().split(" ").length < 2) {
      setErrorText("Lütfen gerçek Ad ve Soyadınızı girin (örneğin: Ahmet Karaca).");
      return;
    }

    try {
      setIsSubmittingRegister(true);
      const res = await fetch("/api/startups/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: userEmail,
          fullName: regName,
          identityNo: regId,
          role: regRole
        })
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || "Doğrulama kaydı başarısız oldu.");
      }

      setProfile(data.profile);
      setSuccessText(data.message);
      addLog(`KYC_ONBOARDING: ${regName} için kimlik doğrulama onaylandı.`);
      fetchStartups();
      fetchDrafts();
    } catch (err: any) {
      setErrorText(err.message || "Kimlik tespiti yapılamadı.");
    } finally {
      setIsSubmittingRegister(false);
    }
  };

  // Create Workspace New Draft 
  const handleSaveDraft = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setErrorText(null);
    setSuccessText(null);

    if (!profile) return;
    if (!draftTitle.trim() || !draftCategory.trim()) {
      setErrorText("En azından Girişim Adı ve Alan seçimi taslak için de zorunludur.");
      return;
    }

    try {
      setIsSavingDraft(true);
      const res = await fetch("/api/startups/draft-save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: userEmail,
          projectId: selectedDraftId || undefined,
          title: draftTitle,
          category: draftCategory,
          problemSolved: draftProblem,
          strategyDescription: draftStrategy,
          fundingTarget: draftFundingTarget,
          equityOffer: draftEquity,
          stage: draftStage,
          materialsRequired: draftMaterialsRequired // PHYSICS FEASIBILITY: Physical Blueprint resources
        })
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error);
      }

      setSuccessText(data.message);
      addLog(`STUDIO_WORKSHOP: "${draftTitle}" taslağı fiziksel planla güncellendi.`);
      
      if (!selectedDraftId && data.project) {
        setSelectedDraftId(data.project.id);
      }
      
      fetchDrafts();
    } catch (err: any) {
      setErrorText(err.message || "Taslak kaydedilemedi.");
    } finally {
      setIsSavingDraft(false);
    }
  };

  // AI model Studio synthesis assistant suggestion optimizer helper mock simulation
  const handleOptimiseWithAI = () => {
    if (!draftProblem.trim()) {
      setErrorText("Lütfen önce çözülmeye çalışılan ana problemi tanımlayın.");
      return;
    }
    setErrorText(null);
    setIsOptimizingWithAI(true);
    addLog("SYNTHESIS_MODEL_ASSISTANT: Çapraz disiplin sentez modeli akış şeması kontrol ediliyor...");
    
    setTimeout(() => {
      const categoryKeywords = draftCategory.toLowerCase();
      let suggestions = "";
      let materialsSug = "ESP32 Mikroişlemci, ";
      if (categoryKeywords.includes("enerji")) {
        suggestions = "Sentez mekanizmasına termodinamik hücre entropisi ve yapay sinir ağı tabanlı voltaj stabilizatörleri eklendi. Hücre membran geçirgenliği rezonansı ile trafo manyetik kayıpları otonom sönümlenecek. Kararlılık Zeta katsayısı ideal limitsel denge oranı olan 0.707 oranında sabitlendi.";
        materialsSug += "IoT Sinyal Ölçüm Probu, Güç Hattı Trafo Sönümleyici Modülü, CT Kelepçe Akım Sensörü";
      } else if (categoryKeywords.includes("loji") || categoryKeywords.includes("yol") || categoryKeywords.includes("rota")) {
        suggestions = "Otonom lojistik düğümlerindeki mutabakat hızı için Raft Konsensüsü ve karınca kolonisi feromon iz sürme algoritmik kütüphaneleri entegre edildi. Ağdaki sensörler her 50ms'de bir otonom mutabakata vararak gecikmeyi %28 otonom regüle edecek.";
        materialsSug += "Android Takip Terminal Donanımı, GPS Alıcı Modülü, Hücresel LTE Hat Modülü";
      } else {
        suggestions = "Fizobia Yapay Analiz Modeli tarafından disiplinler arası rezonans tespiti yapıldı. Kuantum otonom geri besleme kontrol döngüsü ve Lyapunov asenkron durağanlık vektör diferansiyel eşikleri sisteme entegre edildi. Teorik uygulanabilirlik kanıtı %94 oranında optimize edildi.";
        materialsSug += "Yüksek Çözünürlüklü Kamera, Optik Mesafe Sensörü, Step Motor Sürücüsü";
      }
      
      setDraftStrategy(prev => (prev ? prev + "\n\n" : "") + suggestions);
      setDraftMaterialsRequired(materialsSug);
      setDraftStage("TheoryVerified");
      addLog("SYNTHESIS_MODEL_ASSISTANT: Girişim sentez stratejisi ve fiziki materyal listesi başarıyla optimize edildi.");
      setIsOptimizingWithAI(false);
      setSuccessText("Fizobia Model Studio Girişim fikir stratejenizi ve fiziksel materyal blueprintini otonom formüllerle optimize etti!");
    }, 2000);
  };

  // Create new draft template from scratch helper
  const handleCreateNewDraftTemplate = () => {
    setSelectedDraftId(null);
    setDraftTitle("Yeni Eko-Sinyal Projesi " + Math.floor(Math.random() * 100));
    setDraftCategory("Çevre & Biyoloji");
    setDraftProblem("");
    setDraftStrategy("");
    setDraftFundingTarget("3000");
    setDraftEquity("12");
    setDraftStage("Idea");
    setDraftMaterialsRequired("Metal Hazne Plakası, NDIR CO2 Gaz Sensörü, 12V Solenoid Valf, ESP32 Devresi");
    setErrorText(null);
    setSuccessText("Yeni bir atölye çizim tahtası açıldı. Bilgileri girip 'Taslağı Kaydet' tuşuna tıklayın.");
  };

  // Delete draft action
  const handleDeleteDraft = async (projectId: string) => {
    if (!confirm("Bu taslağı tamamen silmek istiyor musunuz?")) return;
    try {
      setIsDeletingDraft(true);
      const res = await fetch("/api/startups/draft-delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: userEmail, projectId })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);

      setSuccessText(data.message);
      addLog("STUDIO_WORKSHOP: Taslak silindi.");
      
      if (selectedDraftId === projectId) {
        setSelectedDraftId(null);
      }
      fetchDrafts();
    } catch (e: any) {
      setErrorText(e.message || "Hata.");
    } finally {
      setIsDeletingDraft(false);
    }
  };

  // Load draft to editor
  const handleLoadDraftToEditor = (draft: MockProject) => {
    setSelectedDraftId(draft.id);
    setDraftTitle(draft.title);
    setDraftCategory(draft.category);
    setDraftProblem(draft.problemSolved);
    setDraftStrategy(draft.strategyDescription);
    setDraftFundingTarget(String(draft.fundingTarget));
    setDraftEquity(String(draft.equityOffer));
    setDraftStage(draft.stage as any || "Idea");
    setDraftMaterialsRequired(draft.materialsRequired || "");
    setErrorText(null);
    setSuccessText(`"${draft.title}" taslağı editör masasına yüklendi.`);
  };

  // Secure evidence-based publication route (ANTI-PROMISE LAUNCH)
  const handlePublishDraftToStartup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile || !activePublishProjId) return;

    if (!pubProofTitle.trim() || !pubProofDesc.trim()) {
      setErrorText("Boş vaatler ile yayın yapılamaz! Uygulanabilir somut bir simülasyon veya prototip logu girmelisiniz.");
      return;
    }

    if (!draftMaterialsRequired || draftMaterialsRequired.trim().length < 8) {
      setErrorText("Fiziksel tescilli yayın için 'Materyal Blueprint' alanı zorunludur. Boş vaat fonlamasına izin verilmez.");
      return;
    }

    try {
      setIsPublishing(true);
      setErrorText(null);
      setSuccessText(null);

      const res = await fetch("/api/startups/publish-draft", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: userEmail,
          projectId: activePublishProjId,
          proofTitle: pubProofTitle,
          proofType: pubProofType,
          proofDescription: pubProofDesc,
          proofUrl: pubProofUrl,
          materialsRequired: draftMaterialsRequired // STRICT MAT BLUEPRINT MANDATE
        })
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error);
      }

      setProfile(prev => prev ? { ...prev, fzbBalance: data.newBalance } : null);
      setSuccessText(data.message);
      addLog(`STARTUP_ECOSYSTEM: "${data.project?.title}" girişimi somut kanıtlarla ekosisteme girdi. Hakem FZB onayı bekleniyor.`);
      
      // Cleanup
      setActivePublishProjId(null);
      setPubProofTitle("");
      setPubProofDesc("");
      setPubProofUrl("");
      
      if (selectedDraftId === activePublishProjId) {
        setSelectedDraftId(null);
      }

      fetchStartups();
      fetchDrafts();
    } catch (err: any) {
      setErrorText(err.message || "Yayınlanamadı.");
    } finally {
      setIsPublishing(false);
    }
  };

  // Post a new physical proof update / progress evidence logic
  const handleAddEvidenceProofOfWork = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile || !addProofProjId) return;

    if (!newProofTitle.trim() || !newProofDesc.trim()) {
      setErrorText("Kanıt doğrulaması için başlık ve metodoloji tanımlı olmalıdır.");
      return;
    }

    try {
      setIsSubmittingProof(true);
      const res = await fetch("/api/startups/add-proof", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: userEmail,
          projectId: addProofProjId,
          title: newProofTitle,
          type: newProofType,
          description: newProofDesc,
          proofUrl: newProofUrl
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);

      setSuccessText(data.message);
      addLog(`PROOF_OF_WORK: "${newProofTitle}" başlıklı ilerleme sisteme yüklendi. Yatırımcıların onayı bekleniyor.`);
      
      setAddProofProjId(null);
      setNewProofTitle("");
      setNewProofDesc("");
      setNewProofUrl("");
      
      fetchStartups();
    } catch (err: any) {
      setErrorText(err.message);
    } finally {
      setIsSubmittingProof(false);
    }
  };

  // Support / Invest coins to a startup
  const handleInvestProject = async (projectId: string) => {
    setErrorText(null);
    setSuccessText(null);

    if (!profile) return;

    if (investAmount <= 0) {
      setErrorText("Lütfen geçerli bir yatırım tutarı girin.");
      return;
    }

    if (profile.fzbBalance < investAmount) {
      setErrorText(`Mevcut bakiye sınırı aşıldı! Maksimum ${profile.fzbBalance} FZB destekleyebilirsiniz.`);
      return;
    }

    try {
      setIsInvesting(true);
      const res = await fetch("/api/startups/back", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: userEmail, projectId, amount: investAmount })
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error);
      }

      setProfile(prev => prev ? { ...prev, fzbBalance: data.newBalance } : null);
      setSuccessText(data.message);
      addLog(`INVESTMENT_COMPLETE: Girişime ${investAmount} FZB yatırıldı. Karşılığında %${data.calculatedShare} hisse kazanıldı.`);
      setActiveInvestProjId(null);
      fetchStartups();
    } catch (err: any) {
      setErrorText(err.message || "Yatırım işlemi iletilemedi.");
    } finally {
      setIsInvesting(false);
    }
  };

  // Upvote / Validate a proof of work submitted by other users
  const handleApproveProofLog = async (projectId: string, logId: string, logTitle: string) => {
    setErrorText(null);
    setSuccessText(null);

    try {
      const res = await fetch("/api/startups/approve-proof", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: userEmail, projectId, logId })
      });
      const data = await res.json();

      if (!res.ok) throw new Error(data.error);

      setSuccessText(data.message);
      addLog(`INVESTOR_VERIFICATION: "${logTitle}" somut gelişim kanıtı onaylandı. Künye değeri güncellendi.`);
      fetchStartups();
    } catch (err: any) {
      setErrorText(err.message || "Oylama başarısız.");
    }
  };

  // Submit expert FZB Feasibility Approval Certificate
  const handleIssueFzbApproval = async (projectId: string, title: string) => {
    setErrorText(null);
    setSuccessText(null);
    try {
      const res = await fetch("/api/startups/issue-fzb-approval", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: userEmail, projectId })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);

      setSuccessText(data.message);
      addLog(`FZB_AUDIT: "${title}" girişimi için FZB Fizibilite Onayı verildi.`);
      fetchStartups();
    } catch (err: any) {
      setErrorText(err.message || "Fizibilite doğrulaması iletilemedi.");
    }
  };

  // Report AI Vaporware / Speculation balloon flags
  const handleReportVaporwareFlag = async (projectId: string, title: string) => {
    const reason = prompt(`"${title}" projesini hayali yapay zeka verileri barındıran "Vaat Balonu" olduğu gerekçesiyle ihbar etmek için gerekçenizi yazın (3 ihbarda proje geri çekilir ve fonlar acil iade edilir):`);
    if (reason === null) return;
    if (!reason.trim()) {
      alert("İhbar gerekçesi girmek zorunludur!");
      return;
    }
    setErrorText(null);
    setSuccessText(null);
    try {
      const res = await fetch("/api/startups/flag-vaporware", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: userEmail, projectId, reason: reason.trim() })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);

      setSuccessText(data.message);
      addLog(`VAPORWARE_FLAG: "${title}" içi fantezi veri ihbarı yapıldı.`);
      fetchStartups();
    } catch (err: any) {
      setErrorText(err.message || "İhbar kaydı iletilemedi.");
    }
  };

  // Simulative VISA/Mastercard FZB refill complete
  const handleRechargeTokens = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!shopCardName.trim() || !shopCardNo.trim()) {
      alert("Lütfen kart hamili ve numarasını doldurun.");
      return;
    }

    setIsBuyingTokens(true);
    try {
       const res = await fetch("/api/startups/buy-tokens", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: userEmail, amount: shopAmount })
      });
      const data = await res.json();
      if (res.ok) {
        setProfile(prev => prev ? { ...prev, fzbBalance: data.newBalance } : null);
        addLog(`WALLET_RECHARGE: ${shopAmount} FZB hesaba eklendi.`);
        setShowTokenShop(false);
        setShopCardName("");
        setShopCardNo("");
        setSuccessText(`Tebrikler! ${shopAmount} FZB bakiye yüklemesi başarıyla aktarıldı.`);
      }
    } catch(err) {
      console.error(err);
    } finally {
      setIsBuyingTokens(false);
    }
  };

  // Filter computations
  const filteredStartups = startups.filter(proj => {
    const matchesSearch = proj.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          proj.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          proj.problemSolved.toLowerCase().includes(searchQuery.toLowerCase());
    
    if (!matchesSearch) return false;

    if (selectedFilter === "all") return true;
    if (selectedFilter === "boosted") return proj.isBoosted;
    
    // Liga filters
    if (selectedFilter === "incubation") return proj.league === "Incubation";
    if (selectedFilter === "prototype") return proj.league === "Prototype";
    if (selectedFilter === "enterprise") return proj.league === "Enterprise";

    return true;
  });

  if (isProfileLoading) {
    return (
      <div id="startup-loading" className="flex-1 flex flex-col items-center justify-center p-12 min-h-[60vh] bg-[#0A0C10]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500 mb-4"></div>
        <div className="text-xs text-slate-400 font-mono tracking-widest uppercase">Güvenli KYC Onaylı Ağ Bağlantısı Kuruluyor...</div>
      </div>
    );
  }

  // FORCE KYC FOR NEW USERS
  if (!profile) {
    return (
      <div id="kyc-onboarding-screen" className="flex-grow flex flex-col lg:flex-row items-stretch justify-center p-6 gap-6 max-w-6xl mx-auto w-full">
        {/* Onboarding info */}
        <div className="flex-1 text-left space-y-6 flex flex-col justify-center max-w-xl">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded bg-[#10B981]/10 border border-[#10B981]/20 text-[#10B981] text-xs font-mono w-fit">
            <CheckCircle2 size={13} />
            <span>KİMLİK DOĞRULAMALI GÜVENLİ ERİŞİM</span>
          </div>

          <h2 className="text-3xl font-extrabold tracking-tight text-white font-display">
            Fizobia Startup <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-indigo-400">Yatırım & Kuluçka Portalı</span>
          </h2>

          <p className="text-xs text-slate-400 leading-relaxed font-sans">
            Fizobia sentez motoru ile otonom ürettiğiniz interdisipliner projelerinizi ticarileştirmek, diğer geliştiricilerin somut projelerini desteklemek ve yatırımcı ortaklığı kurmak için bu portala katılabilirsiniz.
          </p>

          <div className="space-y-4 border-l-2 border-indigo-500/20 pl-4 py-1 text-xs">
            <div className="space-y-1">
              <h4 className="font-bold text-slate-200">🔍 T.C. Kimlik / Pasaport Doğrulaması</h4>
              <p className="text-slate-400 leading-normal">
                Startup ve yatırım dünyasının güvenliğini korumak amacıyla; tüm kayıt işlemlerinde gerçek kimlik beyanı zorunludur. Dolandırıcılık ve hayali vaat projeleri bu şekilde otonom engellenir.
              </p>
            </div>
            <div className="space-y-1">
              <h4 className="font-bold text-slate-200">💎 Fizobia Token (FZB) ve Gerçek Dünya Kanıtları</h4>
              <p className="text-slate-400 leading-normal">
                Girişimciler fikirlerini önce atölyede taslak olarak geliştirir. Prototip, simülasyon veya fiziksel test çıktısı (kanıt) eklemeden boş vaatlerle startup ekosistemine giremezler. Somut kanıt girdikçe tokenlerin rasyonal ortaklık pay değeri dinamik olarak artar!
              </p>
            </div>
          </div>
        </div>

        {/* KYC Verification Registration Card */}
        <div className="w-full lg:w-[450px] shrink-0 border border-slate-800 bg-[#0E1117] rounded-xl overflow-hidden relative shadow-[0_15px_30px_rgba(0,0,0,0.6)] self-center p-6 space-y-6">
          <div className="absolute top-0 left-0 right-0 h-[3px] bg-gradient-to-r from-emerald-500 via-indigo-500 to-indigo-600"></div>

          <div className="text-center space-y-1">
            <Lock size={20} className="text-indigo-400 mx-auto animate-pulse" />
            <h3 className="text-sm font-bold text-white uppercase tracking-wider font-mono">GÜVENLİ ÜYE DOĞRULAMA KAYDI</h3>
            <p className="text-[10px] text-slate-500">Startup ekosistemine giriş için adınızı ve T.C./Pasaport numaranızı doğrulayın</p>
          </div>

          <form onSubmit={handleRegister} className="space-y-4">
            {errorText && (
              <div className="p-3 rounded bg-rose-950/20 border border-rose-900/40 text-rose-400 text-[11px] flex gap-2 items-start">
                <AlertCircle size={14} className="shrink-0 mt-0.5" />
                <p>{errorText}</p>
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-[10px] uppercase text-indigo-400 font-bold block">E-POSTA ADRESİ</label>
              <input
                type="text"
                disabled
                value={userEmail}
                className="w-full px-3 py-2 bg-slate-950/40 border border-slate-800 rounded text-xs text-slate-400 font-mono outline-none cursor-not-allowed"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-[10px] uppercase text-indigo-400 font-bold block">AD SOYAD (KİMLİKTE YAZDIĞI GİBİ)</label>
              <input
                type="text"
                required
                placeholder="Örn: Yasin Karademir"
                value={regName}
                onChange={(e) => setRegName(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800/80 rounded text-xs text-white focus:border-indigo-500/80 outline-none transition-all font-sans"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-[10px] uppercase text-indigo-400 font-bold block">T.C. KİMLİK / PASAPORT NO (ZORUNLU)</label>
              <input
                type="text"
                required
                maxLength={11}
                placeholder="Gerçek kimlik numaranızı yazın"
                value={regId}
                onChange={(e) => setRegId(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800/80 rounded text-xs text-white focus:border-indigo-500/80 outline-none transition-all font-mono"
              />
              <p className="text-[9px] text-slate-500 leading-snug">
                Kimlik verileriniz, diğer tarafların güven duyması ve yatırım sözleşmesi tahsisatında resmi pay aktarımı için saklanır.
              </p>
            </div>

            <div className="space-y-1.5">
              <label className="text-[10px] uppercase text-indigo-400 font-bold block">EKOSİSTEM ROLÜNÜZ</label>
              <select
                value={regRole}
                onChange={(e: any) => setRegRole(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800/80 rounded text-xs text-white focus:border-indigo-500/80 outline-none cursor-pointer"
              >
                <option value="both">Geliştirici + Yatırımcı (Her İkisi)</option>
                <option value="developer">Girişimci ve Geliştirici (Proje Yayınlar)</option>
                <option value="investor">Sadece Yatırımcı (Projeleri Fonlar)</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={isSubmittingRegister}
              className="w-full py-2.5 bg-gradient-to-r from-emerald-600 to-indigo-600 hover:from-emerald-500 hover:to-indigo-500 text-white text-xs font-bold uppercase tracking-wider rounded transition-all cursor-pointer flex items-center justify-center gap-2 shadow-[0_4px_15px_rgba(16,185,129,0.2)]"
            >
              <CheckCircle2 size={14} />
              <span>{isSubmittingRegister ? "Kimlik Sorgulanıyor..." : "KİMLİĞİ DOĞRULA VE BAŞLA"}</span>
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col lg:flex-row overflow-hidden relative w-full anim-fade-in bg-[#0A0C10]">
      
      {/* LEFT SIDEBAR: PROFILE & STUDIO WORKSPACE EDITOR */}
      <aside className="w-full lg:w-[380px] bg-[#0D0F14] border-b lg:border-b-0 lg:border-r border-slate-800/80 shrink-0 flex flex-col gap-5 overflow-y-auto escrollbar select-none">
        
        {/* Profile, Balance and Simulate Token recharge */}
        <div className="p-4 border-b border-slate-800/60 bg-[#12151C]/40 space-y-3.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-indigo-500/10 border border-indigo-500/35 flex items-center justify-center text-indigo-400">
                <User size={15} />
              </div>
              <div className="text-left">
                <h4 className="text-xs font-black text-white">{profile.fullName}</h4>
                <p className="text-[9px] text-slate-500 font-mono">
                  KYC ID: {profile.identityNo.substring(0, 3)}***{profile.identityNo.substring(profile.identityNo.length - 2)}
                </p>
              </div>
            </div>
            <span className="text-[8px] tracking-widest font-mono font-bold text-emerald-400 bg-emerald-950/40 border border-emerald-900/40 px-2 py-0.5 rounded">
              • ONAYLI KYC
            </span>
          </div>

          <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-900/80 flex justify-between items-center">
            <div>
              <span className="text-[8px] text-slate-500 uppercase font-mono block">CÜZDAN BAKİYESİ</span>
              <div className="flex items-center gap-1 mt-0.5">
                <Coins size={13} className="text-yellow-500" />
                <span className="text-sm font-black text-white font-mono">{profile.fzbBalance}</span>
                <span className="text-[9px] text-indigo-400 font-mono">FZB</span>
              </div>
            </div>
            <button
              onClick={() => setShowTokenShop(true)}
              className="px-2 py-1 bg-indigo-600 hover:bg-indigo-500 text-white text-[9px] font-bold uppercase tracking-wider rounded transition-colors flex items-center gap-1 cursor-pointer"
            >
              <PlusCircle size={10} />
              <span>YÜKLE</span>
            </button>
          </div>

          {/* SIMULATED VISA CARD SHOP FOR RECHARGES */}
          {showTokenShop && (
            <div className="border border-indigo-600 bg-slate-950 p-3 rounded-lg space-y-3 relative anim-fade-in">
              <div className="flex justify-between items-center border-b border-slate-800 pb-1.5">
                <span className="text-[9px] font-bold text-indigo-400 uppercase tracking-wider font-mono">Simüle Mastercard Tek-Tık POS</span>
                <button onClick={() => setShowTokenShop(false)} className="text-[10px] text-slate-400 hover:text-white font-mono">X</button>
              </div>
              <form onSubmit={handleRechargeTokens} className="space-y-2.5 text-left">
                <div className="space-y-1">
                  <label className="text-[8px] text-slate-500 font-mono">TUTAR SEÇİMİ</label>
                  <select 
                    value={shopAmount}
                    onChange={(e) => setShopAmount(parseInt(e.target.value))}
                    className="w-full bg-[#12151C] border border-slate-800 p-1 rounded text-white text-xs"
                  >
                    <option value={500}>500 FZB - 100 TL</option>
                    <option value={1000}>1000 FZB - 200 TL</option>
                    <option value={2000}>2000 FZB - 400 TL</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-[8px] text-slate-500 font-mono">KART BILGILERI</label>
                  <input 
                    type="text" 
                    required 
                    placeholder="Ad Soyad" 
                    value={shopCardName}
                    onChange={(e) => setShopCardName(e.target.value)}
                    className="w-full bg-[#12151C] border border-slate-800 p-1.5 rounded text-[11px] text-white"
                  />
                  <input 
                    type="text" 
                    required 
                    maxLength={16}
                    placeholder="16 Haneli Kart No" 
                    value={shopCardNo}
                    onChange={(e) => setShopCardNo(e.target.value)}
                    className="w-full bg-[#12151C] border border-slate-800 p-1.5 rounded text-[11px] text-white font-mono mt-1"
                  />
                </div>
                <button 
                  type="submit"
                  disabled={isBuyingTokens}
                  className="w-full py-1 bg-yellow-600 hover:bg-yellow-500 text-white rounded text-[10px] uppercase font-bold cursor-pointer"
                >
                  {isBuyingTokens ? "POS Onayı Alınıyor..." : "LİMİTSİZ SİMÜLE ÖDE"}
                </button>
              </form>
            </div>
          )}
        </div>

        {/* WORKSHOP / ATÖLYE SECTIONS */}
        <div className="px-4 space-y-4 text-left">
          
          {/* USER DRAFTS WORKSPACE LISTINGS */}
          {profile.role !== "investor" && (
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-[10px] uppercase font-bold tracking-wider text-emerald-400 font-mono flex items-center gap-1">
                  <Cpu size={12} />
                  <span>TASLAK ATÖLYEM ({drafts.length})</span>
                </span>
                
                <button
                  onClick={handleCreateNewDraftTemplate}
                  className="text-[9px] bg-slate-900 hover:bg-slate-800 border border-slate-800 text-white font-mono px-2 py-0.5 rounded flex items-center gap-1 cursor-pointer"
                >
                  <Plus size={10} />
                  <span>YENİ TUVAL</span>
                </button>
              </div>

              {drafts.length === 0 ? (
                <div className="p-3 border border-dashed border-slate-800 rounded-lg text-center text-slate-500 text-[10px]">
                  Fizobia sentez sisteminizden taslak eklemediniz. Aşağıdan yeni proje taslak tahtası açın!
                </div>
              ) : (
                <div className="space-y-1.5 max-h-[140px] overflow-y-auto escrollbar">
                  {drafts.map((d) => (
                    <div 
                      key={d.id}
                      className={`p-2 rounded border transition-all text-left relative group ${
                        selectedDraftId === d.id
                          ? "border-emerald-500 bg-[#12181C]"
                          : "border-slate-800/60 bg-[#0E1116] hover:border-slate-700"
                      }`}
                    >
                      <div className="pr-12 cursor-pointer" onClick={() => handleLoadDraftToEditor(d)}>
                        <h5 className="text-[11px] font-black text-slate-200 truncate">{d.title}</h5>
                        <p className="text-[9px] text-[#10B981] font-mono leading-none mt-1">🧬 {d.category}</p>
                      </div>
                      
                      <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1 opacity-60 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={() => handleDeleteDraft(d.id)}
                          className="p-1 hover:text-rose-500 text-slate-500"
                          title="Sil"
                        >
                          <Trash2 size={11} />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ACTIVE SELECTED DRAFT INTERACTIVE MANIPULATION AREA */}
          {profile.role !== "investor" ? (
            <div className="border border-slate-800/80 bg-[#12151C]/60 p-3.5 rounded-xl space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800/60 pb-2">
                <div className="flex items-center gap-1.5 text-white">
                  <Wand2 size={13} className="text-indigo-400" />
                  <span className="text-[11px] font-bold font-mono uppercase tracking-wider">
                    {selectedDraftId ? "FİKİR DETAYLANDIRMA MASASI" : "YENİ TASLAK TASARIMI"}
                  </span>
                </div>
                {selectedDraftId && (
                  <span className="text-[8px] bg-slate-900 border border-slate-800 text-slate-400 font-mono px-1 rounded uppercase">
                    KOD: {selectedDraftId.substring(0, 8)}
                  </span>
                )}
              </div>

              <form onSubmit={handleSaveDraft} className="space-y-3 font-sans text-xs">
                <div className="space-y-1">
                  <label className="text-[8px] text-slate-500 block uppercase font-mono font-bold">GİRİŞİM BAŞLIĞI</label>
                  <input
                    type="text"
                    required
                    value={draftTitle}
                    onChange={(e) => setDraftTitle(e.target.value)}
                    placeholder="Örn: Biyomimetik Fotosentez Pili"
                    className="w-full bg-slate-950 border border-slate-800 p-1.5 rounded text-[11px] focus:border-indigo-500 text-white outline-none"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[8px] text-slate-500 block uppercase font-mono font-bold">DİSİPLİNLER ARASI ALAN</label>
                  <input
                    type="text"
                    required
                    value={draftCategory}
                    onChange={(e) => setDraftCategory(e.target.value)}
                    placeholder="Örn: Biyoloji & Mühendislik"
                    className="w-full bg-slate-950 border border-slate-800 p-1.5 rounded text-[11px] focus:border-indigo-500 text-white outline-none"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[8px] text-slate-500 block uppercase font-mono font-bold">İŞLENEN REEL PROBLEM</label>
                  <textarea
                    rows={2}
                    value={draftProblem}
                    onChange={(e) => setDraftProblem(e.target.value)}
                    placeholder="Sahanın karşılaştığı dikey açmaz nedir?"
                    className="w-full bg-slate-950 border border-slate-800 p-1.5 rounded text-[11px] focus:border-indigo-500 text-slate-300 outline-none leading-relaxed"
                  />
                </div>

                <div className="space-y-1 relative">
                  <div className="flex justify-between items-center mb-0.5">
                    <label className="text-[8px] text-slate-500 uppercase font-mono font-bold">FİZOBİA ENTEGRE STRATEJİSİ VE MATEMATİĞİ</label>
                    <button
                      type="button"
                      onClick={handleOptimiseWithAI}
                      disabled={isOptimizingWithAI || !draftProblem}
                      className="text-[8px] px-1.5 py-0.5 bg-indigo-950 border border-indigo-900/60 text-indigo-400 hover:text-indigo-300 flex items-center gap-1 rounded transition-colors font-mono font-bold disabled:opacity-40 cursor-pointer"
                    >
                      <Sparkles size={8} />
                      <span>{isOptimizingWithAI ? "ANALİZ EDİLİYOR..." : "Y.Z. METRİKLERİ EKLE"}</span>
                    </button>
                  </div>
                  <textarea
                    rows={4}
                    value={draftStrategy}
                    onChange={(e) => setDraftStrategy(e.target.value)}
                    placeholder="Optimizasyon formülasyonu ve çözüm teorisi..."
                    className="w-full bg-slate-950 border border-slate-800 p-1.5 rounded text-[11px] focus:border-indigo-500 text-slate-200 outline-none leading-relaxed"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[8px] text-slate-500 block uppercase font-mono font-bold">🔧 MATERYAL BLUEPRINT (REEL MATERYAL / ENSTRÜMANTASYON GİRDİSİ)</label>
                  <textarea
                    rows={2}
                    required
                    value={draftMaterialsRequired}
                    onChange={(e) => setDraftMaterialsRequired(e.target.value)}
                    placeholder="Bu fikri sahada inşa etmek için gerekli gerçek dünya girdilerini yazın (Örn: Metal Hazne Plakası, NDIR CO2 Sensörü, ESP32 Devresi...)"
                    className="w-full bg-slate-950 border border-slate-800 p-1.5 rounded text-[11px] focus:border-emerald-500 text-emerald-400 font-mono outline-none leading-relaxed"
                  />
                  <div className="text-[8px] text-slate-550 italic font-mono">
                    * Fizobia vaat balonu tesciline izin vermez; materyal girdisi tescilde zorunludur.
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <label className="text-[8px] text-slate-500 block font-mono font-bold">ASGARİ BAKİYE HEDEFİ</label>
                    <input
                      type="number"
                      required
                      value={draftFundingTarget}
                      onChange={(e) => setDraftFundingTarget(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 p-1 rounded text-[11px] text-white font-mono"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-[8px] text-slate-500 block font-mono font-bold">TEKLİF HİSSE (%)</label>
                    <input
                      type="number"
                      required
                      min={1}
                      max={90}
                      value={draftEquity}
                      onChange={(e) => setDraftEquity(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 p-1 rounded text-[11px] text-white font-mono"
                    />
                  </div>
                </div>

                <div className="flex gap-2">
                  <button
                    type="submit"
                    disabled={isSavingDraft}
                    className="flex-1 py-1.5 bg-slate-800 hover:bg-slate-700 text-white font-mono text-[10px] font-bold uppercase rounded cursor-pointer transition-colors"
                  >
                    {isSavingDraft ? "Kaydediliyor..." : "TASLAĞI KAYDET"}
                  </button>

                  {selectedDraftId && (
                    <button
                      type="button"
                      onClick={() => {
                        setActivePublishProjId(selectedDraftId);
                        setPubProofTitle(draftTitle + " - Canlı Simülasyon Çıktısı");
                      }}
                      className="px-3 py-1.5 bg-gradient-to-r from-emerald-600 to-indigo-600 hover:from-emerald-500 hover:to-indigo-500 text-white font-mono text-[10px] font-black uppercase rounded cursor-pointer transition-all"
                    >
                      YAYINA GEÇİR 🚀
                    </button>
                  )}
                </div>
              </form>
            </div>
          ) : (
            <div className="border border-slate-800 bg-[#12151C]/40 p-4 rounded-xl text-xs text-slate-400 space-y-2 text-center select-none">
              <Lock size={16} className="mx-auto text-indigo-400" />
              <p className="font-bold">Sadece Yatırımcı Rolündesiniz</p>
              <p className="text-[10px]/relaxed text-slate-500">
                Lojistik, enerji ve biyoloji alanındaki doğrulanmış prototipleri inceleyerek FZB tokenlerinizle hisse yatırımı yapabilirsiniz.
              </p>
            </div>
          )}

        </div>

      </aside>

      {/* RIGHT CHANNELS: ACTIVE STARTUP MARKETPLACE, ANTI-PROMISE LISTS, EVIDENCE FEEDBOOKS */}
      <main className="flex-1 p-5 flex flex-col gap-5 overflow-y-auto bg-[#0A0C10] select-none text-left">
        
        {/* TOP STATUS AND ERROR MESSAGES HUD */}
        {(errorText || successText) && (
          <div className="anim-fade-in duration-200">
            {errorText && (
              <div className="p-3.5 rounded-lg bg-rose-950/20 border border-rose-900/35 text-rose-300 text-xs flex gap-2 items-center">
                <AlertCircle size={14} className="shrink-0" />
                <p className="flex-1 text-left">{errorText}</p>
                <button onClick={() => setErrorText(null)} className="ml-auto font-mono text-[9px] hover:text-white font-bold text-slate-400">X</button>
              </div>
            )}
            {successText && (
              <div className="p-3.5 rounded-lg bg-emerald-950/20 border border-emerald-900/35 text-emerald-300 text-xs flex gap-2 items-center">
                <CheckCircle2 size={14} className="shrink-0 animate-bounce" />
                <p className="flex-1 text-left">{successText}</p>
                <button onClick={() => setSuccessText(null)} className="ml-auto font-mono text-[9px] hover:text-white font-bold text-slate-400">X</button>
              </div>
            )}
          </div>
        )}

        {/* HERO HEADER */}
        <div className="border border-slate-800/80 bg-[#0E1117] px-5 py-4 rounded-xl relative overflow-hidden flex flex-col md:flex-row items-center justify-between gap-5 tracking-tight shadow-md">
          <div className="absolute top-0 left-0 bottom-0 w-[4px] bg-emerald-500"></div>
          
          <div className="space-y-1.5 text-left md:max-w-2xl">
            <div className="flex items-center gap-2">
              <span className="text-[9px] px-2 py-0.5 bg-emerald-950 text-emerald-400 border border-emerald-905 rounded font-mono font-bold uppercase">
                FİZOBİA STARTUP & KULUÇKA PORTALİ
              </span>
              <span className="text-slate-600 font-mono">/</span>
              <span className="text-[9px] text-indigo-400 font-mono">ANTI-PROMISE PROTOTYPE TRACKER</span>
            </div>
            
            <h3 className="text-lg md:text-xl font-black text-white">
              Vaatler Değerlendirilemez! Sadece Çalışan Çıktıları ve Kanıtları Fonla
            </h3>
            
            <p className="text-[10px] text-slate-400 leading-relaxed">
              Ekosisteme sadece fikirle değil, mutlaka bir **somut çıktı** (veri/simülasyon) göstererek girilir. Projeler gerçek hayatta uygulandıkça ve doğrulamalar yatırımcı hakemlerce onaylandıkça, proje tokenleri **LİG** yükselir ve **dinamik değerlemesi** başlar!
            </p>
          </div>

          <div className="flex gap-4 bg-slate-950/60 p-3 border border-slate-900 rounded-lg shrink-0 text-center font-mono text-xs">
            <div>
              <span className="text-[8px] text-slate-500 uppercase block leading-none mb-1">AKTİF GİRİŞİM</span>
              <span className="text-sm font-black text-white">{startups.filter(p=>!p.isDraft).length}</span>
            </div>
            <div className="w-px bg-slate-800 my-1"></div>
            <div>
              <span className="text-[8px] text-slate-500 uppercase block leading-none mb-1">ORTAKLIK SÖZLEŞMESİ</span>
              <span className="text-sm font-black text-emerald-400">
                {startups.filter(p=>!p.isDraft).reduce((sum, s) => sum + s.backersList.length, 0)}
              </span>
            </div>
          </div>
        </div>

        {/* PROOF-BASED PUBLISHING FLOATER SCREEN PANEL */}
        {activePublishProjId && (
          <div className="border border-emerald-600 bg-slate-950/95 p-4 rounded-xl space-y-3 relative shadow-2xl anim-fade-in border-dashed">
            <h4 className="text-xs font-black text-emerald-400 font-mono flex items-center gap-1.5 uppercase">
              <Rocket size={14} className="animate-spin duration-300" />
              <span>GİRİŞİMİ DOĞRULANABİLİR GERÇEK DÜNYA KANITIYLA CANLIYA AL</span>
            </h4>
            <p className="text-[10px] text-slate-400 leading-relaxed">
              "Fizobia vaad değil somut kanıt arar." Çalışan simülasyon çıktısı verilerinizi belirterek projenizi kuluçka ligine taşıyın. 
              Doğrulanmış girilen prototipler için yayın ücreti sadece <strong className="text-emerald-400">{publishFeeVerified} FZB</strong>'dir (Normal: 80 FZB).
            </p>

            <form onSubmit={handlePublishDraftToStartup} className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              <div className="space-y-2 text-left">
                <div className="space-y-0.5">
                  <label className="text-[8px] text-slate-500 font-bold uppercase font-mono block">DOĞRULAMA ÇIKTISI BAŞLIĞI</label>
                  <input
                    type="text"
                    required
                    placeholder="Örn: 1.0-A Fiziksel Test Ölçüm Log ve Grafik Verisi"
                    value={pubProofTitle}
                    onChange={(e) => setPubProofTitle(e.target.value)}
                    className="w-full bg-[#12151C] border border-slate-800 p-2 rounded text-xs text-white"
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-0.5">
                    <label className="text-[8px] text-slate-500 font-bold uppercase font-mono block">KANIT SİSTEMİ</label>
                    <select
                      value={pubProofType}
                      onChange={(e: any) => setPubProofType(e.target.value)}
                      className="w-full bg-[#12151C] border border-slate-800 p-1.5 rounded text-xs text-white"
                    >
                      <option value="simulation">Veri Akışı / Simülasyon</option>
                      <option value="prototype">ESP32/Ardu fiziksel Prototip</option>
                      <option value="media">Fotoğraf & Video Kanıtı</option>
                      <option value="test">Laboratuvar Kimya Raporu</option>
                    </select>
                  </div>
                  <div className="space-y-0.5">
                    <label className="text-[8px] text-slate-500 font-bold uppercase font-mono block">PROTOTİP GÖRSEL URL (OPSİYONEL)</label>
                    <input
                      type="text"
                      placeholder="Görsel linki (Boş ise şablon atanır)"
                      value={pubProofUrl}
                      onChange={(e) => setPubProofUrl(e.target.value)}
                      className="w-full bg-[#12151C] border border-slate-800 p-1.5 rounded text-xs text-white"
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-1 text-left flex flex-col justify-between">
                <div className="space-y-0.5">
                  <label className="text-[8px] text-slate-500 font-bold uppercase font-mono block">KANITLANAN TEKNİK METRİKLER (EN AZ 20 KARAKTER)</label>
                  <textarea
                    required
                    rows={3}
                    placeholder="Lütfen vaat olmayan gerçekçi gözlem sonuçlarını yazın. Örn: 'Akış sensörü 2.5 BAR altında %98 sızdırmazlık teyit etti, simüle zeta sönümü 0.707 rezonansına yerleşti.'"
                    value={pubProofDesc}
                    onChange={(e) => setPubProofDesc(e.target.value)}
                    className="w-full bg-[#12151C] border border-slate-800 p-1.5 rounded text-xs text-slate-200"
                  />
                </div>
                
                <div className="flex gap-2 justify-end">
                  <button
                    type="button"
                    onClick={() => setActivePublishProjId(null)}
                    className="px-3 py-1 bg-slate-900 border border-slate-800 rounded text-[10px] text-slate-400 cursor-pointer"
                  >
                    VAZGEÇ
                  </button>
                  <button
                    type="submit"
                    disabled={isPublishing}
                    className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded text-[10px] font-mono cursor-pointer"
                  >
                    {isPublishing ? "EKOSISTEME AKTARILIYOR..." : `KANITI ONAYLA & YAYINLA (${publishFeeVerified} FZB)`}
                  </button>
                </div>
              </div>
            </form>
          </div>
        )}

        {/* SEARCH AND FILTERS TOOLBAR */}
        <div className="flex flex-col md:flex-row items-stretch justify-between gap-3 bg-[#0E1117] p-2.5 rounded-xl border border-slate-800/60">
          <div className="flex-1 relative">
            <input
              type="text"
              placeholder="Girişim başlığı, disiplin alanı veya problem analizi ara..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-[#12151C] border border-slate-800/80 rounded-lg px-4 py-2.5 text-xs text-white focus:border-indigo-500 outline-none transition-all pl-9"
            />
            <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-550 text-xs">🔍</span>
          </div>

          <div className="flex gap-1.5 flex-wrap">
            <button
              onClick={() => setSelectedFilter("all")}
              className={`px-3 py-1 text-xs font-bold leading-none cursor-pointer border rounded ${
                selectedFilter === "all"
                  ? "bg-slate-700 text-white border-slate-600"
                  : "bg-[#12151C] text-slate-400 border-slate-800 hover:text-white"
              }`}
            >
              Tümü
            </button>
            <button
              onClick={() => setSelectedFilter("incubation")}
              className={`px-3 py-1 text-xs font-bold leading-none cursor-pointer border rounded flex items-center gap-1 ${
                selectedFilter === "incubation"
                  ? "bg-emerald-900/60 text-emerald-300 border-emerald-800"
                  : "bg-[#12151C] text-slate-400 border-slate-800 hover:text-white"
              }`}
            >
              <span>🚀 Kuluçka</span>
            </button>
            <button
              onClick={() => setSelectedFilter("prototype")}
              className={`px-3 py-1 text-xs font-bold leading-none cursor-pointer border rounded flex items-center gap-1 ${
                selectedFilter === "prototype"
                  ? "bg-amber-900/60 text-amber-300 border-amber-850"
                  : "bg-[#12151C] text-slate-400 border-slate-850 hover:text-white"
              }`}
            >
              <span>⚙️ Prototip</span>
            </button>
            <button
              onClick={() => setSelectedFilter("enterprise")}
              className={`px-3 py-1 text-xs font-bold leading-none cursor-pointer border rounded flex items-center gap-1 ${
                selectedFilter === "enterprise"
                  ? "bg-indigo-900/60 text-indigo-300 border-indigo-800"
                  : "bg-[#12151C] text-slate-400 border-slate-800 hover:text-white"
              }`}
            >
              <span>🌐 Saha Entegrasyon</span>
            </button>
            <button
              onClick={() => setSelectedFilter("boosted")}
              className={`px-3 py-1 text-xs font-bold leading-none cursor-pointer border rounded flex items-center gap-1 ${
                selectedFilter === "boosted"
                  ? "bg-rose-950/60 text-rose-300 border-rose-800"
                  : "bg-[#12151C] text-slate-400 border-slate-800 hover:text-rose-450"
              }`}
            >
              <Flame size={12} className="text-rose-500 animate-pulse animate-bounce" />
              <span>Öne Çıkanlar</span>
            </button>
          </div>
        </div>

        {/* STARTUP CATALOG LISTINGS */}
        <div className="grid grid-cols-1 gap-6">
          {filteredStartups.length === 0 ? (
            <div className="border border-dashed border-slate-800 p-12 text-center rounded-xl space-y-2">
              <span className="text-2xl">🌵</span>
              <p className="text-xs text-slate-400 font-mono">Aradığınız lig ve kriterlerde tescillenmiş yayında girişim bulunmamaktadır.</p>
              <button 
                onClick={() => { setSelectedFilter("all"); setSearchQuery(""); }}
                className="text-[10px] uppercase font-bold tracking-widest text-[#10B981] underline cursor-pointer"
              >
                Filtreleri Sıfırla
              </button>
            </div>
          ) : (
            filteredStartups.map((proj) => {
              const capRaisedPrg = Math.min(100, Math.round((proj.fundingRaised / proj.fundingTarget) * 100));
              const isCreatorSelf = (profile.identityNo === proj.creatorIdentity || profile.fullName === proj.creatorName);

              // Target limit is league based: Incubation 3000 max, Prototype 7500 max, Enterprise 35000 max
              let maxLimitFzb = 3000;
              let leagueHexBadge = "bg-emerald-950 text-emerald-400 border-emerald-900";
              let leagueLabel = "🚀 Kuluçka Ligi";
              if (proj.league === "Prototype") {
                maxLimitFzb = 7500;
                leagueLabel = "⚙️ Prototip Ligi";
                leagueHexBadge = "bg-amber-950 text-amber-300 border-amber-900";
              } else if (proj.league === "Enterprise") {
                maxLimitFzb = 35000;
                leagueLabel = "🌐 Saha Entegrasyon Ligi";
                leagueHexBadge = "bg-indigo-950 text-indigo-300 border-indigo-900";
              }

              // Dynamic token pricing engine! Initially 1.0 (mean: 1% equity = 100 FZB), can rise up to 10.0 (mean: 1% equity = 1000 FZB)
              const baseValue1Percent = 100;
              const current1PercentValue = Math.round(baseValue1Percent * proj.valuationMultiplier);

              return (
                <div 
                  key={proj.id}
                  className={`border rounded-xl bg-[#0E1117] overflow-hidden relative shadow-lg group transition-all duration-300 text-left ${
                    proj.isBoosted 
                      ? "border-amber-500/50 shadow-[0_0_20px_rgba(245,158,11,0.06)] bg-gradient-to-b from-[#141822] to-[#0E1117]" 
                      : "border-slate-800 hover:border-slate-700 bg-[#0E1117]"
                  }`}
                >
                  {/* Top booster decor line */}
                  {proj.isBoosted && (
                    <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-amber-400 via-yellow-500 to-amber-600"></div>
                  )}

                  {/* Primary content area */}
                  <div className="p-5 space-y-4">
                    
                    {/* Header info bar */}
                    <div className="flex flex-col md:flex-row md:items-start justify-between gap-3.5">
                      <div className="space-y-1">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className="text-[9px] bg-slate-950 text-indigo-400 font-mono border border-slate-850 px-2 py-0.5 rounded font-bold uppercase">
                            🧬 {proj.category}
                          </span>
                          
                          <span className={`text-[9px] font-mono border px-2 py-0.5 rounded font-black uppercase ${leagueHexBadge}`}>
                            {leagueLabel}
                          </span>

                          {proj.isBoosted && (
                            <span className="text-[8px] bg-amber-950 text-amber-300 border border-amber-900/40 px-1.5 py-0.5 rounded font-mono font-bold uppercase tracking-widest flex items-center gap-1 animate-pulse">
                              <Flame size={10} className="fill-amber-500 text-amber-500" />
                              <span>ÖNE ÇIKAN</span>
                            </span>
                          )}
                        </div>

                        <h4 className="text-[15px] font-bold text-slate-100 group-hover:text-white transition-colors pt-1 flex items-center gap-1.5 flex-wrap">
                          {proj.title}
                          
                          {proj.isFzbApproved ? (
                            <span className="text-[9px] bg-emerald-950 font-black border border-emerald-500/80 text-emerald-400 font-mono px-2 py-0.5 rounded shadow-[0_0_10px_rgba(16,185,129,0.3)]">
                              ✓ FZB ONAYLI FİZİBİLİTEDİR
                            </span>
                          ) : (
                            <span className="text-[9px] bg-amber-950 font-black border border-amber-600/50 text-amber-305 font-mono px-2 py-0.5 rounded">
                              ⚠️ FİZİBİLİTE İNCELEMEDE (Kilitli)
                            </span>
                          )}

                          {proj.isRetracted && (
                            <span className="text-[9px] bg-rose-950 border border-rose-500 text-rose-300 font-mono px-2 py-0.5 rounded font-black uppercase tracking-wide animate-pulse">
                              🚨 GERİ ÇEKİLDİ / RETRACTED
                            </span>
                          )}
                        </h4>

                        <div className="flex flex-wrap items-center gap-2 mt-1">
                          <p className="text-[10px] text-slate-500 font-mono">
                            Kurucu Tescili: <strong className="text-slate-350 font-sans">{proj.creatorName}</strong> 
                            <span className="mx-1.5">|</span> Tescil ID: <span className="font-mono text-slate-400">{proj.creatorIdentity ? proj.creatorIdentity.substring(0, 4) + '•••' : 'Doğrulandı'}</span>
                            <span className="mx-1.5">|</span> Yayın: {proj.publishDate}
                          </p>

                          {/* ACTION DYNAMISM BADGE METRIC */}
                          <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-900 px-2 py-0.5 rounded text-[8px] font-mono">
                            <span className="text-[#10B981] font-bold uppercase">Eylemsel Dinamizm Skoru:</span>
                            <strong className="text-white bg-slate-900 px-1 rounded">{proj.dynamismScore || 0} Puan</strong>
                            <div className="w-10 h-1.5 bg-slate-900 rounded-full overflow-hidden inline-block align-middle ml-1 border border-slate-950">
                              <div 
                                className="h-full bg-gradient-to-r from-teal-500 to-emerald-400" 
                                style={{ width: `${Math.min(100, (proj.dynamismScore || 0) * 0.8)}%` }}
                              ></div>
                            </div>
                          </div>

                          {proj.vaporwareFlags > 0 && (
                            <div className="text-[8px] bg-rose-900/30 text-rose-450 border border-rose-900/45 px-1.5 py-0.5 rounded font-mono">
                              İhbarsal Hayal/Balon Şüphesi: <strong className="text-rose-400 font-black">{proj.vaporwareFlags} / 3</strong>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Display Dynamic Token Valuation metrics! */}
                      <div className="bg-slate-950 border border-indigo-950 p-2 text-center rounded-lg min-w-[170px] self-start md:self-auto space-y-1 relative">
                        <span className="text-[8px] text-indigo-400 uppercase font-mono block font-black">DİNAMİK VALÜASYON</span>
                        
                        <div className="flex items-center justify-center gap-1.5">
                          <span className="text-sm font-black text-emerald-400 font-mono">%{proj.equityOffer} Pay</span>
                          <span className="text-[10px] text-slate-500 font-mono">/ {proj.valuationMultiplier}x Rasyo</span>
                        </div>

                        <div className="text-[9px] text-slate-300 border-t border-slate-900 pt-1 font-mono">
                          %1 Pay Alım Değeri: <strong className="text-yellow-500">{current1PercentValue} FZB</strong>
                        </div>
                        <p className="text-[8px] text-slate-550 leading-none">Somut kanıtlar onaylandıkça miktar artar</p>
                      </div>
                    </div>

                    {/* Problem Solved & Strategy detail pane */}
                    <div className="bg-slate-950/70 p-3.5 rounded border border-slate-900 text-xs space-y-3">
                      <div>
                        <div className="text-[9px] uppercase tracking-wider text-slate-500 font-mono font-bold mb-0.5">
                          🔴 Saptanan Dikey Sektör Problemi
                        </div>
                        <p className="text-slate-400 leading-relaxed">{proj.problemSolved}</p>
                      </div>

                      <div>
                        <div className="text-[9px] uppercase tracking-wider text-indigo-400 font-mono font-bold mb-0.5 flex items-center gap-1">
                          <Activity size={10} />
                          <span>Fizobia Entegre Çözüm Stratejisi & Optimizasyonu</span>
                        </div>
                        <p className="text-slate-200 leading-relaxed font-sans font-medium italic">
                          "{proj.strategyDescription}"
                        </p>
                      </div>

                      {/* PHYSICAL MATERIAL BLUEPRINT */}
                      <div className="border-t border-slate-900/60 pt-2 bg-slate-950/30">
                        <div className="text-[9px] uppercase tracking-wider text-emerald-400 font-mono font-bold mb-1 flex items-center gap-1">
                          <span>🛠️ TESCİLLİ REEL MATERYAL GEREKSİNİMLERİ (FİZİKSEL ENSTRÜMANTASYON)</span>
                        </div>
                        <p className="text-emerald-300 font-mono text-[10px] bg-[#0E1117] p-2 rounded border border-emerald-950/50">
                          {proj.materialsRequired || "Fiziksel ekipmanı listelenmemiş fantezi."}
                        </p>
                      </div>
                    </div>

                    {/* Crowdfunding progress indicators per league limits */}
                    <div className="space-y-2">
                      <div className="flex justify-between items-end text-xs font-mono">
                        <div>
                          <span className="text-[9px] text-slate-500 block">KULUÇKA DESTEK BAŞARIMI</span>
                          <div className="flex items-center gap-1">
                            <Coins size={12} className="text-yellow-500" />
                            <span className="text-white font-black">{proj.fundingRaised}</span>
                            <span className="text-slate-400">/ {proj.fundingTarget} FZB hedef</span>
                          </div>
                        </div>

                        <div className="text-right">
                          <span className="text-[8px] text-slate-500 block uppercase">LİG LİMİTİ</span>
                          <span className="text-[11px] text-emerald-400 font-bold">Maks {maxLimitFzb} FZB</span>
                        </div>
                      </div>

                      {/* Custom styled progress rail */}
                      <div className="w-full h-2 bg-slate-950 rounded-full overflow-hidden border border-slate-905">
                        <div 
                          className="h-full bg-gradient-to-r from-emerald-500 via-[#10B981] to-indigo-500 transition-all duration-500 rounded-full"
                          style={{ width: `${Math.min(100, Math.round((proj.fundingRaised / maxLimitFzb) * 100))}%` }}
                        ></div>
                      </div>
                    </div>

                    {/* PROOF OF WORK UPDATES LIST (Continuity on actual metrics, photos, simulation outputs) */}
                    <div className="border-t border-slate-900 pt-3.5 space-y-3 text-left">
                      <div className="flex justify-between items-center">
                        <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 font-mono flex items-center gap-1.5">
                          <CheckSquare size={13} className="text-indigo-400" />
                          <span>DOĞRULANMIŞ SOMUT ADIMLAR & SAHA GERİ BİLDİRİMLERİ ({proj.proofOfWorkLogs.length})</span>
                        </span>
                        
                        {isCreatorSelf && (
                          <button
                            onClick={() => setAddProofProjId(proj.id)}
                            className="text-[9px] bg-slate-900 hover:bg-indigo-950 border border-slate-800 text-indigo-400 font-mono px-2 py-0.5 rounded flex items-center gap-1 cursor-pointer transition-colors"
                          >
                            <Plus size={10} />
                            <span>KANIT EKLE / GÜNCELLE</span>
                          </button>
                        )}
                      </div>

                      {/* Add new Proof of work panel form INLINE */}
                      {addProofProjId === proj.id && (
                        <div className="p-3 bg-slate-950 rounded-lg border border-indigo-900/50 space-y-3 shrink-0 anim-fade-in self-start text-xs">
                          <div className="flex justify-between items-center border-b border-indigo-950 pb-1 mb-1">
                            <span className="text-[10px] font-bold text-indigo-400 uppercase font-mono">YENİ GERÇEK DÜNYA KANITI EKLE</span>
                            <button onClick={() => setAddProofProjId(null)} className="text-slate-500 hover:text-white font-mono text-[9px]">KAPAT</button>
                          </div>
                          
                          <form onSubmit={handleAddEvidenceProofOfWork} className="space-y-3 text-left">
                            <div className="space-y-1.5">
                              <label className="text-[8px] text-slate-550 block font-mono">KANIT BAŞLIĞI</label>
                              <input
                                type="text"
                                required
                                placeholder="Örn: 2. Aşama Beta Kimyasal Akış Vana Montajı Test Edildi"
                                value={newProofTitle}
                                onChange={(e) => setNewProofTitle(e.target.value)}
                                className="w-full bg-[#12151C] border border-slate-850 p-1.5 rounded text-white"
                              />
                            </div>

                            <div className="grid grid-cols-2 gap-2">
                              <div>
                                <label className="text-[8px] text-slate-555 block font-mono">ÇIKTI TÜRÜ</label>
                                <select
                                  value={newProofType}
                                  onChange={(e: any) => setNewProofType(e.target.value)}
                                  className="w-full bg-[#12151C] border border-slate-850 p-1 rounded text-white"
                                >
                                  <option value="prototype">Fiziksel Prototip / Düğüm</option>
                                  <option value="simulation">Simülasyon Çıktısı</option>
                                  <option value="media">Fotoğraf veya Video</option>
                                  <option value="test">Bileşen Test Sonucu</option>
                                </select>
                              </div>
                              <div>
                                <label className="text-[8px] text-slate-555 block font-mono">GÖRSEL VEYA LOG DOSYASI URLsi</label>
                                <input
                                  type="text"
                                  placeholder="Öpr: https://images.unsplash..."
                                  value={newProofUrl}
                                  onChange={(e) => setNewProofUrl(e.target.value)}
                                  className="w-full bg-[#12151C] border border-slate-850 p-1 rounded text-white font-mono"
                                />
                              </div>
                            </div>

                            <div className="space-y-1">
                              <label className="text-[8px] text-slate-555 block font-mono">KANIT METRİKLERİ VE DENEY DETAYI (VAAT DEĞİL GERÇEK VERİLER)</label>
                              <textarea
                                required
                                rows={2.5}
                                placeholder="ESP-32 sıcaklık devresi 48 saatlik sürekli akımda yük rezonansı dalgalanmasını %15 altında kaydetti."
                                value={newProofDesc}
                                onChange={(e) => setNewProofDesc(e.target.value)}
                                className="w-full bg-[#12151C] border border-slate-850 p-1 text-slate-200"
                              />
                            </div>

                            <button
                              type="submit"
                              disabled={isSubmittingProof}
                              className="w-full py-1.5 bg-indigo-600 hover:bg-indigo-500 font-bold text-white uppercase tracking-wider font-mono text-[9px] rounded cursor-pointer"
                            >
                              {isSubmittingProof ? "GÖNDERİLİYOR..." : "SAHA KANITINI TÜM EKOSİSTEME YAYINLA"}
                            </button>
                          </form>
                        </div>
                      )}

                      {/* List proof of work updates */}
                      {proj.proofOfWorkLogs.length === 0 ? (
                        <p className="text-[10px] text-slate-500 italic">Henüz bu girişim tarafından somut kanıt sunulmadı. Girişimci 'Kanıt Ekle' aşamasıyla iletebilir.</p>
                      ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {proj.proofOfWorkLogs.map((log) => {
                            const userHasVoted = log.approvedBy.includes(profile.fullName);
                            return (
                              <div key={log.id} className="p-3 bg-slate-950 rounded-lg border border-slate-900 flex flex-col justify-between space-y-2.5">
                                <div className="space-y-1.5 text-left">
                                  <div className="flex items-center justify-between">
                                    <span className="text-[8px] bg-[#12151C] border border-slate-800 text-indigo-400 font-mono px-1.5 py-0.5 rounded uppercase font-bold tracking-wider">
                                      {log.type === "simulation" ? "💻 SİMÜLASYON" : log.type === "prototype" ? "🔧 FİZİKSEL PROTOTİP" : "📁 METRİK LOG"}
                                    </span>
                                    <span className="text-[8px] text-slate-600 font-mono">{log.date}</span>
                                  </div>

                                  <h5 className="text-[11px] font-bold text-slate-200 leading-snug">{log.title}</h5>
                                  
                                  <p className="text-[10px] text-slate-400 font-sans leading-relaxed">
                                    {log.description}
                                  </p>

                                  {log.proofUrl && log.proofUrl.startsWith("http") && (
                                    <div className="w-full h-24 rounded overflow-hidden relative border border-slate-900 group/img">
                                      <img 
                                        src={log.proofUrl} 
                                        alt={log.title}
                                        referrerPolicy="no-referrer"
                                        className="w-full h-full object-cover group-hover/img:scale-105 transition-all duration-300"
                                      />
                                      <div className="absolute inset-0 bg-slate-950/20"></div>
                                    </div>
                                  )}
                                </div>

                                {/* Upvotes / Approved validation controls by investors */}
                                <div className="flex items-center justify-between border-t border-slate-900/60 pt-2 shrink-0">
                                  <span className="text-[8px] font-mono text-slate-500 uppercase">
                                    ✓ Onaylayan Hakem: <strong className="text-emerald-400 font-bold font-mono">{log.votesCount}</strong>
                                  </span>

                                  {profile.role !== "developer" && (
                                    <button
                                      onClick={() => handleApproveProofLog(proj.id, log.id, log.title)}
                                      disabled={userHasVoted}
                                      className={`px-2 py-1 rounded text-[9px] font-black uppercase font-mono tracking-wider transition-colors cursor-pointer flex items-center gap-1 border ${
                                        userHasVoted 
                                          ? "bg-emerald-950/20 border-emerald-900 text-emerald-400 cursor-not-allowed"
                                          : "bg-[#12151C] hover:bg-emerald-600 border-slate-800 hover:text-white"
                                      }`}
                                    >
                                      {userHasVoted ? "KANIT TESCİLLENDİ ✓" : "GERÇEKLİĞİNİ ONAYLA ✓"}
                                    </button>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>

                    {/* Partners / Backers Panel */}
                    <div className="border-t border-slate-900 pt-3 space-y-1.5">
                      <div className="flex justify-between items-center">
                        <span className="text-[9px] uppercase tracking-wider text-slate-500 font-mono">
                          🤝 SÖZLEŞMELİ ORTAKLAR / DESTEKÇİ LİSTESİ ({proj.backersList.length})
                        </span>
                      </div>
                      
                      {proj.backersList.length === 0 ? (
                        <p className="text-[10px] text-slate-500 italic">Henüz bu girişime token desteği gönderilmedi. Doğrulanmış somut adımları görüp ilk ortak siz olabilirsiniz!</p>
                      ) : (
                        <div className="flex flex-wrap gap-1.5">
                          {proj.backersList.map((backer, bIdx) => (
                            <span 
                              key={bIdx}
                              className="text-[10px] font-mono px-2 py-0.5 bg-slate-950 border border-slate-850 rounded text-slate-350 flex items-center gap-1"
                            >
                              <span className="w-1 h-1 bg-emerald-500 rounded-full animate-ping"></span>
                              <strong>{backer.investorName}</strong> : {backer.investedAmount} FZB (%{backer.equityShare} pay)
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                  </div>

                  {/* BOTTOM ACTION BAR */}
                  <div className="bg-slate-950/40 border-t border-slate-850 p-3 flex flex-col sm:flex-row items-center justify-between gap-4">
                    <p className="text-[9px] text-slate-500 leading-snug max-w-lg text-left">
                      🚨 <strong>Hukuki Sözleşmeli Akit:</strong> Bu hak tesciline FZB aktarmak; projenin gerçek dünya somut adımlarına (% oranında) hukuki pay kazandıracaktır. Kimlik numaranız tescil onayı oluşturarak resmi ortaklık hakkına dönüşür.
                    </p>

                    <div className="flex flex-wrap gap-2.5 w-full sm:w-auto self-end sm:self-center shrink-0">
                      
                      {/* EXPERT AUDITOR CONTROLS */}
                      {profile.role !== "developer" && !proj.isRetracted && (
                        <div className="flex gap-1.5 flex-wrap">
                          {!proj.isFzbApproved && (
                            <button
                              onClick={() => handleIssueFzbApproval(proj.id, proj.title)}
                              className="px-2.5 py-1.5 bg-emerald-950/75 hover:bg-emerald-900 text-emerald-400 border border-emerald-800 text-[9px] font-mono font-bold uppercase rounded cursor-pointer transition-colors"
                              title="Tescilli materyal blueprintini onaylayarak projeyi yatırım yapılabilir kılar."
                            >
                              🛡️ FZB Fizibilite Onayla
                            </button>
                          )}
                          <button
                            onClick={() => handleReportVaporwareFlag(proj.id, proj.title)}
                            className="px-2.5 py-1.5 bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 border border-slate-800 hover:text-white text-[9px] font-mono font-bold uppercase rounded cursor-pointer transition-colors"
                            title="Yapay zeka fantezisi barındıran vaat balonu olarak ihbar et."
                          >
                            ⚠️ Balon İhbar Et
                          </button>
                        </div>
                      )}

                      {proj.isRetracted ? (
                        <div className="px-3 py-2 bg-rose-950/40 border border-rose-900 rounded text-rose-300 text-[10px] font-mono font-bold">
                          🚨 GERİ ÇEKİLDİ: {proj.retractionReason || "Bilinmiyor"}
                        </div>
                      ) : activeInvestProjId === proj.id ? (
                        <div className="flex items-center gap-1.5 bg-slate-950 border border-slate-800 p-1 rounded-lg anim-fade-in shrink-0 text-xs">
                          <input
                            type="number"
                            min={10}
                            max={profile.fzbBalance}
                            value={investAmount}
                            onChange={(e) => setInvestAmount(Math.max(10, parseInt(e.target.value) || 0))}
                            className="w-16 bg-[#12151C] border border-slate-800 rounded px-1 py-0.5 text-xs text-white font-mono outline-none"
                          />
                          
                          <button
                            onClick={() => handleInvestProject(proj.id)}
                            disabled={isInvesting || !proj.isFzbApproved}
                            className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed text-white rounded text-[10px] font-black uppercase transition-colors cursor-pointer"
                          >
                            {isInvesting ? "Ödeniyor..." : "GÖNDER"}
                          </button>
                          
                          <button
                            onClick={() => setActiveInvestProjId(null)}
                            className="text-[10px] text-slate-500 hover:text-white px-1 font-mono"
                          >
                            X
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => {
                            if (!proj.isFzbApproved) {
                              alert("Bu projenin FZB uzman fizibilite onayı henüz tamamlanmamıştır. Boş vaat fonlamasını engellemek için yatırım onaya kadar kilitlidir!");
                              return;
                            }
                            setActiveInvestProjId(proj.id);
                            setInvestAmount(Math.min(profile.fzbBalance, 300));
                          }}
                          disabled={!proj.isFzbApproved}
                          className={`w-full sm:w-auto px-4 py-2 text-white text-[10px] font-black uppercase tracking-wider rounded transition-all cursor-pointer shadow-sm flex items-center justify-center gap-1 ${
                            proj.isFzbApproved 
                              ? "bg-gradient-to-r from-emerald-600 to-indigo-600 hover:from-emerald-500 hover:to-indigo-500" 
                              : "bg-slate-900 border border-slate-850 text-slate-505 cursor-not-allowed"
                          }`}
                        >
                          <Coins size={12} />
                          <span>{proj.isFzbApproved ? "YATIRIM YAP / PAY AL" : "FİZİBİLİTE ONAYLANMALI"}</span>
                        </button>
                      )}
                    </div>
                  </div>

                </div>
              );
            })
          )}
        </div>

      </main>

    </div>
  );
}
