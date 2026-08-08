import os
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    bot_token: str = Field(..., validation_alias="TELEGRAM_BOT_TOKEN")
    gemini_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY")
    database_url: str = Field(default="sqlite+aiosqlite:///./bot.db", validation_alias="DATABASE_URL")
    admin_ids_raw: Union[str, int, List[int]] = Field(default="7306854093", validation_alias="ADMIN_IDS")
    default_model: str = Field(default="claude", validation_alias="DEFAULT_MODEL")
    default_system_prompt: str = Field(
        default=(
            "Siz Telegram Business shaxsiy yordamchisisiz.\n"
            "QOIDALAR:\n"
            "1. Har qanday vaziyatda FAQAT va FAQAT O'zbek tilida javob bering.\n"
            "2. Hech qachon Anthropic, Claude, OpenAI yoki AI model/bot haqida gapirmang.\n"
            "3. O'zingizni shunchaki ushbu akkaunt egasining shaxsiy yordamchisi deb biling.\n"
            "4. HAR XABARDA SALOM BERMANG — faqat kun davomidagi birinchi murojaatga bitta qisqa salom bilan boshlashingiz mumkin.\n"
            "5. Javoblar batafsil, aniq va foydali bo'lsin. Bir xil so'zlarni takrorlamang. Xuddi odam yozayotgandek tabiiy bo'lsin.\n"
            "6. Javoblarda ** (bold markdown) va keraksiz murakkab iboralarni ishlatmang."
        ),
        validation_alias="DEFAULT_SYSTEM_PROMPT"
    )
    rate_limit_seconds: float = Field(default=1.5, validation_alias="RATE_LIMIT_SECONDS")
    max_history_length: int = Field(default=20, validation_alias="MAX_HISTORY_LENGTH")
    port: int = Field(default=3000, validation_alias="PORT")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    @property
    def admin_ids(self) -> List[int]:
        if isinstance(self.admin_ids_raw, list):
            return [int(x) for x in self.admin_ids_raw]
        if isinstance(self.admin_ids_raw, int):
            return [self.admin_ids_raw]
        if isinstance(self.admin_ids_raw, str):
            parts = [p.strip() for p in self.admin_ids_raw.split(",") if p.strip()]
            res = []
            for p in parts:
                try:
                    res.append(int(p))
                except ValueError:
                    pass
            return res or [7306854093]
        return [7306854093]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
