from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class OAMSettings:
    registry_backend: str
    redis_url: str

    @classmethod
    def from_env(cls) -> OAMSettings:
        return cls(
            registry_backend=os.getenv("OAM_REGISTRY_BACKEND", "memory").lower(),
            redis_url=os.getenv("OAM_REDIS_URL", "redis://localhost:6379/0"),
        )


settings = OAMSettings.from_env()
