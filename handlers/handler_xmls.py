# xml_utils.py
import os
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
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
    """Handle uploaded XML files - merge with current playlist data"""
    if not message.document or not message.document.file_name.endswith('.xml'):
        return

    try:
        await message.answer("📥 Processing uploaded XML...")
        file_info = await message.bot.get_file(message.document.file_id)
        downloaded_file = await message.bot.download_file(file_info.file_path)
        xml_content = downloaded_file.read().decode('utf-8')

        from utils.xml_parser import xml_to_playlist, merge_playlist_data
        
        # Import state_data here to avoid circular imports
        try:
            from handlers.handler_state_data import user_playlists, user_edited_playlists
        except ImportError:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from handlers.handler_state_data import user_playlists, user_edited_playlists
        
        uploaded_playlist = xml_to_playlist(xml_content)
        user_id = message.from_user.id
        
        # Get current playlist data
        current_playlist = user_playlists.get(user_id)
        
        if not current_playlist:
            await message.answer("❌ No current playlist found. Please analyze a playlist first.", reply_markup=start_kb)
            return
        
        # Merge uploaded XML with current playlist data
        merged_playlist = merge_playlist_data(current_playlist, uploaded_playlist)
        
        # Update BOTH stored playlist data AND edited playlists
        user_playlists[user_id] = merged_playlist
        user_edited_playlists[user_id] = merged_playlist
        
        # Save the merged data to bot storage
        from utils.xml_generator import save_bot_xml
        save_bot_xml(user_id, merged_playlist)

        # Count stats for user feedback
        total_tracks = len(merged_playlist['tracks'])
        downloaded_count = sum(1 for track in merged_playlist['tracks'] if track.get('downloaded'))
        not_downloaded_count = total_tracks - downloaded_count
        custom_titles_count = sum(1 for track in merged_playlist['tracks'] if track.get('custom_title') and track['custom_title'] != track.get('original_title'))
        artists_count = sum(1 for track in merged_playlist['tracks'] if track.get('artist'))
        albums_count = sum(1 for track in merged_playlist['tracks'] if track.get('album'))

        await message.answer(
            f"✅ XML merged successfully!\n"
            f"📊 Playlist Status:\n"
            f"• Total tracks: {total_tracks}\n"
            f"• ✅ Downloaded: {downloaded_count}\n"
            f"• ⏳ Not downloaded: {not_downloaded_count}\n"
            f"• ✏️ Custom titles: {custom_titles_count}\n"
            f"• 🎤 Artists set: {artists_count}\n"
            f"• 💿 Albums set: {albums_count}\n\n"
            f"Choose download option:",
            reply_markup=xml_uploaded_kb
        )

    except Exception as e:
        await message.answer(f"❌ Error processing XML: {str(e)}", reply_markup=start_kb)

@router.message(Command("download_edited"))
async def cmd_download_edited(message: Message):
    """Download playlist with edited metadata"""
    user_id = message.from_user.id
    edited_playlist = user_edited_playlists.get(user_id)
    import os 
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

