from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()


def main_menu_private() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Борд задач", callback_data="go_board")
    builder.button(text="📋 Как пользоваться", callback_data="go_help")
    builder.adjust(1)
    return builder.as_markup()


def main_menu_group() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🆕 Создать проект", switch_inline_query_current_chat="/new_project")
    builder.button(text="📋 Показать чеклист", switch_inline_query_current_chat="/show_checklist")
    builder.button(text="➕ Добавить раздел", switch_inline_query_current_chat="/new_section")
    builder.button(text="✅ Добавить задачу", switch_inline_query_current_chat="/new_task")
    builder.button(text="📅 Изменить сроки", switch_inline_query_current_chat="/set_project_dates")
    builder.adjust(1)
    return builder.as_markup()


@router.message(Command("start"))
async def cmd_start(message: Message):
    if message.chat.type == "private":
        await message.answer(
            "👋 Привет!\n\n"
            "Я помогаю управлять чеклистами дизайн-проектов.\n\n"
            "<b>Для арт-директора</b> — борд всех задач по всем проектам с фильтрами.\n\n"
            "<b>Для команды</b> — добавь меня в чат проекта и создай чеклист.\n\n"
            "Что хочешь сделать?",
            parse_mode="HTML",
            reply_markup=main_menu_private()
        )
    else:
        await message.answer(
            "👋 Привет! Я готов к работе.\n\n"
            "Используй кнопки ниже или команды для управления проектом:",
            reply_markup=main_menu_group()
        )


@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "📖 <b>Как пользоваться</b>\n\n"
        "<b>В чате проекта (группе):</b>\n"
        "/new_project — создать проект\n"
        "/show_checklist — показать все задачи\n"
        "/new_section — добавить раздел (Мерч, Декор…)\n"
        "/new_task — добавить задачу\n"
        "/set_project_dates — изменить сроки\n"
        "/task_N — открыть задачу №N\n\n"
        "<b>В личке (арт-директор):</b>\n"
        "/board — борд всех задач с фильтрами",
        parse_mode="HTML"
    )


from aiogram.types import CallbackQuery
from aiogram import F
import asyncpg
from db import queries as q
from handlers.common import format_board
from keyboards.inline import board_filter_keyboard
from config import ART_DIRECTOR_IDS


@router.callback_query(F.data == "go_board")
async def cb_go_board(call: CallbackQuery, pool: asyncpg.Pool):
    if ART_DIRECTOR_IDS and call.from_user.id not in ART_DIRECTOR_IDS:
        await call.answer("У вас нет доступа к борду.", show_alert=True)
        return
    projects = await q.get_all_projects(pool)
    tasks = await q.get_board_tasks(pool)
    text = format_board(tasks)
    await call.message.answer(text, parse_mode="HTML",
                               reply_markup=board_filter_keyboard(projects))
    await call.answer()


@router.callback_query(F.data == "go_help")
async def cb_go_help(call: CallbackQuery):
    await call.message.answer(
        "📖 <b>Как пользоваться</b>\n\n"
        "<b>В чате проекта (группе):</b>\n"
        "/new_project — создать проект\n"
        "/show_checklist — показать все задачи\n"
        "/new_section — добавить раздел (Мерч, Декор…)\n"
        "/new_task — добавить задачу\n"
        "/set_project_dates — изменить сроки\n"
        "/task_N — открыть задачу №N\n\n"
        "<b>В личке (арт-директор):</b>\n"
        "/board — борд всех задач с фильтрами",
        parse_mode="HTML"
    )
    await call.answer()
