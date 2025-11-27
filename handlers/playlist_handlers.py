from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import Command
import tempfile
import os

router = Router()

@router.message(Command("playlist"))
async def cmd_playlist(message: Message):
    """Analyze YouTube playlist and show options"""
    print("🎯 PLAYLIST COMMAND TRIGGERED!")
    
    try:
        # Extract URL from command
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("Usage: /playlist <youtube_playlist_url>")
            return
        
        url = parts[1]
        
        # Verify it's a playlist URL
        if "playlist?list=" not in url:
            await message.answer("❌ This doesn't look like a YouTube playlist URL")
            return
        
        await message.answer("🔍 Analyzing playlist...")
        
        # Import the playlist functions
        try:
            from utils.playlist_analyzer import analyze_playlist
        except ImportError as e:
            await message.answer(f"❌ Import error: {e}")
            return
        
        # Analyze playlist
        playlist_data = await analyze_playlist(url)
        print(f"Playlist analyzed: {len(playlist_data['tracks'])} tracks")
        
        # Store playlist data temporarily
        if not hasattr(cmd_playlist, 'user_playlists'):
            cmd_playlist.user_playlists = {}
        cmd_playlist.user_playlists[message.from_user.id] = playlist_data
        
        # Create REPLY keyboard with options
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        
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

@router.message(Command("generate_xml"))
async def cmd_generate_xml(message: Message):
    """Generate and send XML file"""
    user_id = message.from_user.id
    
    # Get playlist data from temporary storage
    playlist_data = getattr(cmd_playlist, 'user_playlists', {}).get(user_id)
    
    if not playlist_data:
        await message.answer("❌ No playlist data found. Please use /playlist first.")
        return
    
    try:
        from utils.xml_generator import playlist_to_xml
        xml_content = playlist_to_xml(playlist_data)
        
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as f:
            f.write(xml_content)
            temp_file = f.name
        
        # Send XML file
        await message.answer_document(
            FSInputFile(temp_file, filename=f"playlist_{playlist_data['playlist_id']}.xml"),
            caption=f"📋 XML for playlist: {len(playlist_data['tracks'])} tracks\n\n"
                   "Edit the custom_title, artist, and album fields, then upload back."
        )
        
        # Clean up
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

@router.message(F.document)
async def handle_xml_upload(message: Message):
    """Handle uploaded XML files"""
    if not message.document or not message.document.file_name.endswith('.xml'):
        return
    
    try:
        await message.answer("📥 Processing uploaded XML...")
        
        # Download the file
        file_info = await message.bot.get_file(message.document.file_id)
        downloaded_file = await message.bot.download_file(file_info.file_path)
        xml_content = downloaded_file.read().decode('utf-8')
        
        # Parse XML
        from utils.xml_parser import xml_to_playlist
        edited_playlist = xml_to_playlist(xml_content)
        
        # Store the edited playlist
        if not hasattr(handle_xml_upload, 'user_edited_playlists'):
            handle_xml_upload.user_edited_playlists = {}
        handle_xml_upload.user_edited_playlists[message.from_user.id] = edited_playlist
        
        # Create reply keyboard for downloading with edits
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        
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
