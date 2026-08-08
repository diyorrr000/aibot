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
    async def process_photo(cls, bot: Bot, photo_list: List[types.PhotoSize], caption: str = "") -> List[Any]:
        photo = photo_list[-1]
        file_info = await bot.get_file(photo.file_id)
        file_bytes = await bot.download_file(file_info.file_path)
        optimized = cls.optimize_image(file_bytes.read())

        image_part = genai_types.Part.from_bytes(data=optimized, mime_type="image/jpeg")
        prompt_text = "Rasmda nimalar tasvirlanganini aniqlab o'zbek tilida tahlil qiling."
        if caption:
            prompt_text += f"\nIzoh: {caption}"
        return [image_part, prompt_text]

    @classmethod
    async def process_voice(cls, bot: Bot, voice: types.Voice) -> List[Any]:
        file_info = await bot.get_file(voice.file_id)
        file_bytes = await bot.download_file(file_info.file_path)
        audio_part = genai_types.Part.from_bytes(data=file_bytes.read(), mime_type="audio/ogg")
        prompt_text = "Ovozli xabarni eshitib, undagi fikrlarga o'zbek tilida to'liq javob bering."
        return [audio_part, prompt_text]

    @classmethod
    async def save_temporary_media(cls, bot: Bot, message: types.Message, target_chat_id: int) -> bool:
        reply = message.reply_to_message
        if not reply:
            return False

        src_name = message.chat.title or getattr(message.chat, "full_name", None) or "Noma'lum"
        caption = f"💾 {src_name} dan saqlandi"

        if reply.text:
            text = f"{caption}\n\n{reply.text}"
            try:
                await bot.send_message(chat_id=target_chat_id, text=text, parse_mode=None)
                return True
            except Exception as e:
                logger.error(f"Error sending saved text: {e}")
                return False

        file_id = None
        kind = None
        if reply.photo: file_id, kind = reply.photo[-1].file_id, "photo"
        elif reply.video: file_id, kind = reply.video.file_id, "video"
        elif reply.voice: file_id, kind = reply.voice.file_id, "voice"
        elif reply.document: file_id, kind = reply.document.file_id, "document"
        elif reply.audio: file_id, kind = reply.audio.file_id, "audio"
        elif reply.animation: file_id, kind = reply.animation.file_id, "animation"
        elif reply.video_note: file_id, kind = reply.video_note.file_id, "video_note"
        elif reply.sticker: file_id, kind = reply.sticker.file_id, "sticker"

        if not file_id:
            try:
                await bot.forward_message(chat_id=target_chat_id, from_chat_id=reply.chat.id, message_id=reply.message_id)
                return True
            except Exception as e:
                logger.error(f"Could not forward message: {e}")
                return False

        sender = getattr(bot, f"send_{kind}", None)
        if sender is None: return False

        try:
            file_info = await bot.get_file(file_id)
            file_bytes = await bot.download_file(file_info.file_path)
            filename = file_info.file_path.split("/")[-1]
            input_file = types.BufferedInputFile(file_bytes.read(), filename=filename)
            if kind in ("video_note", "sticker"):
                await sender(chat_id=target_chat_id, **{kind: input_file})
            else:
                await sender(chat_id=target_chat_id, **{kind: input_file}, caption=caption)
            return True
        except Exception as e:
            logger.warning(f"Download failed for {kind}, trying file_id fallback: {e}")
            try:
                if kind in ("video_note", "sticker"):
                    await sender(chat_id=target_chat_id, **{kind: file_id})
                else:
                    await sender(chat_id=target_chat_id, **{kind: file_id}, caption=caption)
                return True
            except Exception as e2:
                logger.error(f"file_id fallback failed: {e2}")
                return False

media_service = MediaService()
