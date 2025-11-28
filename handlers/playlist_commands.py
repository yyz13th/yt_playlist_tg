from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.filters import Command
import tempfile

router = Router()

# Store user playlists and waiting states
user_playlists = {}
waiting_for_url = {}  # Track users waiting for URL input

@router.message(Command("playlist"))
async def cmd_playlist(message: Message):
    """Start playlist process - ask for URL"""
    print("🎯 PLAYLIST COMMAND TRIGGERED - ASKING FOR URL")
    
    user_id = message.from_user.id
    waiting_for_url[user_id] = True

    await message.answer(
        "📋 Please send the YouTube playlist URL:\n\n"
        "Example: https://www.youtube.com/playlist?list=PLxxxxxxxxxxxxxxx"
    )

@router.message(lambda message: waiting_for_url.get(message.from_user.id, False))
async def handle_playlist_url(message: Message):
    """Handle the playlist URL after user sends it"""
    user_id = message.from_user.id
    
    # Remove from waiting state
    waiting_for_url[user_id] = False
    
    url = message.text.strip()
    print(f"🔄 Processing playlist URL: {url}")

    if "playlist?list=" not in url:
        await message.answer("❌ This doesn't look like a YouTube playlist URL. Please use /playlist again.")
        return

    await message.answer("🔍 Analyzing playlist...")

    try:
        from utils.playlist_analyzer import analyze_playlist
        playlist_data = await analyze_playlist(url)
        print(f"✅ Playlist analyzed: {len(playlist_data['tracks'])} tracks")

        # Store playlist data
        user_playlists[user_id] = playlist_data

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

        import os
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
