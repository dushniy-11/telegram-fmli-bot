from os import getenv
import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from handlers.routes import router
from handlers.routes import notifier

load_dotenv()
TOKEN = getenv("BOT_TOKEN")

dp = Dispatcher()
dp.include_router(router)


async def main():
    bot = Bot(token=TOKEN)
    asyncio.create_task(notifier(bot))
    print('Start')
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
