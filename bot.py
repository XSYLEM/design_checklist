import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import BOT_TOKEN, DATABASE_URL
from db import init_db
from handlers import projects, tasks, board

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="создать_чеклист",           description="Создать проект в этом чате"),
        BotCommand(command="показать_чеклист",           description="Показать чеклист проекта"),
        BotCommand(command="добавить_раздел",            description="Добавить раздел (Мерч, Декор…)"),
        BotCommand(command="добавить_задачу",            description="Добавить задачу"),
        BotCommand(command="изменить_сроки_реализации",  description="Изменить даты проекта"),
        BotCommand(command="все_задачи",                 description="Борд арт-директора (личка)"),
    ]
    await bot.set_my_commands(commands)


async def main():
    pool = await init_db(DATABASE_URL)

    bot = Bot(token=BOT_TOKEN)
    bot["pool"] = pool  # attach pool to bot for access in handlers

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(projects.router)
    dp.include_router(tasks.router)
    dp.include_router(board.router)

    await set_commands(bot)
    logger.info("Bot started")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())
