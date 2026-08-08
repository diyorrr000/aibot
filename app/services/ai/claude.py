import asyncio
import logging
from typing import List, Any, Optional
import aiohttp
from app.services.ai.base import BaseAIProvider
from app.utils.helpers import clean_ai_markdown

logger = logging.getLogger(__name__)

CLAUDE_API_URL = "http://de3.bot-hosting.net:21007/kilwa-claude"

class ClaudeProvider(BaseAIProvider):
    async def generate_response(
        self,
        contents: List[Any],
        system_prompt: Optional[str] = None,
        timeout: float = 25.0,
        retries: int = 2,
    ) -> str:
        text_parts = [item for item in contents if isinstance(item, str)]
        user_text = "\n".join(text_parts) if text_parts else "Salom!"

        if system_prompt:
            full_prompt = f"{system_prompt}\n\nMijoz xabari: {user_text}"
        else:
            full_prompt = user_text

        delay = 1.0
        last_error = None
        for attempt in range(retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        CLAUDE_API_URL,
                        params={"text": full_prompt},
                        timeout=aiohttp.ClientTimeout(total=timeout),
                    ) as resp:
                        if resp.status != 200:
                            raise Exception(f"Status {resp.status}")
                        data = await resp.json(content_type=None)
                        if data.get("status") != "success":
                            raise Exception(f"API error: {data}")
                        reply = data.get("reply", "")
                        if not reply:
                            raise Exception("Empty reply")
                        return clean_ai_markdown(reply)
            except Exception as e:
                last_error = e
                logger.warning(f"Claude API attempt {attempt+1}/{retries} failed: {e}")
                await asyncio.sleep(delay)
                delay *= 1.5

        raise Exception(f"Claude API error: {last_error}")
