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
    def __init__(self, api_key: str = settings.gemini_api_key):
        self.api_key = api_key
        self._client = None

    def get_client(self):
        if not self._client and self.api_key:
            self._client = genai.Client(api_key=self.api_key)
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
        thinking_config = types.ThinkingConfig(thinking_budget=0)

        config = types.GenerateContentConfig(
            thinking_config=thinking_config,
            system_instruction=(
                f"{prompt_system}\n"
                "CRITICAL INSTRUCTIONS:\n"
                "1. You must write and respond exclusively in the Uzbek language.\n"
                "2. In your responses, NEVER use bold markdown formatting (do NOT use **).\n"
                "3. Code blocks must use standard triple backticks."
            )
        )

        delay = 1.0
        last_error = None
        for attempt in range(retries):
            try:
                response = await asyncio.wait_for(
                    client.aio.models.generate_content(
                        model=settings.default_model or "gemini-2.5-flash-lite",
                        contents=contents,
                        config=config
                    ),
                    timeout=timeout
                )
                text = response.text
                if not text:
                    raise ValueError("Empty response from Gemini API.")
                return clean_ai_markdown(text)
            except Exception as e:
                last_error = e
                logger.warning(f"Gemini API attempt {attempt+1}/{retries} failed: {e}")
                await asyncio.sleep(delay)
                delay *= 1.5

        raise Exception(f"Gemini API error: {last_error}")
