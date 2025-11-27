import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.client.telegram import TelegramAPIServer
from dotenv import load_dotenv

async def main():
    load_dotenv()
    token = os.getenv('BOT_TOKEN')

    local_api = TelegramAPIServer.from_base("http://77.110.116.36:8081")
    bot = Bot(token=token, server=local_api)

    dp = Dispatcher()
    try:
        if not os.path.exists("downloads"):
            os.makedirs("downloads")
        
        from handlers.commands import router as commands_router
        from handlers.callback import router as callback_router
        
        dp.include_router(commands_router)
        dp.include_router(callback_router)
        
        print('Bot Start')
        await dp.start_polling(bot)
        await bot.session.close()
    except Exception as ex:
        print(f"There's an exception: {ex}")

if  __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
