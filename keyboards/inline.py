from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db.models import STATUS_LABELS, STATUS_KEYS


def status_keyboard(task_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, label in STATUS_LABELS.items():
        builder.button(text=label, callback_data=f"status:{task_id}:{key}")
    builder.button(text="🗑 Удалить", callback_data=f"del_task:{task_id}")
    builder.button(text="📅 Изм. дедлайн", callback_data=f"edit_deadline:{task_id}")
    builder.adjust(2, 2)
    return builder.as_markup()


def sections_keyboard(sections, project_id: int, add_new=True) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for s in sections:
        builder.button(text=s["name"], callback_data=f"sel_section:{s['id']}")
    if add_new:
        builder.button(text="➕ Новый раздел", callback_data=f"new_section:{project_id}")
    builder.adjust(2)
    return builder.as_markup()


def board_filter_keyboard(projects, current_project=None,
                           current_status=None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📁 Все проекты" if not current_project else "✖ Сбросить проект",
                   callback_data="board_filter:project:0")
    for p in projects:
        mark = "✓ " if current_project == p["id"] else ""
        builder.button(text=f"{mark}{p['name']}", callback_data=f"board_filter:project:{p['id']}")

    builder.button(text="── Статус ──", callback_data="noop")
    builder.button(text="Все" if current_status else "✓ Все",
                   callback_data="board_filter:status:")
    for key, label in STATUS_LABELS.items():
        mark = "✓ " if current_status == key else ""
        builder.button(text=f"{mark}{label}", callback_data=f"board_filter:status:{key}")

    builder.button(text="🔄 Обновить", callback_data="board_refresh")
    builder.adjust(1)
    return builder.as_markup()


def project_dates_keyboard(project_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Изм. даты проекта", callback_data=f"edit_proj_dates:{project_id}")
    builder.adjust(1)
    return builder.as_markup()
