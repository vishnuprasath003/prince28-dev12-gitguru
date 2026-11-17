import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    app_name: str = "GitGuru"
    debug: bool = False
    api_prefix: str = "/v1"

    @property
    def project_root(self):
        return Path(__file__).resolve().parents[3]

    @property
    def data_file(self):
        return self.project_root / "data" / "sample_records.json"


def get_settings():
    return Settings(
        app_name=os.getenv("APP_NAME", "GitGuru"),
        debug=os.getenv("DEBUG", "false").lower() == "true",
        api_prefix=os.getenv("API_PREFIX", "/v1"),
    )
