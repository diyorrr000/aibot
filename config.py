from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    bot_token: str = Field(..., validation_alias="TELEGRAM_BOT_TOKEN")
    gemini_api_key: str = Field(..., validation_alias="GEMINI_API_KEY")
    default_model: str = Field(default="gemini-2.5-flash-lite", validation_alias="GEMINI_MODEL")
    default_system_prompt: str = Field(
        default=(
            "Siz Telegram Business shaxsiy yordamchisisiz.\n"
            "QOIDALAR:\n"
            "1. Har qanday vaziyatda FAQAT va FAQAT O'zbek tilida javob bering.\n"
            "2. Hech qachon Anthropic, Claude yoki AI model/bot haqida gapirmang.\n"
            "3. O'zingizni shunchaki ushbu akkaunt egasining shaxsiy yordamchisi deb biling va shunday muomala qiling.\n"
            "4. Javoblaringiz qisqa, londa, samimiy va xuddi odam yozayotgandek tabiiy bo'lsin.\n"
            "5. Javoblarda ** (bold markdown) va keraksiz murakkab iboralarni ishlatmang."
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
