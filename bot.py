import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import BOT_TOKEN, DATABASE_URL
from db import init_db
from handlers import projects, tasks, board, start

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="new_project",      description="Создать проект в этом чате"),
        BotCommand(command="show_checklist",   description="Показать чеклист проекта"),
        BotCommand(command="new_section",      description="Добавить раздел (Мерч, Декор…)"),
        BotCommand(command="new_task",         description="Добавить задачу"),
        BotCommand(command="set_project_dates",description="Изменить даты проекта"),
        BotCommand(command="board",            description="Борд арт-директора (личка)"),
        BotCommand(command="help",             description="Как пользоваться"),
    ]
    await bot.set_my_commands(commands)


async def main():
    pool = await init_db(DATABASE_URL)
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp["pool"] = pool

    dp.include_router(start.router)
    dp.include_router(projects.router)
    dp.include_router(tasks.router)
    dp.include_router(board.router)

    await set_commands(bot)
    logger.info("Bot started")
    await dp.start_polling(bot, allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    asyncio.run(main())
