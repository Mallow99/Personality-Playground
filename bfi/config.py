"""Configuration lives on the server; credentials never enter the browser."""

import ipaddress
import os
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field

ROOT = Path(__file__).resolve().parent.parent


class Character(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=60)
    description: str = Field(min_length=1, max_length=300)
    system_prompt: str = Field(min_length=1, max_length=8000)
    profile_id: str = "companion"
    theme: Literal["foundation", "academic", "engineering", "business"] = "foundation"


@dataclass(frozen=True)
class Settings:
    backend: str = "mock"
    base_url: str = "http://127.0.0.1:8080/v1"
    model: str = "local-model"
    api_key: str = ""
    timeout: float = 120
    max_tokens: int = 512
    history_pairs: int = 12
    context_chars: int = 24000
    data_dir: Path = ROOT / "data"
    character_file: Path = ROOT / "config/character.json"
    profiles_file: Path = ROOT / "config/profiles.json"
    project_root: Path | None = None
    search_api_key: str = ""
    adapter_label: str = ""

    def __post_init__(self):
        if self.backend not in {"mock", "openai"}:
            raise ValueError("BFI_BACKEND must be mock or openai.")
        url = urlsplit(self.base_url)
        try:
            _ = url.port
            loopback = url.hostname == "localhost" or ipaddress.ip_address(url.hostname).is_loopback
        except ValueError:
            loopback = False
        if (
            url.scheme not in {"http", "https"}
            or not loopback
            or url.username
            or url.password
            or url.query
            or url.fragment
        ):
            raise ValueError(
                "BFI_BASE_URL must be a loopback HTTP(S) URL without credentials or query."
            )
        if not self.model.strip() or len(self.model) > 300:
            raise ValueError("BFI_MODEL must contain 1–300 characters.")
        if not 1 <= self.timeout <= 600 or not 1 <= self.max_tokens <= 8192:
            raise ValueError("Timeout must be 1–600 seconds; max tokens must be 1–8192.")
        if not 1 <= self.history_pairs <= 100 or not 1000 <= self.context_chars <= 200000:
            raise ValueError("History pairs must be 1–100; context chars must be 1000–200000.")

    @classmethod
    def from_env(cls):
        def path(name, default):
            value = Path(os.getenv(name, default))
            return value if value.is_absolute() else ROOT / value

        return cls(
            backend=os.getenv("BFI_BACKEND", "mock"),
            base_url=os.getenv("BFI_BASE_URL", "http://127.0.0.1:8080/v1").rstrip("/"),
            model=os.getenv("BFI_MODEL", "local-model"),
            api_key=os.getenv("BFI_API_KEY", ""),
            timeout=float(os.getenv("BFI_TIMEOUT_SECONDS", "120")),
            max_tokens=int(os.getenv("BFI_MAX_TOKENS", "512")),
            history_pairs=int(os.getenv("BFI_HISTORY_PAIRS", "12")),
            context_chars=int(os.getenv("BFI_CONTEXT_CHARS", "24000")),
            data_dir=path("BFI_DATA_DIR", "data"),
            character_file=path("BFI_CHARACTER_FILE", "config/character.json"),
            profiles_file=path("BFI_PROFILES_FILE", "config/profiles.json"),
            project_root=path("BFI_PROJECT_ROOT", ".") if os.getenv("BFI_PROJECT_ROOT") else None,
            search_api_key=os.getenv("BFI_BRAVE_API_KEY", ""),
            adapter_label=os.getenv("BFI_ADAPTER_LABEL", ""),
        )

    def for_profile(self, profile_id):
        """Each profile may use its own local server/model; omitted values inherit defaults."""
        prefix = f"BFI_{profile_id.upper()}_"
        return replace(
            self,
            backend=os.getenv(prefix + "BACKEND", self.backend),
            base_url=os.getenv(prefix + "BASE_URL", self.base_url).rstrip("/"),
            model=os.getenv(prefix + "MODEL", self.model),
            api_key=os.getenv(prefix + "API_KEY", self.api_key),
            adapter_label=os.getenv(prefix + "ADAPTER_LABEL", self.adapter_label),
        )

    @property
    def identity(self):
        identity = {
            "backend": self.backend,
            "endpoint": self.base_url if self.backend != "mock" else None,
            "requested_model": self.model if self.backend != "mock" else "mock-script-v1",
        }
        if self.adapter_label:
            identity["configured_adapter"] = self.adapter_label
        return identity
