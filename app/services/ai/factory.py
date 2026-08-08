import logging
from typing import List, Any, Optional, Dict
from app.services.ai.base import BaseAIProvider
from app.services.ai.gemini import GeminiProvider
from app.services.ai.claude import ClaudeProvider
from app.services.ai.gpt import GPTProvider
from app.services.ai.grok import GrokProvider

logger = logging.getLogger(__name__)

class AIProviderFactory:
    def __init__(self):
        self.providers: Dict[str, BaseAIProvider] = {
            "gemini": GeminiProvider(),
            "claude": ClaudeProvider(),
            "gpt": GPTProvider(),
            "grok": GrokProvider(),
        }

    def get(self, name: str = "gemini") -> BaseAIProvider:
        return self.providers.get(name.lower(), self.providers["gemini"])

    async def generate_response(
        self,
        contents: List[Any],
        system_prompt: Optional[str] = None,
        preferred_model: str = "gemini",
        timeout: float = 25.0,
    ) -> str:
        pref = (preferred_model or "gemini").lower()
        chain = [pref]
        for name in ["gemini", "claude", "gpt", "grok"]:
            if name not in chain:
                chain.append(name)

        for provider_name in chain:
            provider = self.get(provider_name)
            try:
                logger.info(f"Generating AI response using {provider_name}...")
                reply = await provider.generate_response(
                    contents=contents,
                    system_prompt=system_prompt,
                    timeout=timeout,
                    retries=2
                )
                if reply and reply.strip():
                    return reply
            except Exception as e:
                logger.warning(f"AI Provider '{provider_name}' error: {e}")

        return "Kechirasiz, AI xizmatida vaqtinchalik muammo yuz berdi. Birozdan so'ng qayta yozing."

ai_factory = AIProviderFactory()

