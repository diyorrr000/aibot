import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    bot_token: str = Field(..., validation_alias="TELEGRAM_BOT_TOKEN")
    openai_api_key: str = Field(..., validation_alias="OPENAI_API_KEY")
    database_url: str = Field(
        default="sqlite+aiosqlite:///./bot.db", 
        validation_alias="DATABASE_URL"
    )
    default_model: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")
    default_system_prompt: str = Field(
        default=(
            "Siz Telegram Business yordamchisisiz. Mijozlar bilan muloyim, "
            "do'stona va professional tarzda gaplashing. Javoblaringizni o'zbek tilida, "
            "tushunarli va chiroyli formatda taqdim eting."
        ),
        validation_alias="DEFAULT_SYSTEM_PROMPT"
    )
    rate_limit_seconds: float = Field(default=1.5, validation_alias="RATE_LIMIT_SECONDS")
    max_history_length: int = Field(default=20, validation_alias="MAX_HISTORY_LENGTH")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
