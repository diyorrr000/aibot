import asyncio
import cloudscraper
import re
import time
import logging
from typing import List, Any, Optional

logger = logging.getLogger(__name__)

TEMP_EMAIL_API = "https://zecora0.serv00.net/Gmail.php"
SYNTX_BASE = "https://api.syntx.ai/api/v1"
USER_AGENT = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36"


class GrokService:
    def __init__(self):
        self.token: Optional[str] = None
        self.chat_uuid: Optional[str] = None
        self.message_count: int = 0
        self.max_per_session: int = 4  # Reinitialize before hitting the 5-message limit
        self._scraper = None
        self._lock = asyncio.Lock()

    # ─────────────────────── SYNC SESSION CREATION ───────────────────────

    def _create_session_sync(self):
        """Blocking session creation: email → OTP → token → chat UUID."""
        scraper = cloudscraper.create_scraper()

        # 1. Create temporary email
        resp = scraper.get(f"{TEMP_EMAIL_API}?action=create", timeout=20)
        if resp.status_code != 200:
            raise Exception(f"Temp-email creation failed: {resp.status_code}")
        data = resp.json()
        email, mailbox_id = data["email"], data["id"]
        logger.info(f"Grok: temp email created → {email}")

        # 2. Send OTP request
        resp = scraper.post(
            f"{SYNTX_BASE}/auth/email/send-otp",
            json={"email": email, "ref_uuid": None, "utm": ""},
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        if resp.status_code != 200 or not resp.json().get("success"):
            raise Exception("OTP send failed")
        logger.info("Grok: OTP sent, waiting…")

        # 3. Poll inbox for OTP code
        otp = None
        start = time.time()
        last_id = None
        while time.time() - start < 120:
            resp = scraper.get(
                f"{TEMP_EMAIL_API}?action=get_messages&mailbox_id={mailbox_id}&email={email}",
                timeout=15,
            )
            if resp.status_code == 200:
                msgs = resp.json()
                if msgs and isinstance(msgs, list) and msgs[0].get("id") != last_id:
                    last_id = msgs[0]["id"]
                    body = msgs[0].get("html", "") or msgs[0].get("text", "") or msgs[0].get("body", "")
                    m = re.search(r"\b(\d{6})\b", body) if body else None
                    if m:
                        otp = m.group(1)
                        logger.info(f"Grok: OTP received → {otp}")
                        break
            time.sleep(2)

        if not otp:
            raise Exception("OTP not received within 120s")

        # 4. Verify OTP → get token
        resp = scraper.post(
            f"{SYNTX_BASE}/auth/email/verify-otp",
            json={"email": email, "otp_code": otp, "ref_uuid": None, "utm": ""},
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        if resp.status_code != 200 or not resp.json().get("success"):
            raise Exception("OTP verification failed")
        token = resp.json()["token"]
        logger.info("Grok: authenticated ✓")

        # 5. Create chat session
        resp = scraper.post(
            f"{SYNTX_BASE}/chats",
            json={"title": "Bot Chat", "scope": "text"},
            headers={"Authorization": f"Bearer {token}", "User-Agent": USER_AGENT},
            timeout=15,
        )
        if resp.status_code != 201:
            raise Exception(f"Chat creation failed: {resp.status_code}")
        chat_uuid = resp.json()["uuid"]
        logger.info(f"Grok: chat created → {chat_uuid}")

        return token, chat_uuid, scraper

    # ─────────────────────── SYNC MESSAGE SENDING ────────────────────────

    def _send_message_sync(self, text: str, model: str = "grok-3") -> str:
        """Blocking message send + reply poll."""
        objects = [
            {"object_type": "text", "object_url": None, "object_text": text, "model_type": model}
        ]
        resp = self._scraper.post(
            f"{SYNTX_BASE}/chats/{self.chat_uuid}/messages?ai_name=grok",
            json={"objects": objects},
            headers={"Authorization": f"Bearer {self.token}", "User-Agent": USER_AGENT},
            timeout=30,
        )
        if resp.status_code != 200:
            raise Exception(f"Message send failed: {resp.text[:200]}")
        msg_id = resp.json().get("id")
        if not msg_id:
            raise Exception("No message ID returned")

        # Poll for AI reply
        start = time.time()
        while time.time() - start < 120:
            resp = self._scraper.get(
                f"{SYNTX_BASE}/chats/{self.chat_uuid}/messages?page_size=20",
                headers={"Authorization": f"Bearer {self.token}", "User-Agent": USER_AGENT},
                timeout=15,
            )
            if resp.status_code == 200:
                for msg in resp.json().get("messages", []):
                    if msg.get("author_id") == -1 and msg.get("id", 0) > msg_id:
                        obj = (msg.get("message_object") or [{}])[0]
                        if obj.get("object_type") == "text" and obj.get("completed"):
                            return obj["object_text"]
            time.sleep(1)

        raise Exception("No reply from Grok within 120s")

    # ────────────────────── ASYNC PUBLIC API ─────────────────────────────

    async def initialize(self):
        """Create a fresh Grok session (async wrapper)."""
        loop = asyncio.get_event_loop()
        token, chat_uuid, scraper = await loop.run_in_executor(None, self._create_session_sync)
        self.token = token
        self.chat_uuid = chat_uuid
        self._scraper = scraper
        self.message_count = 0
        logger.info("Grok: session ready ✓")

    async def generate_response(
        self,
        contents: List[Any],
        system_prompt: Optional[str] = None,
        model: str = "grok-3",
        retries: int = 2,
        delay: float = 1.0,
    ) -> str:
        """
        Drop-in replacement for GeminiService.generate_response().
        Accepts the same arguments but uses Grok 3 under the hood.
        Images / audio are passed as text description (Grok text-only for now).
        """
        async with self._lock:
            # Re-init if session is fresh or nearing the per-session message cap
            if not self.token or not self.chat_uuid or self.message_count >= self.max_per_session:
                logger.info("Grok: creating new session…")
                await self.initialize()

            # Build unified text from contents list
            text_parts = []
            for item in contents:
                if isinstance(item, str):
                    text_parts.append(item)
                # Non-text parts (images/audio) are noted but skipped for Grok text mode
            full_user_text = "\n".join(text_parts) if text_parts else "Salom!"

            # Prepend system prompt so Grok follows the same persona
            if system_prompt:
                final_text = (
                    f"[TIZIM YO'RIQNOMASI]\n{system_prompt}\n\n"
                    f"[FOYDALANUVCHI XABARI]\n{full_user_text}"
                )
            else:
                final_text = full_user_text

            loop = asyncio.get_event_loop()
            last_error = None
            for attempt in range(retries):
                try:
                    reply = await loop.run_in_executor(
                        None, self._send_message_sync, final_text, "grok-3"
                    )
                    self.message_count += 1
                    logger.info(f"Grok: reply received (session msg #{self.message_count})")
                    return reply
                except Exception as e:
                    last_error = e
                    logger.warning(f"Grok attempt {attempt+1} failed: {e}. Re-initializing…")
                    await self.initialize()
                    await asyncio.sleep(delay)

            raise Exception(f"Grok failed after {retries} attempts: {last_error}")


grok_service = GrokService()
