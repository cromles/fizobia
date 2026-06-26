"""Dikey uzmanlık departmanları — mikro işçi hücreleri ve yatırım kategorileri."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.mesh.critic import CRITIC_AGENT_ID
from app.mesh.proof_pipeline import MESH_PROOF_AGENTS
from app.workers.media_brand import AGENT_ID as BRAND_ID
from app.workers.media_outreach import AGENT_ID as OUTREACH_ID
from app.workers.media_proof import AGENT_ID as PROOF_MEDIA_ID
from app.workers.media_render import AGENT_ID as RENDER_ID
from app.workers.media_story import AGENT_ID as STORY_ID
from app.workers.text_competitors import ARENA_TEXT_COMPETITORS
from app.workers.web_crawler import AGENT_ID as WEB_CRAWLER_ID

DEPARTMENT_MEDIA_VIDEO = "media_video"
DEPARTMENT_COPYWRITING = "copywriting"
DEPARTMENT_TECHNICAL = "technical"

ARTICLE_PIPELINE_AGENTS: Tuple[str, ...] = (
    WEB_CRAWLER_ID,
    STORY_ID,
    BRAND_ID,
    CRITIC_AGENT_ID,
)


@dataclass(frozen=True)
class DepartmentSpec:
    code: str
    label_tr: str
    label_short: str
    description: str
    invest_hint: str
    pipeline_ids: Tuple[str, ...]
    agent_ids: Tuple[str, ...]

    def to_public(self, *, registered_ids: Optional[Sequence[str]] = None) -> Dict[str, Any]:
        reg = set(registered_ids or [])
        eligible = [aid for aid in self.agent_ids if not reg or aid in reg]
        return {
            "code": self.code,
            "label_tr": self.label_tr,
            "label_short": self.label_short,
            "description": self.description,
            "invest_hint": self.invest_hint,
            "pipeline_ids": list(self.pipeline_ids),
            "agent_ids": list(self.agent_ids),
            "agent_count": len(self.agent_ids),
            "registered_count": len(eligible),
            "article_chain": list(ARTICLE_PIPELINE_AGENTS) if self.code == DEPARTMENT_COPYWRITING else [],
        }


DEPARTMENTS: Dict[str, DepartmentSpec] = {
    DEPARTMENT_MEDIA_VIDEO: DepartmentSpec(
        code=DEPARTMENT_MEDIA_VIDEO,
        label_tr="Medya ve İçerik Üretimi",
        label_short="Edit / Video",
        description="Görsel estetik, video kurgu şemaları, render ve montaj — sadece bu işçi hücreleri.",
        invest_hint="Video Edit Ajanları havuzuna yatırım",
        pipeline_ids=("arena",),
        agent_ids=ARENA_TEXT_COMPETITORS + (RENDER_ID, OUTREACH_ID, PROOF_MEDIA_ID),
    ),
    DEPARTMENT_COPYWRITING: DepartmentSpec(
        code=DEPARTMENT_COPYWRITING,
        label_tr="Yazılı Basın ve Metin",
        label_short="Makale / Copywriting",
        description="SEO, dil bilgisi, kanca cümleleri, hikaye anlatımı ve metin mimarisi.",
        invest_hint="Makale ve metin ajanlarına yatırım",
        pipeline_ids=("article",),
        agent_ids=ARTICLE_PIPELINE_AGENTS,
    ),
    DEPARTMENT_TECHNICAL: DepartmentSpec(
        code=DEPARTMENT_TECHNICAL,
        label_tr="Teknik Tasarım ve Analiz",
        label_short="Kod / Mimari",
        description="Kod blokları, veri tabanı şemaları ve teknik sistem mimarisi analizi.",
        invest_hint="Teknik Analiz Ajanları havuzuna yatırım",
        pipeline_ids=("mesh_proof", "ecosystem_assembly"),
        agent_ids=MESH_PROOF_AGENTS,
    ),
}

# Bir ajan birden fazla departmanda görev alabilir (ör. Crawler hem teknik hem makale zincirinde).
AGENT_DEPARTMENTS: Dict[str, Tuple[str, ...]] = {
    WEB_CRAWLER_ID: (DEPARTMENT_TECHNICAL, DEPARTMENT_COPYWRITING),
    STORY_ID: (DEPARTMENT_COPYWRITING, DEPARTMENT_MEDIA_VIDEO),
    BRAND_ID: (DEPARTMENT_COPYWRITING, DEPARTMENT_MEDIA_VIDEO),
    CRITIC_AGENT_ID: (DEPARTMENT_COPYWRITING, DEPARTMENT_MEDIA_VIDEO),
    RENDER_ID: (DEPARTMENT_MEDIA_VIDEO,),
    OUTREACH_ID: (DEPARTMENT_MEDIA_VIDEO,),
    PROOF_MEDIA_ID: (DEPARTMENT_MEDIA_VIDEO,),
}
for aid in ARENA_TEXT_COMPETITORS:
    AGENT_DEPARTMENTS.setdefault(aid, (DEPARTMENT_MEDIA_VIDEO,))
for aid in MESH_PROOF_AGENTS:
    AGENT_DEPARTMENTS.setdefault(aid, (DEPARTMENT_TECHNICAL,))


def primary_department(agent_id: str) -> str:
    """Yatırım filtresi için birincil departman."""
    depts = AGENT_DEPARTMENTS.get(agent_id)
    if depts:
        return depts[0]
    return DEPARTMENT_TECHNICAL


def departments_for_agent(agent_id: str) -> Tuple[str, ...]:
    return AGENT_DEPARTMENTS.get(agent_id, (DEPARTMENT_TECHNICAL,))


def agents_in_department(department_code: str) -> Tuple[str, ...]:
    spec = DEPARTMENTS.get(department_code)
    return spec.agent_ids if spec else ()


def list_departments(*, registered_agent_ids: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    reg = list(registered_agent_ids or [])
    items = [spec.to_public(registered_ids=reg) for spec in DEPARTMENTS.values()]
    items.sort(key=lambda d: d["code"])
    return {
        "philosophy": "Tek genel model yok — her departman kendi mikro işçi hücreleriyle çalışır.",
        "departments": items,
        "count": len(items),
        "article_pipeline": {
            "pipeline": "article",
            "agents": list(ARTICLE_PIPELINE_AGENTS),
            "steps": [
                {"order": 1, "role": "Araştırmacı", "agent_id": WEB_CRAWLER_ID},
                {"order": 2, "role": "Taslakçı", "agent_id": STORY_ID},
                {"order": 3, "role": "Editör", "agent_id": BRAND_ID},
                {"order": 4, "role": "Denetçi", "agent_id": CRITIC_AGENT_ID},
            ],
        },
    }
