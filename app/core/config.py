from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8', extra="ignore")

    APP_NAME: str = "cursor-2api"
    APP_VERSION: str = "2.0.0"
    DESCRIPTION: str = "一个将 cursor.com 转换为兼容 OpenAI 格式 API 的高性能代理 (Cookie 认证版)。"

    API_MASTER_KEY: Optional[str] = None
    NGINX_PORT: int = 8088
    API_REQUEST_TIMEOUT: int = 180
    
    # 新增 Cookie 配置
    CURSOR_COOKIE: Optional[str] = None

    KNOWN_MODELS: List[str] = [
        "anthropic/claude-sonnet-4.5",
        "openai/gpt-5-nano",
        "google/gemini-2.5-flash"
    ]

settings = Settings()
