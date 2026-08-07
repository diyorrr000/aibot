import asyncio
import logging
import re
from typing import List, Any, Optional
import aiohttp

logger = logging.getLogger(__name__)

API_URLS = {
    "claude": "http://de3.bot-hosting.net:21007/kilwa-claude",
    "grok": "http://de3.bot-hosting.net:21007/kilwa-grok",
    "gpt": "http://de3.bot-hosting.net:21007/kilwa-chatgpt",
}

MODEL_NAMES = {
    "claude": "🧠 Claude Haiku 4.5 (KILWA)",
    "grok": "🌌 Grok 4.3 (KILWA)",
    "gpt": "🤖 GPT 4o (KILWA)",
}


def _clean_text(text: str) -> str:
    """Remove markdown bold (**), translation blocks, and unwanted AI self-identifications."""
    if "\n---\n" in text:
        text = text.split("\n---\n")[0]
    if "**Translation:**" in text:
        text = text.split("**Translation:**")[0]
    if "**Tarjima:**" in text:
        text = text.split("**Tarjima:**")[0]

    # Remove **bold** markers
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text, flags=re.DOTALL)
    # Remove *italic* markers
    text = re.sub(r'\*(.+?)\*', r'\1', text, flags=re.DOTALL)
    # Remove __underline__ markers
    text = re.sub(r'__(.+?)__', r'\1', text, flags=re.DOTALL)
    # Remove lone ** or * leftovers
    text = re.sub(r'\*{1,2}', '', text)
    # Clean up excess blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


class KilwaAIService:
    """
    Multi-model AI Service using KILWA APIs:
    - Claude Haiku 4.5 (http://de3.bot-hosting.net:21007/kilwa-claude)
    - Grok 4.3 (http://de3.bot-hosting.net:21007/kilwa-grok)
    """

    async def generate_response(
        self,
        contents: List[Any],
        system_prompt: Optional[str] = None,
        model: str = "claude",
        retries: int = 3,
        delay: float = 1.5,
        timeout: float = 25,
    ) -> str:
        target_model = model.lower() if model and model.lower() in API_URLS else "claude"
        api_url = API_URLS[target_model]

        # Build user text from contents list
        text_parts = []
        for item in contents:
            if isinstance(item, str):
                text_parts.append(item)
        user_text = "\n".join(text_parts) if text_parts else "Salom!"

        # Prepend system prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\nMijoz xabari: {user_text}"
        else:
            full_prompt = user_text

        last_error = None
        for attempt in range(retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        api_url,
                        params={"text": full_prompt},
                        timeout=aiohttp.ClientTimeout(total=timeout),
                    ) as resp:
                        if resp.status != 200:
                            raise Exception(f"API returned status {resp.status}")
                        data = await resp.json(content_type=None)
                        if data.get("status") != "success":
                            raise Exception(f"API error: {data}")
                        reply = data.get("reply", "")
                        if not reply:
                            raise Exception("Empty reply from API")

                        # Clean ** and other markdown leftovers
                        reply = _clean_text(reply)
                        logger.info(f"{target_model.upper()} API reply received (attempt {attempt + 1})")
                        return reply

            except Exception as e:
                last_error = e
                logger.warning(f"{target_model.upper()} API attempt {attempt + 1}/{retries} failed: {e}")
                await asyncio.sleep(delay)
                delay *= 1.5

        raise Exception(f"KILWA {target_model.upper()} API failed after {retries} attempts: {last_error}")


ai_service = KilwaAIService()
# Backward compatibility alias
claude_service = ai_service
