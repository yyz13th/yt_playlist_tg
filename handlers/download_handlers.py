from aiogram import Router
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
import os

router = Router()

# Import download function
from handlers.function import download_playlist_audio

@router.message(Command("download_songs"))
async def cmd_download_songs(message: Message):
    """Download all songs in the playlist"""
    user_id = message.from_user.id
    
    # Get playlist data from temporary storage
    from handlers.playlist_handlers import cmd_playlist
    playlist_data = getattr(cmd_playlist, 'user_playlists', {}).get(user_id)
    
    if not playlist_data:
        await message.answer("❌ No playlist data found. Please use /playlist first.")
        return
    
    await message.answer(f"📥 Downloading {len(playlist_data['tracks'])} tracks...")
    
    # Import keyboard
    from keyboards.inline_kb import reply_btn
    
    # Download each track
    success_count = 0
    for i, track in enumerate(playlist_data['tracks'], 1):
        try:
            track_name = track.get('custom_title') or track['original_title']
            await message.answer(f"🎵 {i}/{len(playlist_data['tracks'])}: Downloading {track_name}...")
            
            # Download the actual file
            file_path = await download_playlist_audio(message.bot, message.chat.id, track)
            
            # Send the audio file to chat
            audio_file = FSInputFile(file_path)
            
            # Create caption with metadata
            caption = f"🎵 {track_name}"
            if track.get('artist'):
                caption += f" - {track['artist']}"
            if track.get('album'):
                caption += f" ({track['album']})"
            
            await message.answer_audio(audio_file, caption=caption)
            
            # Clean up the downloaded file
            os.remove(file_path)
            
            success_count += 1
            
        except Exception as e:
            print(f"Error downloading {track['original_title']}: {e}")
            await message.answer(f"❌ Failed to download: {track['original_title']}")
    
    await message.answer(f"✅ Download completed: {success_count}/{len(playlist_data['tracks'])} tracks", reply_markup=reply_btn)

@router.message(Command("download_edited"))
async def cmd_download_edited(message: Message):
    """Download playlist with edited metadata"""
    user_id = message.from_user.id
    
    # Get edited playlist data
    from handlers.playlist_handlers import handle_xml_upload
    edited_playlist = getattr(handle_xml_upload, 'user_edited_playlists', {}).get(user_id)
    
    if not edited_playlist:
        await message.answer("❌ Edited playlist data not found. Please upload XML again.")
        return
    
    await message.answer(f"📥 Downloading {len(edited_playlist['tracks'])} tracks with your edits...")
    
    # Import keyboard
    from keyboards.inline_kb import reply_btn
    
    # Download each track with custom metadata
    success_count = 0
    for i, track in enumerate(edited_playlist['tracks'], 1):
        try:
            # Show custom metadata if available
            track_name = track.get('custom_title') or track['original_title']
            artist = track.get('artist', 'Unknown')
            
            await message.answer(f"🎵 {i}/{len(edited_playlist['tracks'])}: Downloading {track_name} - {artist}...")
            
            # Download the actual file with custom metadata
            file_path = await download_playlist_audio(message.bot, message.chat.id, track)
            
            # Send the audio file to chat
            audio_file = FSInputFile(file_path)
            
            # Create caption with custom metadata
            caption = f"🎵 {track_name}"
            if artist and artist != "Unknown":
                caption += f" - {artist}"
            if track.get('album'):
                caption += f" ({track['album']})"
            
            await message.answer_audio(audio_file, caption=caption)
            
            # Clean up the downloaded file
            os.remove(file_path)
            
            success_count += 1
            
        except Exception as e:
            print(f"Error downloading {track['original_title']}: {e}")
            await message.answer(f"❌ Failed: {track['original_title']}")
    
    await message.answer(f"✅ Download completed: {success_count}/{len(edited_playlist['tracks'])} tracks", reply_markup=reply_btn)
