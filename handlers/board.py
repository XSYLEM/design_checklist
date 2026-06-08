import asyncpg
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from db import queries as q
from handlers.common import format_board
from keyboards.inline import board_filter_keyboard
from config import ART_DIRECTOR_IDS

router = Router()


class BoardFilter(StatesGroup):
    active = State()


def is_art_director(user_id: int) -> bool:
    return not ART_DIRECTOR_IDS or user_id in ART_DIRECTOR_IDS


@router.message(Command("board"))
async def cmd_board(message: Message, state: FSMContext, pool: asyncpg.Pool):
    if message.chat.type != "private":
        await message.answer("Борд доступен только в личке с ботом.")
        return
    if not is_art_director(message.from_user.id):
        await message.answer("У вас нет доступа к борду.")
        return
    projects = await q.get_all_projects(pool)
    tasks = await q.get_board_tasks(pool)
    await state.set_state(BoardFilter.active)
    await state.update_data(project_id=None, status=None)
    text = format_board(tasks)
    await message.answer(text, parse_mode="HTML",
                         reply_markup=board_filter_keyboard(projects))


@router.callback_query(F.data.startswith("board_filter:"))
async def cb_board_filter(call: CallbackQuery, state: FSMContext, pool: asyncpg.Pool):
    if not is_art_director(call.from_user.id):
        await call.answer("Нет доступа.")
        return
    _, filter_type, value = call.data.split(":", 2)
    data = await state.get_data()
    if filter_type == "project":
        pid = int(value)
        data["project_id"] = pid if pid != 0 else None
    elif filter_type == "status":
        data["status"] = value if value else None
    await state.update_data(**data)
    tasks = await q.get_board_tasks(pool, project_id=data.get("project_id"),
                                     status=data.get("status"))
    projects = await q.get_all_projects(pool)
    text = format_board(tasks)
    await call.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=board_filter_keyboard(projects, current_project=data.get("project_id"),
                                           current_status=data.get("status"))
    )
    await call.answer()


@router.callback_query(F.data == "board_refresh")
async def cb_board_refresh(call: CallbackQuery, state: FSMContext, pool: asyncpg.Pool):
    if not is_art_director(call.from_user.id):
        await call.answer("Нет доступа.")
        return
    data = await state.get_data()
    tasks = await q.get_board_tasks(pool, project_id=data.get("project_id"),
                                     status=data.get("status"))
    projects = await q.get_all_projects(pool)
    text = format_board(tasks)
    await call.message.edit_text(
        text, parse_mode="HTML",
        reply_markup=board_filter_keyboard(projects, current_project=data.get("project_id"),
                                           current_status=data.get("status"))
    )
    await call.answer("Обновлено")


@router.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery):
    await call.answer()
