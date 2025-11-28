# playlist.py
from aiogram import Router
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
import os
from handlers.handler_state_data import user_playlists, waiting_for_url
from handlers.handler_keyboards import playlist_loaded_kb, start_kb

router = Router()

@router.message(Command("playlist"))
async def cmd_playlist(message: Message):
    """Start playlist process - ask for URL"""
    user_id = message.from_user.id
    waiting_for_url[user_id] = True

    await message.answer(
        "📋 Пожалуйста, отправь ссылку на YouTube плейлист:\n\n"
        "Пример: https://www.youtube.com/playlist?list=PLxxxxxxxxxxxxxxx",
        reply_markup=None
    )

@router.message(lambda message: waiting_for_url.get(message.from_user.id, False))
async def handle_playlist_url(message: Message):
    """Handle the playlist URL after user sends it"""
    user_id = message.from_user.id
    waiting_for_url[user_id] = False
    url = message.text.strip()

    if "playlist?list=" not in url:
        await message.answer("❌ Это не похоже на ссылку YouTube плейлиста.", reply_markup=start_kb)
        return

    await message.answer("🔍 Анализирую плейлист...")

    try:
        from utils.playlist_analyzer import analyze_playlist
        playlist_data = await analyze_playlist(url)
        user_playlists[user_id] = playlist_data

        await message.answer(
            f"📋 Плейлист проанализирован: найдено {len(playlist_data['tracks'])} треков\n\n"
            "Что хочешь сделать?",
            reply_markup=playlist_loaded_kb
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка при обработке плейлиста: {str(e)}", reply_markup=start_kb)

@router.message(Command("download_songs"))
async def cmd_download_songs(message: Message):
    """Download all songs in the playlist"""
    user_id = message.from_user.id
    playlist_data = user_playlists.get(user_id)
    
    if not playlist_data:
        await message.answer("❌ No playlist data found.", reply_markup=start_kb)
        return

    await message.answer(f"📥 Downloading {len(playlist_data['tracks'])} tracks...")
    success_count = 0
    progress_msg = await message.answer("🔄 Progress: 0% (0/0)")

    for i, track in enumerate(playlist_data['tracks'], 1):
        try:
            track_name = track.get('custom_title') or track['original_title']
        
            # Update progress
            progress = int((i / len(playlist_data['tracks'])) * 100)
            await progress_msg.edit_text(f"🔄 Progress: {progress}% ({i}/{len(playlist_data['tracks'])})\nCurrent: {track_name}")

            from handlers.function import download_playlist_audio
            file_path = await download_playlist_audio(message.bot, message.chat.id, track)

            audio_file = FSInputFile(file_path)
            caption = f"🎵 {track_name}"
            if track.get('artist'):
                caption += f" - {track['artist']}"
            if track.get('album'):
                caption += f" ({track['album']})"

            await message.answer_audio(audio_file, caption=caption)
            os.remove(file_path)
            success_count += 1

        except Exception as e:
            await message.answer(f"❌ Failed to download: {track['original_title']}")

# Delete the progress message when done
    await progress_msg.delete()

    await message.answer(
        f"✅ Download completed: {success_count}/{len(playlist_data['tracks'])} tracks",
        reply_markup=start_kb
)

@router.message(Command("generate_xml"))
async def cmd_generate_xml(message: Message):
    """Generate and send XML file"""
    user_id = message.from_user.id
    playlist_data = user_playlists.get(user_id)
    
    if not playlist_data:
        await message.answer("❌ No playlist data found.", reply_markup=start_kb)
        return

    try:
        from utils.xml_generator import playlist_to_xml
        import tempfile
        
        xml_content = playlist_to_xml(playlist_data)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as f:
            f.write(xml_content)
            temp_file = f.name

        await message.answer_document(
            FSInputFile(temp_file, filename=f"playlist_{playlist_data['playlist_id']}.xml"),
            caption=f"📋 XML for playlist: {len(playlist_data['tracks'])} tracks",
            reply_markup=start_kb
        )
        os.unlink(temp_file)

    except Exception as e:
        await message.answer(f"❌ Error generating XML: {str(e)}", reply_markup=start_kb)
