import asyncio
import logging
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from config import settings

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self, api_key: str = settings.gemini_api_key):
        self.ai_client = genai.Client(api_key=api_key)

    async def generate_response(
        self,
        contents: List[Any],
        system_prompt: Optional[str] = None,
        model: str = "gemini-2.5-flash-lite",
        retries: int = 3,
        delay: float = 1.0
    ) -> str:
        """
        Generate content using Google Gemini API (gemini-2.5-flash-lite).
        Supports text, photo, audio (voice), and document inputs.
        """
        prompt_system = system_prompt or settings.default_system_prompt
        
        # Thinking config for Gemini 2.5 models
        thinking_config = types.ThinkingConfig(thinking_budget=0)

        config = types.GenerateContentConfig(
            thinking_config=thinking_config,
            system_instruction=(
                f"{prompt_system}\n"
                "CRITICAL INSTRUCTIONS:\n"
                "1. You must write and respond exclusively in the Uzbek language.\n"
                "2. In your responses, NEVER use bold markdown formatting (do NOT use **).\n"
                "3. Keep the text beautiful, elegant, and readable by separating key ideas using newlines or bullet points.\n"
                "4. Code blocks must use standard triple backticks.\n"
                "5. Do not output any thinking process or internal reasoning blocks."
            )
        )

        for i in range(retries):
            try:
                logger.info(f"Calling Gemini API model={model} (attempt {i+1}/{retries})")
                response = await self.ai_client.aio.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config
                )
                text = response.text
                if not text:
                    raise ValueError("Gemini API returned an empty response.")
                return text
            except Exception as e:
                error_msg = str(e)
                is_temp = any(err in error_msg for err in ["503", "429", "RESOURCE_EXHAUSTED", "high demand"])
                if is_temp and i < retries - 1:
                    logger.warning(f"Temporary Gemini API error: {e}. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    delay *= 2
                    continue
                logger.error(f"Gemini API Error: {e}", exc_info=True)
                raise e

gemini_service = GeminiService()
