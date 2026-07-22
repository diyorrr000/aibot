import io
import logging
from typing import List, Any
from PIL import Image
from aiogram import Bot, types
from google.genai import types as genai_types

logger = logging.getLogger(__name__)

class MediaService:
    @staticmethod
    def optimize_image(image_bytes: bytes, max_size: int = 1280) -> bytes:
        """
        Resize image to save RAM/bandwidth before sending to Gemini.
        """
        img = Image.open(io.BytesIO(image_bytes))
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
        return out_io.getvalue()

    @classmethod
    async def process_photo(
        cls,
        bot: Bot,
        photo_list: List[types.PhotoSize],
        caption: str = ""
    ) -> List[Any]:
        """
        Download photo and create Gemini multimodal image part.
        """
        photo = photo_list[-1]
        file_info = await bot.get_file(photo.file_id)
        file_bytes = await bot.download_file(file_info.file_path)
        
        optimized = cls.optimize_image(file_bytes.read())
        
        image_part = genai_types.Part.from_bytes(
            data=optimized,
            mime_type="image/jpeg"
        )
        
        prompt_text = (
            f"Ushbu rasmda nimalar tasvirlanganini (ob'ektlar, chizmalar, umumiy ko'rinish) va undagi barcha yozuvlarni aniqlang.\n"
            f"O'zbek tilidagi imlo xatolarini tuzating.\n"
            f"Rasm va undagi matn nima haqida ekanini to'liq tahlil qilib, o'zbek tilida batafsil tushuntirib bering.\n"
        )
        if caption:
            prompt_text += f"Mijozning rasmga bergan izohi: {caption}\n"

        return [image_part, prompt_text]

    @classmethod
    async def process_voice(
        cls,
        bot: Bot,
        voice: types.Voice
    ) -> List[Any]:
        """
        Download voice note (.ogg) and send natively to Gemini 2.5 Flash Lite multimodal audio engine.
        """
        file_info = await bot.get_file(voice.file_id)
        file_bytes = await bot.download_file(file_info.file_path)
        
        audio_part = genai_types.Part.from_bytes(
            data=file_bytes.read(),
            mime_type="audio/ogg"
        )
        
        prompt_text = (
            "Ushbu ovozli xabarni diqqat bilan eshiting va unda aytilgan fikrlarga, savollarga "
            "yoki topshiriqlarga to'liq o'zbek tilida javob berin."
        )
        return [audio_part, prompt_text]

    @classmethod
    async def process_document(
        cls,
        bot: Bot,
        document: types.Document,
        caption: str = ""
    ) -> List[Any]:
        """
        Download document file and parse contents for Gemini prompt.
        """
        file_info = await bot.get_file(document.file_id)
        file_bytes = await bot.download_file(file_info.file_path)
        
        doc_raw = file_bytes.read()
        
        doc_part = genai_types.Part.from_bytes(
            data=doc_raw,
            mime_type=document.mime_type or "text/plain"
        )
        
        prompt_text = f"Mijoz hujjat yubordi ({document.file_name}). Undagi ma'lumotlarni tahlil qilib javob bering."
        if caption:
            prompt_text += f"\nIzoh: {caption}"
            
        return [doc_part, prompt_text]

media_service = MediaService()
