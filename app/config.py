import os
import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Settings:
    app_name: str = "office-agent"
    app_env: str = "local"
    host: str = "127.0.0.1"
    port: int = 8000

    # DingTalk Open Platform API
    dingtalk_app_key: str | None = None
    dingtalk_app_secret: str | None = None
    dingtalk_api_base_url: str = "https://api.dingtalk.com"

    database_path: str = "data/office_agent.db"
    public_base_url: str = ""

    # MCP server deployment configuration. stdio is best for same-host tools;
    # streamable-http/sse is better when other tools call this server remotely.
    mcp_transport: str = "stdio"
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8010
    mcp_streamable_http_path: str = "/mcp"
    mcp_sse_path: str = "/sse"
    mcp_message_path: str = "/messages/"
    mcp_stateless_http: bool = False
    # Agent brain mode: enable/disable autonomous agent with planning and memory
    enable_agent_brain: bool = False
    
    # LLM configuration for agent brain
    llm_api_key: str | None = None
    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-chat"
    
    # Email SMTP configuration
    smtp_host: str | None = None
    smtp_port: int = 465
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_timeout: int = 30
    smtp_use_tls: bool = True
    smtp_use_starttls: bool = False
    max_file_size_mb: int = 20
    allow_external_input_files: bool = False
    upload_dir: str = "data/files"
    gotenberg_url: str | None = None
    gotenberg_timeout: int = 120
    office_agent_font_dir: str = "/usr/local/share/fonts/office-agent"
    office_agent_docx_font: str = "Noto Serif CJK SC"
    notice_channels: dict[str, dict[str, Any]] | None = None

    @property
    def resolved_database_path(self) -> Path:
        path = Path(self.database_path)
        if path.is_absolute():
            return path
        return PROJECT_ROOT / path

    @property
    def is_email_configured(self) -> bool:
        """Check if SMTP is properly configured."""
        return bool(self.smtp_host and self.smtp_username and self.smtp_password)

    @property
    def is_dingtalk_configured(self) -> bool:
        """Check if DingTalk API is properly configured."""
        return bool(self.dingtalk_app_key and self.dingtalk_app_secret)

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @property
    def resolved_upload_dir(self) -> Path:
        path = Path(self.upload_dir)
        if path.is_absolute():
            return path
        return PROJECT_ROOT / path

    @property
    def configured_notice_channels(self) -> dict[str, dict[str, Any]]:
        return self.notice_channels or {}


@lru_cache
def get_settings() -> Settings:
    _load_dotenv(PROJECT_ROOT / ".env")
    return Settings(
        app_name=os.getenv("APP_NAME", "office-agent"),
        app_env=os.getenv("APP_ENV", "local"),
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
        dingtalk_app_key=os.getenv("DINGTALK_APP_KEY") or None,
        dingtalk_app_secret=os.getenv("DINGTALK_APP_SECRET") or None,
        dingtalk_api_base_url=os.getenv("DINGTALK_API_BASE_URL", "https://api.dingtalk.com"),
        database_path=os.getenv("DATABASE_PATH", "data/office_agent.db"),
        public_base_url=os.getenv("PUBLIC_BASE_URL", ""),
        mcp_transport=os.getenv("MCP_TRANSPORT", "stdio"),
        mcp_host=os.getenv("MCP_HOST", "127.0.0.1"),
        mcp_port=int(os.getenv("MCP_PORT", "8010")),
        mcp_streamable_http_path=os.getenv("MCP_STREAMABLE_HTTP_PATH", "/mcp"),
        mcp_sse_path=os.getenv("MCP_SSE_PATH", "/sse"),
        mcp_message_path=os.getenv("MCP_MESSAGE_PATH", "/messages/"),
        mcp_stateless_http=os.getenv("MCP_STATELESS_HTTP", "false").lower() == "true",
        enable_agent_brain=os.getenv("ENABLE_AGENT_BRAIN", "false").lower() == "true",
        llm_api_key=os.getenv("DEEPSEEK_API_KEY") or os.getenv("LLM_API_KEY"),
        llm_base_url=os.getenv("DEEPSEEK_BASE_URL") or os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
        llm_model=os.getenv("DEEPSEEK_MODEL") or os.getenv("LLM_MODEL", "deepseek-chat"),
        smtp_host=os.getenv("SMTP_HOST") or None,
        smtp_port=int(os.getenv("SMTP_PORT", "465")),
        smtp_username=os.getenv("SMTP_USERNAME") or None,
        smtp_password=os.getenv("SMTP_PASSWORD") or None,
        smtp_timeout=int(os.getenv("SMTP_TIMEOUT", "30")),
        smtp_use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
        smtp_use_starttls=os.getenv("SMTP_USE_STARTTLS", "false").lower() == "true",
        max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "20")),
        allow_external_input_files=os.getenv("ALLOW_EXTERNAL_INPUT_FILES", "false").lower() == "true",
        upload_dir=os.getenv("UPLOAD_DIR", "data/files"),
        gotenberg_url=os.getenv("GOTENBERG_URL") or None,
        gotenberg_timeout=int(os.getenv("GOTENBERG_TIMEOUT", "120")),
        office_agent_font_dir=os.getenv("OFFICE_AGENT_FONT_DIR", "/usr/local/share/fonts/office-agent"),
        office_agent_docx_font=os.getenv("OFFICE_AGENT_DOCX_FONT", "Noto Serif CJK SC"),
        notice_channels=_load_notice_channels(os.getenv("NOTICE_CHANNELS", "")),
    )


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _load_notice_channels(raw: str) -> dict[str, dict[str, Any]]:
    if not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error("Invalid NOTICE_CHANNELS JSON: %s", exc)
        raise ValueError(f"Invalid NOTICE_CHANNELS JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("NOTICE_CHANNELS must be a JSON object")
    channels: dict[str, dict[str, Any]] = {}
    for channel_id, config in parsed.items():
        if isinstance(channel_id, str) and isinstance(config, dict):
            channels[channel_id] = config
        else:
            raise ValueError("NOTICE_CHANNELS entries must be object values keyed by channel_id")
    return channels
