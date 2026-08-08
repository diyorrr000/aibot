import logging
from typing import List, Any, Optional, Dict
from app.services.ai.base import BaseAIProvider
from app.services.ai.claude import ClaudeProvider
from app.services.ai.grok import GrokProvider
from app.services.ai.gpt import GPTProvider
from app.services.ai.gemini import GeminiProvider

logger = logging.getLogger(__name__)

class AIProviderFactory:
    def __init__(self):
        self.providers: Dict[str, BaseAIProvider] = {
            "claude": ClaudeProvider(),
            "grok": GrokProvider(),
            "gpt": GPTProvider(),
            "gemini": GeminiProvider(),
        }

    def get(self, name: str) -> BaseAIProvider:
        key = name.lower().strip() if name else "gemini"
        return self.providers.get(key, self.providers["gemini"])

    async def generate_response(
        self,
        contents: List[Any],
        system_prompt: Optional[str] = None,
        preferred_model: str = "gemini",
        timeout: float = 20.0,
    ) -> str:
        preferred = (preferred_model or "gemini").lower()
        if preferred not in self.providers:
            preferred = "gemini"

        # Fallback chain order: preferred first, then Gemini (which is working & fast), then others
        chain = [preferred]
        for m in ("gemini", "claude", "gpt", "grok"):
            if m not in chain:
                chain.append(m)

        last_err = None
        for model_name in chain:
            provider = self.get(model_name)
            try:
                logger.info(f"Generating AI response using provider={model_name}")
                reply = await provider.generate_response(
                    contents=contents,
                    system_prompt=system_prompt,
                    timeout=timeout,
                    retries=1
                )
                if reply and reply.strip():
                    return reply
            except Exception as e:
                last_err = e
                logger.warning(f"AI provider {model_name} failed: {e}")

        logger.error(f"All AI providers failed. Last error: {last_err}")
        return "Kechirasiz, AI xizmatida vaqtinchalik muammo yuz berdi. Birozdan so'ng qayta yozing."

ai_factory = AIProviderFactory()
