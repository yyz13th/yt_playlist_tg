#!/usr/bin/env python3
from handlers.commands import router as commands_router
print("✅ commands_router imported")

from handlers.callback import router as callback_router
print("✅ callback_router imported")

from handlers.playlist_handlers import router as playlist_router
print("✅ playlist_router imported")

from handlers.download_handlers import router as download_router
print("✅ download_router imported")

print("🎉 All imports successful!")
