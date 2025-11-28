import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.client.telegram import TelegramAPIServer
from dotenv import load_dotenv

async def main():
    load_dotenv()
    token = os.getenv('BOT_TOKEN')
    print(f"✅ Bot token: {token[:10]}...")

    local_api = TelegramAPIServer.from_base("http://77.110.116.36:8081")
    bot = Bot(token=token, server=local_api)
    print("✅ Bot instance created")

    dp = Dispatcher()
    print("✅ Dispatcher created")
    
    try:
        if not os.path.exists("downloads"):
            os.makedirs("downloads")
            print("✅ Downloads directory created")
        
        # Import all routers with debug
        print("🔄 Importing routers...")
        
        try:
            from handlers.commands import router as commands_router
            dp.include_router(commands_router)
            print("✅ commands_router included")
        except Exception as e:
            print(f"❌ commands_router failed: {e}")
            
        try:
            from handlers.callback import router as callback_router
            dp.include_router(callback_router)
            print("✅ callback_router included")
        except Exception as e:
            print(f"❌ callback_router failed: {e}")
            
        try:
            from handlers.playlist_commands import router as playlist_commands_router
            dp.include_router(playlist_commands_router)
            print("✅ playlist_commands_router included")
        except Exception as e:
            print(f"❌ playlist_commands_router failed: {e}")
            
        #try:
        #    from handlers.handler_playlists import router as playlist_downloads_router
        #    dp.include_router(playlist_downloads_router)
        #    print("✅ playlist_downloads_router included")
        #except Exception as e:
        #    print(f"❌ playlist_downloads_router failed: {e}")
        
        print('🚀 Bot Starting polling...')
        await dp.start_polling(bot)
        print('❌ Bot stopped unexpectedly')
        
    except Exception as ex:
        print(f"❌ There's an exception: {ex}")

if  __name__ == '__main__':
    try:
        print("🤖 Starting bot...")
        asyncio.run(main())
    except KeyboardInterrupt:
        print('⏹️ Exit by user')
    except Exception as e:
        print(f'💥 Critical error: {e}')
