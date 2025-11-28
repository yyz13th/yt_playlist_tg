# xml_utils.py
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
import os
from handlers.handler_state_data import user_edited_playlists
from handlers.handler_keyboards import xml_uploaded_kb, start_kb

router = Router()

@router.message(Command("upload_xml"))
async def cmd_upload_xml(message: Message):
    """Prompt user to upload XML file"""
    await message.answer(
        "📤 Please upload your edited XML file.\n\n"
        "Make sure it's the same playlist XML you downloaded earlier.",
        reply_markup=None
    )

@router.message(F.document)
async def handle_xml_upload(message: Message):
    """Handle uploaded XML files"""
    if not message.document or not message.document.file_name.endswith('.xml'):
        return

    try:
        await message.answer("📥 Processing uploaded XML...")
        file_info = await message.bot.get_file(message.document.file_id)
        downloaded_file = await message.bot.download_file(file_info.file_path)
        xml_content = downloaded_file.read().decode('utf-8')

        from utils.xml_parser import xml_to_playlist
        edited_playlist = xml_to_playlist(xml_content)
        user_edited_playlists[message.from_user.id] = edited_playlist

        await message.answer(
            f"✅ XML imported successfully!\nTracks: {len(edited_playlist['tracks'])}",
            reply_markup=xml_uploaded_kb
        )

    except Exception as e:
        await message.answer(f"❌ Error processing XML: {str(e)}", reply_markup=start_kb)

@router.message(Command("download_edited"))
async def cmd_download_edited(message: Message):
    """Download playlist with edited metadata"""
    user_id = message.from_user.id
    edited_playlist = user_edited_playlists.get(user_id)
    
    if not edited_playlist:
        await message.answer("❌ Edited playlist data not found.", reply_markup=start_kb)
        return

    await message.answer(f"📥 Downloading {len(edited_playlist['tracks'])} tracks with your edits...")
    success_count = 0
    
    for i, track in enumerate(edited_playlist['tracks'], 1):
        try:
            track_name = track.get('custom_title') or track['original_title']
            artist = track.get('artist', 'Unknown')
            await message.answer(f"🎵 {i}/{len(edited_playlist['tracks'])}: Downloading {track_name} - {artist}...")

            from handlers.function import download_playlist_audio
            file_path = await download_playlist_audio(message.bot, message.chat.id, track)

            audio_file = FSInputFile(file_path)
            caption = f"🎵 {track_name}"
            if artist and artist != "Unknown":
                caption += f" - {artist}"
            if track.get('album'):
                caption += f" ({track['album']})"

            await message.answer_audio(audio_file, caption=caption)
            os.remove(file_path)
            success_count += 1

        except Exception as e:
            await message.answer(f"❌ Failed: {track['original_title']}")

    await message.answer(
        f"✅ Download completed: {success_count}/{len(edited_playlist['tracks'])} tracks", 
        reply_markup=start_kb
    )
