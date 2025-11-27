from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, FSInputFile, ReplyKeyboardMarkup, KeyboardButton
import handlers.function as hf
import url_storage as storage
import keyboards.inline_kb as in_kb
import tempfile
import os

router = Router()

# Temporary store for last URL per chat
last_url_per_chat = {}

# Store user playlists
user_playlists = {}
user_edited_playlists = {}

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.reply(
        "Привет. Видос можно скачать тут. Ботом. Я его дам. Боту нужна ссылка. Ссылку я не дам.",
        reply_markup=in_kb.reply_btn
    )

# PLAYLIST COMMANDS
@router.message(Command("playlist"))
async def cmd_playlist(message: Message):
    """Analyze YouTube playlist and show options"""
    print("🎯 PLAYLIST COMMAND TRIGGERED!")
    
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("Usage: /playlist <youtube_playlist_url>")
            return
        
        url = parts[1]
        
        if "playlist?list=" not in url:
            await message.answer("❌ This doesn't look like a YouTube playlist URL")
            return
        
        await message.answer("🔍 Analyzing playlist...")
        
        from utils.playlist_analyzer import analyze_playlist
        playlist_data = await analyze_playlist(url)
        print(f"Playlist analyzed: {len(playlist_data['tracks'])} tracks")
        
        # Store playlist data
        user_playlists[message.from_user.id] = playlist_data
        
        # Create reply keyboard
        playlist_kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="/download_songs")],
                [KeyboardButton(text="/generate_xml")],
                [KeyboardButton(text="/upload_xml")],
                [KeyboardButton(text="/start")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        await message.answer(
            f"📋 Playlist analyzed: {len(playlist_data['tracks'])} tracks found\n\n"
            "What would you like to do?",
            reply_markup=playlist_kb
        )
        
    except Exception as e:
        print(f"❌ Error in playlist handler: {e}")
        await message.answer(f"❌ Error processing playlist: {str(e)}")

@router.message(Command("download_songs"))
async def cmd_download_songs(message: Message):
    """Download all songs in the playlist"""
    user_id = message.from_user.id
    
    playlist_data = user_playlists.get(user_id)
    if not playlist_data:
        await message.answer("❌ No playlist data found. Please use /playlist first.")
        return
    
    await message.answer(f"📥 Downloading {len(playlist_data['tracks'])} tracks...")
    
    success_count = 0
    for i, track in enumerate(playlist_data['tracks'], 1):
        try:
            track_name = track.get('custom_title') or track['original_title']
            await message.answer(f"🎵 {i}/{len(playlist_data['tracks'])}: Downloading {track_name}...")
            
            # Download the actual file
            from handlers.function import download_playlist_audio
            file_path = await download_playlist_audio(message.bot, message.chat.id, track)
            
            # Send the audio file to chat
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
            print(f"Error downloading {track['original_title']}: {e}")
            await message.answer(f"❌ Failed to download: {track['original_title']}")
    
    await message.answer(f"✅ Download completed: {success_count}/{len(playlist_data['tracks'])} tracks", reply_markup=in_kb.reply_btn)

@router.message(Command("generate_xml"))
async def cmd_generate_xml(message: Message):
    """Generate and send XML file"""
    user_id = message.from_user.id
    
    playlist_data = user_playlists.get(user_id)
    if not playlist_data:
        await message.answer("❌ No playlist data found. Please use /playlist first.")
        return
    
    try:
        from utils.xml_generator import playlist_to_xml
        xml_content = playlist_to_xml(playlist_data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as f:
            f.write(xml_content)
            temp_file = f.name
        
        await message.answer_document(
            FSInputFile(temp_file, filename=f"playlist_{playlist_data['playlist_id']}.xml"),
            caption=f"📋 XML for playlist: {len(playlist_data['tracks'])} tracks\n\n"
                   "Edit the custom_title, artist, and album fields, then upload back."
        )
        
        os.unlink(temp_file)
        
    except Exception as e:
        await message.answer(f"❌ Error generating XML: {str(e)}")

@router.message(Command("upload_xml"))
async def cmd_upload_xml(message: Message):
    """Prompt user to upload XML file"""
    await message.answer(
        "📤 Please upload your edited XML file.\n\n"
        "Make sure it's the same playlist XML you downloaded earlier."
    )

@router.message(Command("download_edited"))
async def cmd_download_edited(message: Message):
    """Download playlist with edited metadata"""
    user_id = message.from_user.id
    
    edited_playlist = user_edited_playlists.get(user_id)
    if not edited_playlist:
        await message.answer("❌ Edited playlist data not found. Please upload XML again.")
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
            print(f"Error downloading {track['original_title']}: {e}")
            await message.answer(f"❌ Failed: {track['original_title']}")
    
    await message.answer(f"✅ Download completed: {success_count}/{len(edited_playlist['tracks'])} tracks", reply_markup=in_kb.reply_btn)

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
        
        edited_kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="/download_edited")],
                [KeyboardButton(text="/start")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        await message.answer(
            f"✅ XML imported successfully!\n"
            f"Tracks: {len(edited_playlist['tracks'])}\n\n"
            f"Ready to download with your custom titles and metadata.",
            reply_markup=edited_kb
        )
        
    except Exception as e:
        await message.answer(f"❌ Error processing XML: {str(e)}")

# ORIGINAL HANDLERS
@router.message(lambda message: True)
async def handle_video(message: Message):
    text = message.text.strip()
    chat_id = message.chat.id

    # Skip playlist commands and URLs
    if text.startswith('/playlist') or "playlist?list=" in text:
        return
    
    # If message contains a link
    if any(x in text for x in ["twitter.com", "x.com", "instagram.com", "tiktok.com", "youtube.com", "youtu.be"]):
        url = text
        url_id = hf.generate_url_id(url)
        storage.url_storage[url_id] = url
        storage.save_url_storage(storage.url_storage)
        storage.url_storage = storage.load_url_storage()

        last_url_per_chat[chat_id] = url_id

        await message.answer(reply_markup=in_kb.reply_btn)
        return

    # If message is /audio
    if text == "/audio":
        url_id = last_url_per_chat.get(chat_id)
        if not url_id:
            return await message.answer("Сначала отправь ссылку!")

        url = storage.url_storage.get(url_id)
        if not url:
            return await message.answer("Ссылка не найдена!")
        
        loading_msg = await message.answer("Начинаю загрузку...")
        await hf.download_and_send_media(message.bot, message.chat.id, url, media_type='audio')
        await loading_msg.delete()
        return

    # Any other text
    await message.answer("Отправь ссылку на видео или /audio после ссылки.")
