import os
from dataclasses import dataclass


@dataclass
class Settings:
    base_url: str
    token: str

    @classmethod
    def from_env(cls):
        base = os.environ.get("BCRM_BASE_URL", "").rstrip("/")
        token = os.environ.get("BCRM_TOKEN", "")
        if not base or not token:
            raise SystemExit("BCRM_BASE_URL and BCRM_TOKEN env vars are required")
        return cls(base_url=base, token=token)
