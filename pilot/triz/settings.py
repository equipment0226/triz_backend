"""설정 로더: .env(환경변수) + config/*.yaml 을 하나로 합친다.

우선순위: 환경변수 > config/*.yaml > 코드 기본값
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"

load_dotenv(ROOT / ".env")


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default) or default


def _env_f(key: str, default: float) -> float:
    try:
        return float(os.getenv(key) or default)
    except ValueError:
        return default


def _env_i(key: str, default: int) -> int:
    try:
        return int(os.getenv(key) or default)
    except ValueError:
        return default


class TierConfig:
    def __init__(self, tier: str, default_model: str):
        self.tier = tier
        self.model = _env(f"LLM_MODEL_{tier}", default_model)
        self.api_key = _env(f"LLM_API_KEY_{tier}") or _env("LLM_API_KEY")
        self.base_url = _env(f"LLM_BASE_URL_{tier}") or _env("LLM_BASE_URL", "https://api.deepseek.com/v1")
        self.temperature = _env_f(f"LLM_TEMPERATURE_{tier}", {"T1": 0.1, "T2": 0.3, "T3": 0.7}[tier])
        self.max_tokens = _env_i(f"LLM_MAX_TOKENS_{tier}", {"T1": 2400, "T2": 6500, "T3": 1800}[tier])
        self.json_mode = _env(f"LLM_JSON_MODE_{tier}", "false" if "reason" in self.model.lower() else "true").lower() == "true"
        self.supports_temperature = _env(f"LLM_SUPPORTS_TEMPERATURE_{tier}", "false" if "reason" in self.model.lower() else "true").lower() == "true"
        self.token_parameter = _env(f"LLM_TOKEN_PARAMETER_{tier}", "max_tokens")
        self.cost_in = _env_f(f"COST_IN_PER_M_{tier}", 0.28)
        self.cost_out = _env_f(f"COST_OUT_PER_M_{tier}", 0.42)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Tier {self.tier} model={self.model}>"


class Settings:
    def __init__(self) -> None:
        self.root = ROOT
        self.host = _env("APP_HOST", "127.0.0.1")
        self.port = _env_i("PORT", _env_i("APP_PORT", 8000))
        self.embed_mcp = _env("TRIZ_EMBED_MCP", "false").lower() == "true"
        self.app_token = _env("TRIZ_APP_TOKEN")
        self.require_user_auth = _env("REQUIRE_USER_AUTH", "true" if self.app_token else "false").lower() == "true"
        self.legacy_owner_email = _env("LEGACY_OWNER_EMAIL").strip().lower()
        self.log_level = _env("LOG_LEVEL", "INFO")

        self.db_path = (ROOT / _env("DB_PATH", "./data/triz.db")).resolve()
        self.database_url = _env("DATABASE_URL") or _env("MYSQL_URL")
        if not self.database_url and _env("MYSQLHOST"):
            from sqlalchemy import URL
            self.database_url = URL.create("mysql+pymysql", username=_env("MYSQLUSER"),
                password=_env("MYSQLPASSWORD"), host=_env("MYSQLHOST"),
                port=_env_i("MYSQLPORT", 3306), database=_env("MYSQLDATABASE", "railway"))
        if isinstance(self.database_url, str) and self.database_url.startswith("mysql://"):
            self.database_url = self.database_url.replace("mysql://", "mysql+pymysql://", 1)
        self.orchestrator = _env("ORCHESTRATOR", "local")
        self.n8n_webhook_url = _env("N8N_DISPATCH_URL")
        self.service_token = _env("TRIZ_SERVICE_TOKEN")
        self.mcp_url = _env("TRIZ_MCP_URL", "http://127.0.0.1:8001/mcp")
        self.max_upload_bytes = _env_i("MAX_UPLOAD_MB", 25) * 1024 * 1024
        self.storage_dir = (ROOT / _env("STORAGE_DIR", "./data/storage")).resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.timeout = _env_i("LLM_TIMEOUT_SEC", 180)
        self.max_retries = _env_i("LLM_MAX_RETRIES", 2)
        self.tiers = {
            "T1": TierConfig("T1", "deepseek-chat"),
            "T2": TierConfig("T2", "deepseek-chat"),
            "T3": TierConfig("T3", "deepseek-chat"),
        }

        self.search_provider = _env("SEARCH_PROVIDER", "none").lower()
        self.tavily_key = _env("TAVILY_API_KEY")
        self.patentsview_key = _env("PATENTSVIEW_API_KEY")
        self.free_patent_search = _env("FREE_PATENT_SEARCH", "true").lower() == "true"
        self.patent_search_provider = _env("PATENT_SEARCH_PROVIDER", "vector").lower()
        self.patent_database_url = _env("PATENT_DATABASE_URL")
        if self.patent_database_url.startswith("mysql://"):
            self.patent_database_url = self.patent_database_url.replace("mysql://", "mysql+pymysql://", 1)
        self.qdrant_url = _env("QDRANT_URL")
        self.qdrant_api_key = _env("QDRANT_API_KEY")
        self.patent_collection = _env("PATENT_VECTOR_COLLECTION", "patents_e5_small_v1")
        self.patent_embedding_model = "intfloat/multilingual-e5-small"
        self.patent_embedding_threads = _env_i("PATENT_EMBEDDING_THREADS", 2)
        self.patent_search_timeout = _env_i("PATENT_SEARCH_TIMEOUT_SECONDS", 20)
        self.patent_min_score = _env_f("PATENT_MIN_SCORE", 0.75)
        self.patent_db_max_bytes = _env_i("PATENT_DB_MAX_BYTES", 200_000_000_000)
        self.patent_vector_max_points = _env_i("PATENT_VECTOR_MAX_POINTS", 10_000_000)
        self.bigquery_project_id = _env("BIGQUERY_PROJECT_ID")
        self.bigquery_location = _env("BIGQUERY_LOCATION", "US")
        self.bigquery_credentials_json = _env("GOOGLE_SERVICE_ACCOUNT_JSON")
        self.bigquery_max_bytes = _env_i("BIGQUERY_MAX_BYTES_BILLED", 256 * 1024**3)
        self.bigquery_monthly_bytes = _env_i("BIGQUERY_MONTHLY_BYTE_LIMIT", 768 * 1024**3)
        self.bigquery_timeout = _env_i("BIGQUERY_TIMEOUT_SECONDS", 90)
        self.bigquery_cache_seconds = _env_i("BIGQUERY_CACHE_SECONDS", 86400)
        self.bigquery_ledger_path = self.storage_dir / "bigquery_patents.sqlite3"
        # 키 없이 쓰는 공개 API를 기본 활성화 (tavily/patentsview는 키가 있을 때만 동작)
        self.evidence_providers = [
            p.strip() for p in _env(
                "EVIDENCE_PROVIDERS", "crossref,openalex,arxiv,patentsview,tavily"
            ).split(",") if p.strip()
        ]

        self.triz: dict[str, Any] = self._load_yaml("triz.yaml")
        self.personas: dict[str, Any] = self._load_yaml("personas.yaml")
        self.rubrics: dict[str, Any] = self._load_yaml("rubrics.yaml")
        self._apply_env_overrides()

    # -------------------------------------------------- helpers
    def _load_yaml(self, name: str) -> dict[str, Any]:
        path = CONFIG_DIR / name
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}

    def _apply_env_overrides(self) -> None:
        mapping = {
            "TRIZ_MIN_SOLUTIONS": ("solutions", "min_solutions", int),
            "TRIZ_MAX_SOLUTIONS": ("solutions", "max_solutions", int),
            "TRIZ_DEFAULT_MODE": ("run", "default_mode", str),
            "PIPELINE_PARALLEL_WORKERS": ("run", "parallel_workers", int),
        }
        for env_key, (section, key, cast) in mapping.items():
            raw = os.getenv(env_key)
            if raw:
                self.triz.setdefault(section, {})[key] = cast(raw)

    def cfg(self, path: str, default: Any = None) -> Any:
        """'solutions.min_solutions' 같은 점 표기로 triz.yaml 값을 읽는다."""
        node: Any = self.triz
        for part in path.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def rubric(self, rubric_id: str) -> dict[str, Any] | None:
        rb = self.rubrics.get(rubric_id)
        if not rb:
            return None
        defaults = self.rubrics.get("defaults", {})
        rb = dict(rb)
        rb.setdefault("pass_threshold", defaults.get("pass_threshold", 0.72))
        rb.setdefault("reject_below", defaults.get("reject_below", 0.45))
        rb["id"] = rubric_id
        return rb

    @property
    def llm_ready(self) -> bool:
        return bool(self.tiers["T1"].api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
