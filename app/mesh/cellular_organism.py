"""Organizma durumu — hücre + homeostazi + metabolizma + geri besleme."""

from __future__ import annotations

from typing import Any, Dict

from app.mesh.cellular_taxonomy import get_cellular_taxonomy
from app.mesh.feedback import get_brain_feedback
from app.mesh.homeostasis import get_homeostasis_status
from app.mesh.mesh_nervous import get_mesh_nervous_status
from app.mesh.metabolism import get_metabolism_status


def get_cellular_organism_status() -> Dict[str, Any]:
    return {
        "cellular": get_cellular_taxonomy(),
        "homeostasis": get_homeostasis_status(),
        "metabolism": get_metabolism_status(),
        "feedback": get_brain_feedback(),
        "nervous_system": get_mesh_nervous_status(),
    }
