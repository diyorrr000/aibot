from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    bot_token: str = Field(..., validation_alias="TELEGRAM_BOT_TOKEN")
    gemini_api_key: str = Field(..., validation_alias="GEMINI_API_KEY")
    default_model: str = Field(default="gemini-2.5-flash-lite", validation_alias="GEMINI_MODEL")
    default_system_prompt: str = Field(
        default=(
            "Siz SecureXXX xizmatkorisiz va Telegram Business yordamchisisiz. "
            "Mijozlar bergan savollarga har doim to'liq o'zbek tilida, qisqa, aniq va londa javob bering. "
            "O'zingiz haqida so'ralganda yoki muloqot davomida 'SecureXXX xizmatkoriman' deb ayting. "
            "Javoblaringizda HECH QACHON qalin shrift (bold markdown **) ishlatmang. "
            "Fikrlar va axborotlarni yangi satrlar va ro'yxat tartibida yozing."
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
