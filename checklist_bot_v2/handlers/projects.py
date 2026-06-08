from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from db import queries as q
from db.models import STATUS_LABELS
from handlers.common import fmt_date, parse_date, format_checklist
from keyboards.inline import sections_keyboard, project_dates_keyboard

router = Router()


class ProjectSetup(StatesGroup):
    waiting_name   = State()
    waiting_start  = State()
    waiting_end    = State()


class EditDates(StatesGroup):
    waiting_start = State()
    waiting_end   = State()


# ── /создать_чеклист — called in a group chat to register the project ───────────

@router.message(Command("создать_чеклист"))
async def cmd_start_project(message: Message, state: FSMContext):
    if message.chat.type == "private":
        await message.answer("Эта команда используется в чате проекта (группе).")
        return
    existing = await q.get_project_by_chat(message.bot["pool"], message.chat.id)
    if existing:
        await message.answer(
            f"Проект <b>{existing['name']}</b> уже создан в этом чате.\n"
            f"Используй /показать_чеклист для просмотра или /изменить_сроки_реализации для смены дат.",
            parse_mode="HTML"
        )
        return
    await state.set_state(ProjectSetup.waiting_name)
    await message.answer("Введи название проекта:")


@router.message(ProjectSetup.waiting_name)
async def project_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(ProjectSetup.waiting_start)
    await message.answer("Дата начала работ (дд.мм.гггг) или /skip:")


@router.message(ProjectSetup.waiting_start)
async def project_start(message: Message, state: FSMContext):
    if message.text.strip() == "/skip":
        await state.update_data(start_date=None)
    else:
        d = parse_date(message.text)
        if not d:
            await message.answer("Не понял дату. Введи в формате дд.мм.гггг или /skip:")
            return
        await state.update_data(start_date=d)
    await state.set_state(ProjectSetup.waiting_end)
    await message.answer("Дата окончания работ (дд.мм.гггг) или /skip:")


@router.message(ProjectSetup.waiting_end)
async def project_end(message: Message, state: FSMContext):
    data = await state.get_data()
    if message.text.strip() == "/skip":
        end_date = None
    else:
        end_date = parse_date(message.text)
        if not end_date:
            await message.answer("Не понял дату. Введи в формате дд.мм.гггг или /skip:")
            return

    pool = message.bot["pool"]
    project = await q.create_project(
        pool, message.chat.id, data["name"], data.get("start_date"), end_date
    )
    await state.clear()
    await message.answer(
        f"✅ Проект <b>{project['name']}</b> создан!\n"
        f"🗓 {fmt_date(project['start_date'])} → {fmt_date(project['end_date'])}\n\n"
        "Теперь добавь первый раздел: /добавить_раздел",
        parse_mode="HTML",
        reply_markup=project_dates_keyboard(project["id"])
    )


# ── /показать_чеклист — show full checklist ─────────────────────────────────────────

@router.message(Command("показать_чеклист"))
async def cmd_checklist(message: Message):
    pool = message.bot["pool"]
    project = await q.get_project_by_chat(pool, message.chat.id)
    if not project:
        await message.answer("Проект не найден. Сначала /создать_чеклист")
        return

    sections = await q.get_sections(pool, project["id"])
    sections_with_tasks = []
    for s in sections:
        tasks = await q.get_tasks_by_section(pool, s["id"])
        sections_with_tasks.append((s, tasks))

    text = format_checklist(project, sections_with_tasks)
    await message.answer(text, parse_mode="HTML",
                         reply_markup=project_dates_keyboard(project["id"]))


# ── /изменить_сроки_реализации — change project dates ───────────────────────────────────────

@router.message(Command("изменить_сроки_реализации"))
async def cmd_edit_dates(message: Message, state: FSMContext):
    pool = message.bot["pool"]
    project = await q.get_project_by_chat(pool, message.chat.id)
    if not project:
        await message.answer("Проект не найден.")
        return
    await state.update_data(project_id=project["id"])
    await state.set_state(EditDates.waiting_start)
    await message.answer(
        f"Текущие даты: {fmt_date(project['start_date'])} → {fmt_date(project['end_date'])}\n"
        "Новая дата начала (дд.мм.гггг) или /skip:"
    )


@router.message(EditDates.waiting_start)
async def edit_dates_start(message: Message, state: FSMContext):
    if message.text.strip() != "/skip":
        d = parse_date(message.text)
        if not d:
            await message.answer("Не понял дату. дд.мм.гггг или /skip:")
            return
        await state.update_data(start_date=d)
    await state.set_state(EditDates.waiting_end)
    await message.answer("Новая дата окончания (дд.мм.гггг) или /skip:")


@router.message(EditDates.waiting_end)
async def edit_dates_end(message: Message, state: FSMContext):
    data = await state.get_data()
    end_date = None
    if message.text.strip() != "/skip":
        end_date = parse_date(message.text)
        if not end_date:
            await message.answer("Не понял дату. дд.мм.гггг или /skip:")
            return

    pool = message.bot["pool"]
    await q.update_project_dates(
        pool, data["project_id"],
        data.get("start_date"), end_date
    )
    await state.clear()
    await message.answer("✅ Даты проекта обновлены!")


# ── Callback: edit dates via button ──────────────────────────────────────────

@router.callback_query(F.data.startswith("edit_proj_dates:"))
async def cb_edit_proj_dates(call: CallbackQuery, state: FSMContext):
    project_id = int(call.data.split(":")[1])
    await state.update_data(project_id=project_id)
    await state.set_state(EditDates.waiting_start)
    await call.message.answer("Новая дата начала проекта (дд.мм.гггг) или /skip:")
    await call.answer()
