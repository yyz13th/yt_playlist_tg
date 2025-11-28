# video_handler.py
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from handlers.handler_state_data import last_url_per_chat
from handlers.handler_keyboards import start_kb
import url_storage as storage
#import hf

router = Router()

@router.message(lambda message: True)
async def handle_video(message: Message):
    if not message.text:
        return

    text = message.text.strip()
    chat_id = message.chat.id

    # Playlist URL detection
    if "playlist?list=" in text:
        await message.answer(
            "🔗 Это плейлист! Пожалуйста, используй команду '📋 Send Playlist'.",
            reply_markup=start_kb
        )
        return

    # Regular video links
    if any(x in text for x in ["twitter.com", "x.com", "instagram.com", "tiktok.com", "youtube.com", "youtu.be"]):
        url = text
        url_id = hf.generate_url_id(url)
        storage.url_storage[url_id] = url
        storage.save_url_storage(storage.url_storage)
        storage.url_storage = storage.load_url_storage()
        last_url_per_chat[chat_id] = url_id

        await message.answer("Ссылка сохранена! Используй /audio для загрузки.", reply_markup=start_kb)
        return

    # Audio download command
    if text == "/audio":
        url_id = last_url_per_chat.get(chat_id)
        if not url_id:
            return await message.answer("Сначала отправь ссылку!", reply_markup=start_kb)

        url = storage.url_storage.get(url_id)
        if not url:
            return await message.answer("Ссылка не найдена!", reply_markup=start_kb)

        loading_msg = await message.answer("Начинаю загрузку...")
        await hf.download_and_send_media(message.bot, message.chat.id, url, media_type='audio')
        await loading_msg.delete()
        return

    # Any other text
    await message.answer("Отправь ссылку на видео или /audio после ссылки.", reply_markup=start_kb)
