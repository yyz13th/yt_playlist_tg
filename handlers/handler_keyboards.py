# keyboards.py
from aiogram import Router, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from handlers.handler_state_data import waiting_for_url, user_playlists, user_edited_playlists

router = Router()

# Keyboard layouts
start_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📋 Send Playlist")],
        [KeyboardButton(text="📤 Upload XML")]
    ],
    resize_keyboard=True
)

playlist_loaded_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎵 Download Songs")],
        [KeyboardButton(text="🎵 Download All")],
        [KeyboardButton(text="📄 Generate XML")],
        [KeyboardButton(text="📤 Upload XML")]
    ],
    resize_keyboard=True
)

xml_uploaded_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎵 Download Edited")],
        [KeyboardButton(text="📥 Download New Only")], 
        [KeyboardButton(text="📤 Upload XML")]
    ],
    resize_keyboard=True
)

# Import handlers to avoid circular imports
from handlers.handler_playlists import cmd_playlist, cmd_download_songs, cmd_generate_xml
from handlers.handler_xmls import cmd_upload_xml, cmd_download_edited

# Button handlers
@router.message(F.text == "📋 Send Playlist")
async def handle_send_playlist_button(message):
    await cmd_playlist(message)

@router.message(F.text == "📤 Upload XML")
async def handle_upload_xml_button(message):
    await cmd_upload_xml(message)

@router.message(F.text == "🎵 Download Songs")
async def handle_download_songs_button(message):
    await cmd_download_songs(message)

@router.message(F.text == "📄 Generate XML")
async def handle_generate_xml_button(message):
    await cmd_generate_xml(message)

@router.message(F.text == "🎵 Download Edited")
async def handle_download_edited_button(message):
    await cmd_download_edited(message)

@router.message(F.text == "🎵 Download All")
async def handle_download_all_button(message):
    from handlers.handler_playlists import cmd_download_all
    await cmd_download_all(message)

@router.message(F.text == "📥 Download New Only")
async def handle_download_new_only_button(message):
    from handlers.handler_xmls import cmd_download_new_only
    await cmd_download_new_only(message)
