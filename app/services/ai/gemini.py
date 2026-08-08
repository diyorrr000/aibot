import asyncio
import logging
from typing import List, Any, Optional
from google import genai
from google.genai import types
from app.config.settings import settings
from app.services.ai.base import BaseAIProvider
from app.utils.helpers import clean_ai_markdown

logger = logging.getLogger(__name__)

class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self._client = None

    def get_client(self):
        key = self.api_key or settings.gemini_api_key
        if not key:
            return None
        if not self._client:
            self._client = genai.Client(api_key=key)
        return self._client

    async def generate_response(
        self,
        contents: List[Any],
        system_prompt: Optional[str] = None,
        timeout: float = 25.0,
        retries: int = 2,
    ) -> str:
        client = self.get_client()
        if not client:
            raise ValueError("GEMINI_API_KEY is not configured.")

        prompt_system = system_prompt or settings.default_system_prompt
        config = types.GenerateContentConfig(
            system_instruction=(
                f"{prompt_system}\n"
                "CRITICAL SYSTEM RULES:\n"
                "1. You must write and respond exclusively in the Uzbek language.\n"
                "2. NEVER use bold markdown formatting (do NOT use **).\n"
                "3. Code blocks must use standard triple backticks.\n"
                "4. NEVER state or reveal that you are Google, Gemini, OpenAI, Claude, AI, LLM, or a bot. You are ALWAYS strictly the personal assistant of the Telegram account owner.\n"
                "5. Understand user intent fully regardless of slang, typos, or input type. Provide rich, highly helpful, comprehensive explanations so the user gets complete answers."
            )
        )

        models_to_try = ["gemini-2.5-flash-lite", "gemini-2.5-flash"]
        last_error = None

        for model in models_to_try:
            delay = 1.0
            for attempt in range(retries):
                try:
                    logger.info(f"Gemini API calling model '{model}' (attempt {attempt+1}/{retries})...")
                    response = await asyncio.wait_for(
                        client.aio.models.generate_content(
                            model=model,
                            contents=contents,
                            config=config
                        ),
                        timeout=timeout
                    )
                    text = response.text
                    if not text:
                        raise ValueError(f"Empty response from Gemini API model {model}.")
                    return clean_ai_markdown(text)
                except Exception as e:
                    last_error = e
                    logger.warning(f"Gemini API model '{model}' attempt {attempt+1}/{retries} failed: {e}")
                    await asyncio.sleep(delay)
                    delay *= 1.5

        raise Exception(f"Gemini API error across all models: {last_error}")

