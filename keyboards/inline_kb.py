from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

async def format_btn(url_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Песенка", callback_data=f"audio|{url_id}")]
    ])
    return keyboard

start_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="/start")]],
    resize_keyboard=True,
    one_time_keyboard=True
)

reply_btn = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/audio")],
        [KeyboardButton(text="/playlist")],
        [KeyboardButton(text="/upload_xml")]
    ],
    resize_keyboard=True,
    onetime_keyboard=False  # or remove this line entirely
)

async def video_quality_btn(url_id):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="360p", callback_data=f"quality|360|{url_id}")],
        [InlineKeyboardButton(text="480p", callback_data=f"quality|480|{url_id}")],
        [InlineKeyboardButton(text="720p", callback_data=f"quality|720|{url_id}")],
        [InlineKeyboardButton(text="Лучшee доступное", callback_data=f"quality|best|{url_id}")]
    ])
    return keyboard
