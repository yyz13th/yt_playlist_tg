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

# In handlers/handler_playlists.py - REPLACE the existing handle_playlist_url function

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
        
        # Check if we have a stored version
        from utils.bot_storage import bot_storage
        from utils.xml_parser import compare_playlists
        
        stored_xml = bot_storage.load_playlist_xml(user_id, playlist_data['playlist_id'])
        
        if stored_xml:
            from utils.xml_parser import xml_to_playlist
            stored_playlist = xml_to_playlist(stored_xml)
            comparison = compare_playlists(playlist_data, stored_playlist)
            
            new_count = len(comparison['new_tracks'])
            updated_count = len(comparison['updated_tracks'])
            
            if new_count > 0 or updated_count > 0:
                await message.answer(
                    f"📋 Плейлист обновлен!\n"
                    f"• Новых треков: {new_count}\n"
                    f"• Обновленных треков: {updated_count}\n"
                    f"• Всего треков: {len(playlist_data['tracks'])}"
                )
            else:
                await message.answer("📋 Плейлист не изменился с последней проверки.")
        
        user_playlists[user_id] = playlist_data

        await message.answer(
            f"📋 Плейлист проанализирован: найдено {len(playlist_data['tracks'])} треков\n\n"
            "Что хочешь сделать?",
            reply_markup=playlist_loaded_kb
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка при обработке плейлиста: {str(e)}", reply_markup=start_kb)
# In handlers/handler_playlists.py - REPLACE the existing cmd_download_songs function


@router.message(Command("download_songs"))
async def cmd_download_songs(message: Message):
    """Download only new/un-downloaded songs"""
    user_id = message.from_user.id

    playlist_data = user_playlists.get(user_id)
    if not playlist_data:
        await message.answer("❌ No playlist data found. Please use /playlist first.", reply_markup=start_kb)
        return

    # Get tracks that need downloading
    from utils.xml_parser import get_tracks_to_download
    tracks_to_download = get_tracks_to_download(user_id, playlist_data)
    
    if not tracks_to_download:
        await message.answer("✅ All songs from this playlist are already downloaded!", reply_markup=start_kb)
        return

    # Double-check: explicitly filter out any downloaded tracks
    tracks_to_download = [track for track in tracks_to_download if not track.get('downloaded', False)]
    
    if not tracks_to_download:
        await message.answer("✅ All songs from this playlist are already downloaded!", reply_markup=start_kb)
        return

    await message.answer(f"📥 Downloading {len(tracks_to_download)} new tracks...")
    success_count = 0
    successful_video_ids = []

    for i, track in enumerate(tracks_to_download, 1):
        try:
            track_name = track.get('custom_title') or track['original_title']
            downloading_msg = await message.answer(f"🎵 {i}/{len(tracks_to_download)}: Downloading {track_name}...")

            from handlers.function import download_playlist_audio
            file_path = await download_playlist_audio(message.bot, message.chat.id, track)

            audio_file = FSInputFile(file_path)
            caption = f"🎵 {track_name}"
            if track.get('artist'):
                caption += f" - {track['artist']}"
            if track.get('album'):
                caption += f" ({track['album']})"

            await message.answer_audio(audio_file, caption=caption)
            await downloading_msg.delete()
            os.remove(file_path)
            success_count += 1
            successful_video_ids.append(track['video_id'])

        except Exception as e:
            await message.answer(f"❌ Failed to download: {track['original_title']}")

    # Update the main playlist data and save to storage
    if success_count > 0:
        from utils.xml_generator import save_bot_xml
        
        # Update download status in the main playlist data
        for track in playlist_data['tracks']:
            if track['video_id'] in successful_video_ids:
                track['downloaded'] = True
        
        # Save updated playlist to bot storage
        save_bot_xml(user_id, playlist_data)
        
        # Also update the user_playlists with the changes
        user_playlists[user_id] = playlist_data

    await message.answer(
        f"✅ Download completed: {success_count}/{len(tracks_to_download)} tracks downloaded",
        reply_markup=start_kb
    )

@router.message(Command("generate_xml"))
async def cmd_generate_xml(message: Message):
    """Generate XML file, copying from existing bot XML if available"""
    user_id = message.from_user.id
    playlist_data = user_playlists.get(user_id)
    
    if not playlist_data:
        await message.answer("❌ No playlist data found. Please use /playlist first.", reply_markup=start_kb)
        return

    try:
        from utils.xml_generator import playlist_to_xml
        import tempfile
        
        # Generate XML, passing user_id to copy from existing bot XML
        xml_content = playlist_to_xml(playlist_data, user_id)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as f:
            f.write(xml_content)
            temp_file = f.name

        # Count downloaded vs not downloaded tracks for the message
        downloaded_count = sum(1 for track in playlist_data['tracks'] if track.get('downloaded'))
        not_downloaded_count = len(playlist_data['tracks']) - downloaded_count

        await message.answer_document(
            FSInputFile(temp_file, filename=f"playlist_{playlist_data['playlist_id']}.xml"),
            caption=(
                f"📋 XML for playlist: {len(playlist_data['tracks'])} tracks\n"
                f"✅ Downloaded: {downloaded_count}\n"
                f"⏳ Not downloaded: {not_downloaded_count}\n\n"
                "Edit the custom_title, artist, and album fields, then upload back."
            ),
            reply_markup=start_kb
        )
        os.unlink(temp_file)

    except Exception as e:
        await message.answer(f"❌ Error generating XML: {str(e)}", reply_markup=start_kb)


# In handlers/handler_playlists.py - ADD this NEW function at the end

@router.message(Command("download_all"))
async def cmd_download_all(message: Message):
    """Download all songs regardless of download status"""
    user_id = message.from_user.id

    playlist_data = user_playlists.get(user_id)
    if not playlist_data:
        await message.answer("❌ No playlist data found.", reply_markup=start_kb)
        return

    # Use all tracks
    tracks_to_download = playlist_data['tracks']
    
    await message.answer(f"📥 Force downloading all {len(tracks_to_download)} tracks...")
    success_count = 0

    for i, track in enumerate(tracks_to_download, 1):
        try:
            track_name = track.get('custom_title') or track['original_title']
            downloading_msg = await message.answer(f"🎵 {i}/{len(tracks_to_download)}: Downloading {track_name}...")

            from handlers.function import download_playlist_audio
            file_path = await download_playlist_audio(message.bot, message.chat.id, track)

            audio_file = FSInputFile(file_path)
            caption = f"🎵 {track_name}"
            if track.get('artist'):
                caption += f" - {track['artist']}"
            if track.get('album'):
                caption += f" ({track['album']})"

            await message.answer_audio(audio_file, caption=caption)
            await downloading_msg.delete()
            os.remove(file_path)
            success_count += 1

        except Exception as e:
            await message.answer(f"❌ Failed to download: {track['original_title']}")

    # After download, save XML with all tracks marked as downloaded
    from utils.xml_generator import save_bot_xml
    save_bot_xml(user_id, playlist_data)

    await message.answer(
        f"✅ Force download completed: {success_count}/{len(tracks_to_download)} tracks downloaded",
        reply_markup=start_kb
    )
