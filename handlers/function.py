from telethon import TelegramClient   # 🔹 ADDED
import os, time, hashlib, yt_dlp
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from dotenv import load_dotenv


# 🔹 ADDED — Telethon setup
load_dotenv()

api_id = int(os.getenv('API_ID'))  # your Telegram App ID from https://my.telegram.org
api_hash = os.getenv('API_HASH')  # your App Hash
telethon_client = TelegramClient('uploader_session', api_id, api_hash)  # 🔹 ADDED


def generate_url_id(url: str):
    return hashlib.md5(url.encode()).hexdigest()


async def download_playlist_audio(bot, chat_id, track_data, download_dir: str = "downloads"):
    """Download single audio track with custom metadata and filename"""

    # Create downloads directory if it doesn't exist
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    # Use custom title if available, otherwise original title
    filename = track_data.get('custom_title') or track_data['original_title']
    # Clean filename from invalid characters
    import re
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)  # Remove invalid filename characters
    filename = filename[:100]  # Limit length

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{download_dir}/{filename}.%(ext)s',
        'restrictfilenames': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    # Add metadata if available
    postprocessor_args = []
    if track_data.get('custom_title'):
        postprocessor_args.extend(['-metadata', f'title={track_data["custom_title"]}'])
    if track_data.get('artist'):
        postprocessor_args.extend(['-metadata', f'artist={track_data["artist"]}'])
    if track_data.get('album'):
        postprocessor_args.extend(['-metadata', f'album={track_data["album"]}'])

    if postprocessor_args:
        ydl_opts['postprocessor_args'] = postprocessor_args

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(track_data['youtube_url'], download=True)
            final_filename = ydl.prepare_filename(info)
            final_filename = final_filename.replace('.webm', '.mp3').replace('.m4a', '.mp3')

            print(f"✅ Downloaded: {final_filename}")
            return final_filename

    except Exception as e:
        print(f"Error downloading {track_data['youtube_url']}: {e}")
        raise e


async def download_and_send_media(bot, chat_id, url, media_type, cleanup_msgs=None):
    # Create downloads directory if it doesn't exist
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    
    # Use a safe filename format without spaces
    ydl_opts = {
        'format': 'bestaudio/best' if media_type == 'audio' else 'best[height<=480][ext=mp4]/best[ext=mp4]',
        'outtmpl': f"downloads/%(title)s.%(ext)s",  # Use video ID instead of title to avoid spaces
        'restrictfilenames': True,  # Remove special characters from filename
    }

    # Add audio postprocessor for audio downloads
    if media_type == 'audio':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })

    try:
        start_time = time.time()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            # Get the actual filename that was downloaded
            filename = ydl.prepare_filename(info)
            
            # For audio downloads with postprocessing, the file extension changes
            if media_type == 'audio':
                filename = os.path.splitext(filename)[0] + '.mp3'
            
            # Get clean name for caption (not for filename)
            clean_name = info.get('title', 'Unknown Title')
            direct_link_info = ydl.extract_info(url, download=False)

        # Check if file actually exists
        if not os.path.exists(filename):
            await bot.send_message(chat_id, f"❌ Downloaded file not found: {filename}")
            return

        file_size_mb = os.path.getsize(filename) / (1024 * 1024)
        print(f"File downloaded: {filename} ({file_size_mb:.2f} MB)")

        # Get direct URL (same as before)
        direct_url = url
        if 'formats' in direct_link_info:
            for fmt in direct_link_info['formats']:
                fmt_url = fmt.get('url', '')
                if (fmt_url and
                    'm3u8' not in fmt_url and
                    'hls' not in fmt_url and
                    fmt.get('vcodec') != 'none' and
                    fmt.get('acodec') != 'none'):
                    direct_url = fmt_url
                    break

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔗 Скачать напрямую", url=direct_url)]
            ]
        )

        caption = f"👌Ну все! Держи {'видяшку' if media_type == 'video' else 'песенку'}.\n ✨{clean_name}✨\n"

        # Check size limit (Bot API = 50 MB)
        if file_size_mb > 49.9:
            try:
                await telethon_client.start()
                await telethon_client.send_file(
                    chat_id,
                    filename,
                    caption=caption
                )
                print("✅ Sent via Telethon (MTProto API)")
            except Exception as e:
                print(f"Telethon send failed: {e}")
                await bot.send_message(
                    chat_id,
                    f"⚠ {clean_name} слишком большой для Telegram (> {file_size_mb:.2f} MB).\n"
                    f"Ты можешь скачать его напрямую по кнопке ниже 👇",
                    reply_markup=keyboard
                )
            finally:
                await telethon_client.disconnect()

            # Cleanup
            if cleanup_msgs:
                for msg in cleanup_msgs:
                    try:
                        await bot.delete_message(chat_id, msg.message_id)
                    except Exception as e:
                        print(f"Failed to delete message {msg.message_id}: {e}")
            return

        # Normal Bot API send (under 50 MB)
        media_file = FSInputFile(filename)
        if media_type == "video":
            await bot.send_video(chat_id, media_file, caption=caption, reply_markup=keyboard)
        else:
            await bot.send_audio(chat_id, media_file, caption=caption, reply_markup=keyboard)

        # Clean up downloaded file
        try:
            os.remove(filename)
            print(f"✅ Cleaned up: {filename}")
        except Exception as e:
            print(f"⚠ Could not delete file {filename}: {e}")

        # Cleanup messages
        if cleanup_msgs:
            for msg in cleanup_msgs:
                try:
                    await bot.delete_message(chat_id, msg.message_id)
                except Exception as e:
                    print(f"Failed to delete message {msg.message_id}: {e}")

    except Exception as e:
        await bot.send_message(chat_id, f"Error: {str(e)}")
        print(f"❌ Download error: {e}")