@router.message(Command("download_new_only"))
async def cmd_download_new_only(message: Message):
    """Download only tracks with downloaded=false from edited playlist"""
    user_id = message.from_user.id

    # Import os at the function level to be safe
    import os

    # Try to get the playlist from user_edited_playlists
    try:
        from handlers.handler_state_data import user_edited_playlists
        edited_playlist = user_edited_playlists.get(user_id)
    except ImportError:
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from handlers.handler_state_data import user_edited_playlists
        edited_playlist = user_edited_playlists.get(user_id)

    # If not found in user_edited_playlists, try to load from bot storage
    if not edited_playlist:
        try:
            from handlers.handler_state_data import user_playlists
            current_playlist = user_playlists.get(user_id)
            if current_playlist:
                from utils.bot_storage import bot_storage
                from utils.xml_parser import xml_to_playlist
                stored_xml = bot_storage.load_playlist_xml(user_id, current_playlist['playlist_id'])
                if stored_xml:
                    edited_playlist = xml_to_playlist(stored_xml)
                    user_edited_playlists[user_id] = edited_playlist
        except Exception as e:
            print(f"Error loading from bot storage: {e}")
            await message.answer(f"❌ Error loading playlist: {str(e)}", reply_markup=start_kb)
            return

    if not edited_playlist:
        await message.answer("❌ Edited playlist data not found. Please upload XML again.", reply_markup=start_kb)
        return

    # Filter tracks to only include those with downloaded=false
    tracks_to_download = [track for track in edited_playlist['tracks'] if not track.get('downloaded', False)]

    if not tracks_to_download:
        await message.answer("✅ All tracks in the edited playlist are already downloaded!", reply_markup=xml_uploaded_kb)
        return

    # Show download summary
    total_tracks = len(edited_playlist['tracks'])
    downloaded_count = sum(1 for track in edited_playlist['tracks'] if track.get('downloaded', False))

    await message.answer(
        f"📊 Download Summary:\n"
        f"• Total tracks: {total_tracks}\n"
        f"• Already downloaded: {downloaded_count}\n"
        f"• To download now: {len(tracks_to_download)}\n\n"
        f"📥 Starting download of {len(tracks_to_download)} new tracks..."
    )

    success_count = 0
    successful_video_ids = []

    for i, track in enumerate(tracks_to_download, 1):
        max_retries = 2
        retry_count = 0
        success = False

        while retry_count < max_retries and not success:
            try:
                track_name = track.get('custom_title') or track['original_title']
                artist = track.get('artist', 'Unknown')

                if retry_count > 0:
                    downloading_msg = await message.answer(f"🎵 {i}/{len(tracks_to_download)}: Retrying {track_name} (attempt {retry_count + 1})...")
                else:
                    downloading_msg = await message.answer(f"🎵 {i}/{len(tracks_to_download)}: Downloading {track_name} - {artist}...")

                from handlers.function import download_playlist_audio
                file_path = await download_playlist_audio(message.bot, message.chat.id, track)

                # Check if file was actually downloaded
                if not file_path or not os.path.exists(file_path):
                    raise Exception(f"Download failed - no file created at {file_path}")

                audio_file = FSInputFile(file_path)

                caption = f"🎵 {track_name}"
                if artist and artist != "Unknown":
                    caption += f" - {artist}"
                if track.get('album'):
                    caption += f" ({track['album']})"

                await message.answer_audio(audio_file, caption=caption)
                await downloading_msg.delete()

                # Clean up the file
                if os.path.exists(file_path):
                    os.remove(file_path)

                success_count += 1
                successful_video_ids.append(track['video_id'])
                success = True

            except Exception as e:
                retry_count += 1
                error_message = str(e)
                print(f"❌ Download error for {track_name} (attempt {retry_count}): {error_message}")

                if retry_count >= max_retries:
                    # Final failure
                    await message.answer(
                        f"❌ Failed to download: {track_name}\n"
                        f"Error: {error_message}\n"
                        f"Tried {max_retries} times."
                    )
                else:
                    # Wait before retry
                    import asyncio
                    await asyncio.sleep(2)  # Wait 2 seconds before retry

    # Update the downloaded flags in the edited playlist
    if success_count > 0:
        for track in edited_playlist['tracks']:
            if track['video_id'] in successful_video_ids:
                track['downloaded'] = True

        # Update both user_edited_playlists and bot storage
        user_edited_playlists[user_id] = edited_playlist

        from utils.xml_generator import save_bot_xml
        save_bot_xml(user_id, edited_playlist)

    await message.answer(
        f"✅ Download completed: {success_count}/{len(tracks_to_download)} new tracks downloaded\n"
        f"📊 Updated status: {downloaded_count + success_count}/{total_tracks} tracks downloaded",
        reply_markup=xml_uploaded_kb
    )
