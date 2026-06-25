from __future__ import annotations

from datetime import datetime, timezone

from app.api.hub_ui.helpers import esc
from app.config import settings
from app.mesh.proof_vault import StoredProof


def render_proof_share_card(proof: StoredProof, *, base_url: str) -> str:
    created = datetime.fromtimestamp(proof.created_at, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    steps_html = "".join(f"<li>{esc(line)}</li>" for line in proof.steps_summary)
    share_url = f"{base_url.rstrip('/')}/hub/proof/share/{esc(proof.proof_id)}"

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <meta property="og:title" content="OAM Mesh Kanıtı — {esc(proof.proof_id)}"/>
  <meta property="og:description" content="{esc(proof.verdict)}"/>
  <title>Mesh Kanıtı · {esc(proof.proof_id)}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; background: #020204; color: #f8fafc; margin: 0; padding: 2rem; }}
    .card {{ max-width: 640px; margin: 0 auto; border: 1px solid rgba(0,255,163,0.25); border-radius: 20px;
      padding: 1.5rem; background: linear-gradient(145deg, rgba(0,255,163,0.08), #08080f); }}
  h1 {{ font-size: 1.4rem; margin: 0 0 0.5rem; color: #00ffa3; }}
    .verdict {{ font-size: 1.05rem; line-height: 1.6; margin: 1rem 0; }}
    .meta {{ color: #94a3b8; font-size: 0.85rem; }}
    ul {{ padding-left: 1.2rem; color: #cbd5e1; font-size: 0.88rem; line-height: 1.55; }}
    .badge {{ display: inline-block; padding: 0.25rem 0.6rem; border-radius: 999px;
      background: rgba(0,255,163,0.15); color: #00ffa3; font-size: 0.72rem; font-weight: 700; }}
    a {{ color: #00ffa3; }}
  </style>
</head>
<body>
  <div class="card">
    <span class="badge">GERÇEK VERİ · MOCK YOK</span>
    <h1>OAM Mesh Kanıtı</h1>
    <p class="meta">{esc(created)} · {esc(proof.pipeline)} · {proof.total_latency_ms:.0f}ms</p>
    <p class="verdict">{esc(proof.verdict)}</p>
    <ul>{steps_html}</ul>
    <p class="meta">Ödeme: ${proof.paid_usdc:.2f} USDC · Staking: ${proof.staking_usdc:.4f} · Ödeyen: {esc(proof.payer or '—')}</p>
    <p class="meta">ID: <code>{esc(proof.proof_id)}</code></p>
    <p><a href="{share_url}">JSON</a> · <a href="/hub">The Hub</a></p>
  </div>
</body>
</html>"""
