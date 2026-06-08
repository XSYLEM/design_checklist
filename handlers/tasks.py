from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import re

from db import queries as q
from db.models import STATUS_LABELS
from handlers.common import fmt_date, parse_date
from keyboards.inline import status_keyboard, sections_keyboard

router = Router()


class AddSection(StatesGroup):
    waiting_name = State()


class AddTask(StatesGroup):
    waiting_section = State()
    waiting_title   = State()
    waiting_deadline = State()


class EditDeadline(StatesGroup):
    waiting_date = State()


# ── /добавить_раздел ──────────────────────────────────────────────────────────────

@router.message(Command("добавить_раздел"))
async def cmd_add_section(message: Message, state: FSMContext):
    pool = message.bot["pool"]
    project = await q.get_project_by_chat(pool, message.chat.id)
    if not project:
        await message.answer("Сначала создай проект: /создать_чеклист")
        return
    await state.update_data(project_id=project["id"])
    await state.set_state(AddSection.waiting_name)
    await message.answer("Название раздела (например: Мерч, Декор, Полиграфия):")


@router.message(AddSection.waiting_name)
async def section_name(message: Message, state: FSMContext):
    data = await state.get_data()
    pool = message.bot["pool"]
    section = await q.create_section(pool, data["project_id"], message.text.strip())
    await state.clear()
    await message.answer(
        f"✅ Раздел <b>{section['name']}</b> создан!\n"
        "Добавь задачу: /добавить_задачу",
        parse_mode="HTML"
    )


# ── /добавить_задачу ─────────────────────────────────────────────────────────────────

@router.message(Command("добавить_задачу"))
async def cmd_add_task(message: Message, state: FSMContext):
    pool = message.bot["pool"]
    project = await q.get_project_by_chat(pool, message.chat.id)
    if not project:
        await message.answer("Сначала создай проект: /создать_чеклист")
        return

    sections = await q.get_sections(pool, project["id"])
    if not sections:
        await message.answer("Сначала создай раздел: /добавить_раздел")
        return

    await state.update_data(project_id=project["id"])
    await state.set_state(AddTask.waiting_section)
    await message.answer(
        "Выбери раздел для задачи:",
        reply_markup=sections_keyboard(sections, project["id"], add_new=True)
    )


@router.callback_query(F.data.startswith("sel_section:"))
async def cb_select_section(call: CallbackQuery, state: FSMContext):
    section_id = int(call.data.split(":")[1])
    await state.update_data(section_id=section_id)
    await state.set_state(AddTask.waiting_title)
    await call.message.answer("Название задачи:")
    await call.answer()


@router.callback_query(F.data.startswith("new_section:"))
async def cb_new_section_from_task(call: CallbackQuery, state: FSMContext):
    project_id = int(call.data.split(":")[1])
    await state.update_data(project_id=project_id)
    await state.set_state(AddSection.waiting_name)
    await call.message.answer("Название нового раздела:")
    await call.answer()


@router.message(AddTask.waiting_title)
async def task_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AddTask.waiting_deadline)
    await message.answer("Дедлайн задачи (дд.мм.гггг) или /skip:")


@router.message(AddTask.waiting_deadline)
async def task_deadline(message: Message, state: FSMContext):
    data = await state.get_data()
    deadline = None
    if message.text.strip() != "/skip":
        deadline = parse_date(message.text)
        if not deadline:
            await message.answer("Не понял дату. дд.мм.гггг или /skip:")
            return

    pool = message.bot["pool"]
    task = await q.create_task(pool, data["section_id"], data["project_id"],
                                data["title"], deadline)
    await state.clear()

    await message.answer(
        f"📌 <b>{task['title']}</b>\n"
        f"📅 Дедлайн: {fmt_date(task['deadline'])}\n"
        f"🔵 В работе\n\n"
        f"Управление задачей /редактировать_задачу_{task['id']}",
        parse_mode="HTML"
    )


# ── /редактировать_задачу_N — task card with controls ────────────────────────────────────────

@router.message(F.text.regexp(r"^/редактировать_задачу_(\d+)"))
async def cmd_task_card(message: Message):
    match = re.match(r"^/редактировать_задачу_(\d+)", message.text)
    task_id = int(match.group(1))
    pool = message.bot["pool"]
    task = await q.get_task(pool, task_id)
    if not task:
        await message.answer("Задача не найдена.")
        return

    status = STATUS_LABELS.get(task["status"], task["status"])
    await message.answer(
        f"📌 <b>{task['title']}</b>\n"
        f"📅 Дедлайн: {fmt_date(task['deadline'])}\n"
        f"Статус: {status}",
        parse_mode="HTML",
        reply_markup=status_keyboard(task_id)
    )


# ── Callbacks: status change ──────────────────────────────────────────────────

@router.callback_query(F.data.startswith("status:"))
async def cb_status(call: CallbackQuery):
    _, task_id_s, new_status = call.data.split(":")
    task_id = int(task_id_s)
    pool = call.bot["pool"]
    await q.update_task_status(pool, task_id, new_status)
    task = await q.get_task(pool, task_id)
    status = STATUS_LABELS.get(task["status"])
    await call.message.edit_text(
        f"📌 <b>{task['title']}</b>\n"
        f"📅 Дедлайн: {fmt_date(task['deadline'])}\n"
        f"Статус: {status}",
        parse_mode="HTML",
        reply_markup=status_keyboard(task_id)
    )
    await call.answer(f"Статус: {status}")


# ── Callbacks: delete task ────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("del_task:"))
async def cb_delete_task(call: CallbackQuery):
    task_id = int(call.data.split(":")[1])
    pool = call.bot["pool"]
    task = await q.get_task(pool, task_id)
    if task:
        await q.delete_task(pool, task_id)
        await call.message.edit_text(f"🗑 Задача <b>{task['title']}</b> удалена.", parse_mode="HTML")
    await call.answer()


# ── Callbacks: edit deadline ──────────────────────────────────────────────────

@router.callback_query(F.data.startswith("edit_deadline:"))
async def cb_edit_deadline(call: CallbackQuery, state: FSMContext):
    task_id = int(call.data.split(":")[1])
    await state.update_data(task_id=task_id)
    await state.set_state(EditDeadline.waiting_date)
    await call.message.answer("Новый дедлайн (дд.мм.гггг) или /skip:")
    await call.answer()


@router.message(EditDeadline.waiting_date)
async def edit_deadline_input(message: Message, state: FSMContext):
    data = await state.get_data()
    task_id = data["task_id"]
    if message.text.strip() == "/skip":
        deadline = None
    else:
        deadline = parse_date(message.text)
        if not deadline:
            await message.answer("Не понял дату. дд.мм.гггг или /skip:")
            return
    pool = message.bot["pool"]
    await q.update_task_deadline(pool, task_id, deadline)
    await state.clear()
    await message.answer(f"✅ Дедлайн обновлён: {fmt_date(deadline)}")
