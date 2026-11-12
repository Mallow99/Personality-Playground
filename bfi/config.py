"""Settings come from the environment and .env; the character comes from a JSON file."""

import ipaddress
import json
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from bfi.errors import AppError

ROOT = Path(__file__).resolve().parent.parent


class ConfigError(AppError):
    def __init__(self, message):
        super().__init__(message, "config")


class Character(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=60)
    description: str = Field(min_length=1, max_length=300)
    system_prompt: str = Field(min_length=1, max_length=8000)


def load_character(path: Path) -> dict:
    try:
        return Character.model_validate(json.loads(path.read_text(encoding="utf-8"))).model_dump()
    except OSError as exc:
        raise ConfigError(f"Cannot read the character file {path}: {exc.strerror}.") from exc
    except ValueError as exc:  # invalid JSON, or a pydantic ValidationError
        problems = (
            "; ".join(f"{'.'.join(map(str, e['loc'])) or 'file'}: {e['msg']}" for e in exc.errors())
            if isinstance(exc, ValidationError)
            else str(exc)
        )
        raise ConfigError(f"The character file {path} is not valid. {problems}") from exc


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

    def __post_init__(self):
        if self.backend not in {"mock", "openai"}:
            raise ConfigError("BFI_BACKEND must be mock or openai.")
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
            raise ConfigError(
                "BFI_BASE_URL must be a loopback HTTP(S) URL without credentials or query."
            )
        if not self.model.strip() or len(self.model) > 300:
            raise ConfigError("BFI_MODEL must contain 1–300 characters.")
        if not 1 <= self.timeout <= 600 or not 1 <= self.max_tokens <= 8192:
            raise ConfigError(
                "BFI_TIMEOUT_SECONDS must be 1–600 and BFI_MAX_TOKENS must be 1–8192."
            )
        if not 1 <= self.history_pairs <= 100 or not 1000 <= self.context_chars <= 200000:
            raise ConfigError(
                "BFI_HISTORY_PAIRS must be 1–100 and BFI_CONTEXT_CHARS must be 1000–200000."
            )

    @classmethod
    def from_env(cls):
        def path(name, default):
            value = Path(os.getenv(name, default))
            return value if value.is_absolute() else ROOT / value

        def number(name, default, kind):
            raw = os.getenv(name, default)
            try:
                return kind(raw)
            except ValueError as exc:
                raise ConfigError(f"{name} must be a number, not {raw!r}.") from exc

        return cls(
            backend=os.getenv("BFI_BACKEND", "mock"),
            base_url=os.getenv("BFI_BASE_URL", "http://127.0.0.1:8080/v1").rstrip("/"),
            model=os.getenv("BFI_MODEL", "local-model"),
            api_key=os.getenv("BFI_API_KEY", ""),
            timeout=number("BFI_TIMEOUT_SECONDS", "120", float),
            max_tokens=number("BFI_MAX_TOKENS", "512", int),
            history_pairs=number("BFI_HISTORY_PAIRS", "12", int),
            context_chars=number("BFI_CONTEXT_CHARS", "24000", int),
            data_dir=path("BFI_DATA_DIR", "data"),
            character_file=path("BFI_CHARACTER_FILE", "config/character.json"),
        )

    @property
    def identity(self):
        """What a conversation is tied to. A chat cannot continue on a different identity."""
        return {
            "backend": self.backend,
            "endpoint": self.base_url if self.backend != "mock" else None,
            "requested_model": self.model if self.backend != "mock" else "mock-script-v1",
        }
