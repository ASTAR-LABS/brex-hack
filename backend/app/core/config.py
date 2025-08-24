from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # API Settings
    app_name: str = "Agent Jam Voice Assistant"
    app_version: str = "1.0.0"
    api_v1_str: str = "/api/v1"

    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True

    # Azure OpenAI Settings
    azure_openai_api_key: Optional[str] = os.getenv("AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: Optional[str] = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
    azure_openai_deployment_name: str = os.getenv(
        "AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4"
    )

    # Whisper Settings
    whisper_model_size: str = "small"  # Upgraded from "base" for better accuracy
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"

    # Audio Processing Settings
    audio_sample_rate: int = 16000
    audio_chunk_duration_ms: int = 30
    audio_buffer_duration_ms: int = 3500  # Increased from 1500ms for better context
    vad_aggressiveness: int = 1  # Reduced from 2 - less aggressive filtering
    vad_enabled: bool = True  # Enable VAD to filter out non-speech audio

    # Session Settings
    session_timeout_minutes: int = 30
    session_persistence_minutes: int = 10  # Keep paused sessions for 10 minutes

    # Cerebras Settings
    cerebras_api_key: Optional[str] = os.getenv("CEREBRAS_API_KEY")
    cerebras_model: str = "gpt-oss-120b"
    cerebras_temperature: float = 0.7
    cerebras_max_tokens: int = 1024

    # GitHub Integration
    github_token: Optional[str] = os.getenv("GITHUB_TOKEN")
    github_owner: Optional[str] = os.getenv("GITHUB_OWNER")
    github_repo: Optional[str] = os.getenv("GITHUB_REPO")

    # Agentic Mode
    use_agentic_mode: bool = os.getenv("USE_AGENTIC_MODE", "false").lower() == "true"

    # MCP Server Configuration
    # GitHub MCP
    enable_github_mcp: bool = os.getenv("ENABLE_GITHUB_MCP", "false").lower() == "true"

    # Google Calendar MCP
    enable_google_calendar_mcp: bool = (
        os.getenv("ENABLE_GOOGLE_CALENDAR_MCP", "false").lower() == "true"
    )
    google_client_id: Optional[str] = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = os.getenv("GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = os.getenv(
        "GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback"
    )

    # Slack MCP
    enable_slack_mcp: bool = os.getenv("ENABLE_SLACK_MCP", "false").lower() == "true"
    # slack_bot_token: Optional[str] = os.getenv("SLACK_BOT_TOKEN")
    # slack_app_token: Optional[str] = os.getenv("SLACK_APP_TOKEN")
    # slack_default_channel: str = os.getenv("SLACK_DEFAULT_CHANNEL", "general")
    slack_mcp_xoxc_token: Optional[str] = os.getenv("SLACK_MCP_XOXC_TOKEN")
    slack_mcp_xoxd_token: Optional[str] = os.getenv("SLACK_MCP_XOXD_TOKEN")
    slack_default_channel: str = os.getenv("SLACK_DEFAULT_CHANNEL", "general")

    # Other MCPs (for future use)
    enable_filesystem_mcp: bool = (
        os.getenv("ENABLE_FILESYSTEM_MCP", "false").lower() == "true"
    )
    filesystem_root: str = os.getenv("FILESYSTEM_ROOT", "/tmp")

    enable_postgres_mcp: bool = (
        os.getenv("ENABLE_POSTGRES_MCP", "false").lower() == "true"
    )
    postgres_connection_string: Optional[str] = os.getenv("POSTGRES_CONNECTION_STRING")

    enable_notion_mcp: bool = os.getenv("ENABLE_NOTION_MCP", "false").lower() == "true"
    notion_api_key: Optional[str] = os.getenv("NOTION_API_KEY")

    enable_google_drive_mcp: bool = (
        os.getenv("ENABLE_GOOGLE_DRIVE_MCP", "false").lower() == "true"
    )

    enable_linear_mcp: bool = os.getenv("ENABLE_LINEAR_MCP", "false").lower() == "true"
    linear_api_key: Optional[str] = os.getenv("LINEAR_API_KEY")

    enable_jira_mcp: bool = os.getenv("ENABLE_JIRA_MCP", "false").lower() == "true"
    jira_url: Optional[str] = os.getenv("JIRA_URL")
    jira_email: Optional[str] = os.getenv("JIRA_EMAIL")
    jira_api_token: Optional[str] = os.getenv("JIRA_API_TOKEN")

    # CORS Settings
    cors_origins: list = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list = ["*"]
    cors_allow_headers: list = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields for flexibility


settings = Settings()
