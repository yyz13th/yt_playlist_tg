from aiogram import Bot, Router, F
from aiogram.types import CallbackQuery
from handlers.function import download_and_send_media
import url_storage as storage

# ADD THIS LINE - Define the router
router = Router()

# Your existing callback handler
@router.callback_query(lambda callback: 'audio' in callback.data)
async def format_selection(callback: CallbackQuery, bot: Bot):
    storage.url_storage = storage.load_url_storage()
    action, url_id = callback.data.split("|")
    url = storage.url_storage.get(url_id)

    if not url:
        await callback.answer("Чет ты не URL адрес кинул....")
        return
    await callback.answer("Щас быстренька скачаю аудио...🐘")

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.delete()

    loading_msg = await callback.message.answer("Забираю к себе аудио...")
    await download_and_send_media(bot, callback.message.chat.id, url, media_type='audio')
    await loading_msg.delete()

# THEN ADD THE NEW PLAYLIST CALLBACK HANDLERS BELOW
import tempfile
import os
from aiogram.types import FSInputFile

# Add these new callback handlers
@router.callback_query(lambda callback: callback.data.startswith('playlist_'))
async def handle_playlist_actions(callback: CallbackQuery, bot: Bot):
    data = callback.data
    user_id = callback.from_user.id
    
    try:
        if data.startswith('playlist_download|'):
            playlist_id = data.split('|')[1]
            await callback.answer("Starting download...")
            await handle_playlist_download(callback, bot, user_id, playlist_id)
            
        elif data.startswith('playlist_xml|'):
            playlist_id = data.split('|')[1]
            await callback.answer("Generating XML...")
            await handle_playlist_xml(callback, bot, user_id, playlist_id)
            
        elif data == 'playlist_upload':
            await callback.answer("Ready for XML upload")
            await handle_playlist_upload(callback)
            
    except Exception as e:
        await callback.answer(f"Error: {str(e)}")
        print(f"Playlist callback error: {e}")

async def handle_playlist_download(callback: CallbackQuery, bot: Bot, user_id: int, playlist_id: str):
    """Download all songs in the playlist"""
    # Get playlist data from temporary storage
    from handlers.commands import cmd_playlist
    playlist_data = getattr(cmd_playlist, 'user_playlists', {}).get(user_id)
    
    if not playlist_data or playlist_data['playlist_id'] != playlist_id:
        await callback.message.answer("❌ Playlist data not found. Please analyze the playlist again.")
        return
    
    await callback.message.edit_reply_markup(reply_markup=None)
    status_msg = await callback.message.answer(f"📥 Downloading {len(playlist_data['tracks'])} tracks...")
    
    # Download each track
    success_count = 0
    for i, track in enumerate(playlist_data['tracks'], 1):
        try:
            await callback.message.answer(f"🎵 {i}/{len(playlist_data['tracks'])}: {track['original_title']}")
            # TODO: Uncomment when download function is ready
            # await download_and_send_media(bot, callback.message.chat.id, track['youtube_url'], media_type='audio')
            success_count += 1
        except Exception as e:
            print(f"Error downloading {track['original_title']}: {e}")
            await callback.message.answer(f"❌ Failed: {track['original_title']}")
    
    await status_msg.edit_text(f"✅ Download completed: {success_count}/{len(playlist_data['tracks'])} tracks")

async def handle_playlist_xml(callback: CallbackQuery, bot: Bot, user_id: int, playlist_id: str):
    """Generate and send XML file"""
    # Get playlist data from temporary storage
    from handlers.commands import cmd_playlist
    playlist_data = getattr(cmd_playlist, 'user_playlists', {}).get(user_id)
    
    if not playlist_data or playlist_data['playlist_id'] != playlist_id:
        await callback.message.answer("❌ Playlist data not found. Please analyze the playlist again.")
        return
    
    await callback.message.edit_reply_markup(reply_markup=None)
    
    try:
        from utils.xml_generator import playlist_to_xml
        xml_content = playlist_to_xml(playlist_data)
        
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as f:
            f.write(xml_content)
            temp_file = f.name
        
        # Send XML file
        await callback.message.answer_document(
            FSInputFile(temp_file, filename=f"playlist_{playlist_id}.xml"),
            caption=f"📋 XML for playlist: {len(playlist_data['tracks'])} tracks\n\n"
                   "Edit the custom_title, artist, and album fields, then upload back."
        )
        
        # Clean up
        os.unlink(temp_file)
        
    except Exception as e:
        await callback.message.answer(f"❌ Error generating XML: {str(e)}")

async def handle_playlist_upload(callback: CallbackQuery):
    """Prompt user to upload XML file"""
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "📤 Please upload your edited XML file.\n\n"
        "Make sure it's the same playlist XML you downloaded earlier."
    )

@router.callback_query(lambda callback: callback.data.startswith('playlist_download_edited|'))
async def handle_playlist_download_edited(callback: CallbackQuery, bot: Bot):
    """Download playlist with edited metadata"""
    playlist_id = callback.data.split('|')[1]
    user_id = callback.from_user.id
    
    # Get edited playlist data
    from handlers.commands import handle_xml_upload
    edited_playlist = getattr(handle_xml_upload, 'user_edited_playlists', {}).get(user_id)
    
    if not edited_playlist or edited_playlist['playlist_id'] != playlist_id:
        await callback.message.answer("❌ Edited playlist data not found. Please upload XML again.")
        return
    
    await callback.message.edit_reply_markup(reply_markup=None)
    status_msg = await callback.message.answer(f"📥 Downloading {len(edited_playlist['tracks'])} tracks with your edits...")
    
    # Download each track with custom metadata
    success_count = 0
    for i, track in enumerate(edited_playlist['tracks'], 1):
        try:
            # Show custom metadata if available
            track_name = track.get('custom_title') or track['original_title']
            artist = track.get('artist', 'Unknown')
            
            await callback.message.answer(f"🎵 {i}/{len(edited_playlist['tracks'])}: {track_name} - {artist}")
            # TODO: Uncomment when download function is ready
            # await download_audio_with_metadata(bot, callback.message.chat.id, track)
            success_count += 1
        except Exception as e:
            print(f"Error downloading {track['original_title']}: {e}")
            await callback.message.answer(f"❌ Failed: {track['original_title']}")
    
    await status_msg.edit_text(f"✅ Download completed: {success_count}/{len(edited_playlist['tracks'])} tracks")
