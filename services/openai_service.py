import logging
import io
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI
from config import settings

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self, api_key: str = settings.openai_api_key):
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate_response(
        self,
        history: List[Dict[str, Any]],
        system_prompt: Optional[str] = None,
        model: str = settings.default_model
    ) -> str:
        """
        Generate chat completion response from OpenAI GPT model.
        history is a list of dicts: [{"role": "user"/"assistant", "content": ...}]
        """
        messages = []
        
        # Insert system prompt if provided
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
            
        messages.extend(history)
        
        try:
            logger.info(f"Sending request to OpenAI using model: {model}")
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=1500,
                temperature=0.7
            )
            reply = response.choices[0].message.content
            return reply or "Kechirasiz, javob shakllantirishda xatolik yuz berdi."
        except Exception as e:
            logger.error(f"OpenAI ChatCompletion error: {e}", exc_info=True)
            raise e

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        filename: str = "voice.ogg"
    ) -> str:
        """
        Transcribe voice notes or audio files using OpenAI Whisper model.
        """
        try:
            logger.info(f"Transcribing audio file ({len(audio_bytes)} bytes) with Whisper...")
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = filename
            
            transcript = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            return transcript.text
        except Exception as e:
            logger.error(f"OpenAI Whisper transcription error: {e}", exc_info=True)
            raise e

openai_service = OpenAIService()
