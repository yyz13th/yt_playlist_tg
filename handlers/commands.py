# main_bot.py
from aiogram import Router
from handlers.handler_keyboards import router as keyboards_router
from handlers.handler_playlists import router as playlist_router
from handlers.handler_xmls import router as xml_router
from handlers.handler_videos import router as video_handler_router

router = Router()
router.include_router(keyboards_router)
router.include_router(playlist_router)
router.include_router(xml_router)
router.include_router(video_handler_router)
# In your main bot file, use main_router
# from main_bot import main_router
