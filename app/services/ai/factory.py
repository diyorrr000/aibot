import logging
from typing import List, Any, Optional, Dict
from app.services.ai.base import BaseAIProvider
from app.services.ai.gemini import GeminiProvider

logger = logging.getLogger(__name__)

class AIProviderFactory:
    def __init__(self):
        self.provider: BaseAIProvider = GeminiProvider()

    def get(self, name: str = "gemini") -> BaseAIProvider:
        return self.provider

    async def generate_response(
        self,
        contents: List[Any],
        system_prompt: Optional[str] = None,
        preferred_model: str = "gemini",
        timeout: float = 25.0,
    ) -> str:
        try:
            logger.info("Generating AI response using Gemini 2.5 Flash...")
            reply = await self.provider.generate_response(
                contents=contents,
                system_prompt=system_prompt,
                timeout=timeout,
                retries=2
            )
            if reply and reply.strip():
                return reply
        except Exception as e:
            logger.error(f"Gemini 2.5 Flash provider error: {e}")

        return "Kechirasiz, AI xizmatida vaqtinchalik muammo yuz berdi. Birozdan so'ng qayta yozing."

ai_factory = AIProviderFactory()
