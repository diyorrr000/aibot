import base64
import io
import logging
from typing import Dict, Any, List, Union
from PIL import Image
from aiogram import Bot, types
from services.openai_service import openai_service

logger = logging.getLogger(__name__)

class MediaService:
    @staticmethod
    def encode_image_base64(image_bytes: bytes, max_size: int = 1280) -> str:
        """
        Resize image and encode to base64 data URI for GPT Vision API.
        """
        img = Image.open(io.BytesIO(image_bytes))
        
        # Handle transparency/modes
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.convert("RGBA").split()[3])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        width, height = img.size
        if max(width, height) > max_size:
            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        out_io = io.BytesIO()
        img.save(out_io, format="JPEG", quality=85)
        base64_str = base64.b64encode(out_io.getvalue()).decode('utf-8')
        return f"data:image/jpeg;base64,{base64_str}"

    @classmethod
    async def process_photo(
        cls,
        bot: Bot,
        photo_list: List[types.PhotoSize],
        caption: str = ""
    ) -> Dict[str, Any]:
        """
        Download photo, convert to base64, and format user content for OpenAI Vision.
        """
        photo = photo_list[-1]
        file_info = await bot.get_file(photo.file_id)
        file_bytes = await bot.download_file(file_info.file_path)
        
        image_data_url = cls.encode_image_base64(file_bytes.read())
        
        text_content = caption if caption else "Rasmda nima tasvirlanganini va undagi matn/savollarni tahlil qilib ber."
        
        content = [
            {"type": "text", "text": text_content},
            {"type": "image_url", "image_url": {"url": image_data_url}}
        ]
        return {"role": "user", "content": content}

    @classmethod
    async def process_voice(
        cls,
        bot: Bot,
        voice: types.Voice
    ) -> Dict[str, Any]:
        """
        Download voice note and transcribe with OpenAI Whisper.
        """
        file_info = await bot.get_file(voice.file_id)
        file_bytes = await bot.download_file(file_info.file_path)
        
        transcript_text = await openai_service.transcribe_audio(
            audio_bytes=file_bytes.read(),
            filename="voice.ogg"
        )
        
        logger.info(f"Voice transcribed text: {transcript_text}")
        prompt = f"[Mijoz yuborgan ovozli xabar matni: '{transcript_text}']"
        return {"role": "user", "content": prompt}

    @classmethod
    async def process_document(
        cls,
        bot: Bot,
        document: types.Document,
        caption: str = ""
    ) -> Dict[str, Any]:
        """
        Download text document if small enough and parse its contents.
        """
        file_info = await bot.get_file(document.file_id)
        file_bytes = await bot.download_file(file_info.file_path)
        
        doc_text = ""
        try:
            doc_text = file_bytes.read().decode('utf-8', errors='ignore')
        except Exception as e:
            logger.warning(f"Could not parse document text: {e}")
            doc_text = f"[Hujjat fayl nomi: {document.file_name}]"

        combined = f"Mijoz hujjat yubordi: {document.file_name}\n"
        if caption:
            combined += f"Izoh: {caption}\n"
        if doc_text and len(doc_text) < 4000:
            combined += f"Hujjat mazmuni:\n{doc_text}"

        return {"role": "user", "content": combined}

media_service = MediaService()
