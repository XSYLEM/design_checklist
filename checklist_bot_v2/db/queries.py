import asyncpg
from typing import Optional
import datetime

# ── Projects ──────────────────────────────────────────────────────────────────

async def create_project(pool: asyncpg.Pool, chat_id: int, name: str,
                          start_date=None, end_date=None):
    return await pool.fetchrow(
        """INSERT INTO projects (chat_id, name, start_date, end_date)
           VALUES ($1, $2, $3, $4)
           ON CONFLICT (chat_id) DO UPDATE
           SET name=$2, start_date=$3, end_date=$4
           RETURNING *""",
        chat_id, name, start_date, end_date
    )

async def get_project_by_chat(pool: asyncpg.Pool, chat_id: int):
    return await pool.fetchrow("SELECT * FROM projects WHERE chat_id=$1", chat_id)

async def get_all_projects(pool: asyncpg.Pool):
    return await pool.fetch("SELECT * FROM projects ORDER BY name")

async def update_project_dates(pool: asyncpg.Pool, project_id: int,
                                start_date=None, end_date=None):
    await pool.execute(
        "UPDATE projects SET start_date=$2, end_date=$3 WHERE id=$1",
        project_id, start_date, end_date
    )

# ── Sections ──────────────────────────────────────────────────────────────────

async def create_section(pool: asyncpg.Pool, project_id: int, name: str):
    count = await pool.fetchval(
        "SELECT COUNT(*) FROM sections WHERE project_id=$1", project_id)
    return await pool.fetchrow(
        "INSERT INTO sections (project_id, name, position) VALUES ($1,$2,$3) RETURNING *",
        project_id, name, count
    )

async def get_sections(pool: asyncpg.Pool, project_id: int):
    return await pool.fetch(
        "SELECT * FROM sections WHERE project_id=$1 ORDER BY position, id",
        project_id
    )

async def delete_section(pool: asyncpg.Pool, section_id: int):
    await pool.execute("DELETE FROM sections WHERE id=$1", section_id)

# ── Tasks ─────────────────────────────────────────────────────────────────────

async def create_task(pool: asyncpg.Pool, section_id: int, project_id: int,
                       title: str, deadline=None):
    return await pool.fetchrow(
        """INSERT INTO tasks (section_id, project_id, title, deadline)
           VALUES ($1,$2,$3,$4) RETURNING *""",
        section_id, project_id, title, deadline
    )

async def get_tasks_by_section(pool: asyncpg.Pool, section_id: int):
    return await pool.fetch(
        "SELECT * FROM tasks WHERE section_id=$1 ORDER BY created_at",
        section_id
    )

async def get_task(pool: asyncpg.Pool, task_id: int):
    return await pool.fetchrow("SELECT * FROM tasks WHERE id=$1", task_id)

async def update_task_status(pool: asyncpg.Pool, task_id: int, status: str):
    await pool.execute(
        "UPDATE tasks SET status=$2, updated_at=NOW() WHERE id=$1",
        task_id, status
    )

async def update_task_deadline(pool: asyncpg.Pool, task_id: int, deadline):
    await pool.execute(
        "UPDATE tasks SET deadline=$2, updated_at=NOW() WHERE id=$1",
        task_id, deadline
    )

async def delete_task(pool: asyncpg.Pool, task_id: int):
    await pool.execute("DELETE FROM tasks WHERE id=$1", task_id)

# ── Board queries (art director) ──────────────────────────────────────────────

async def get_board_tasks(pool: asyncpg.Pool,
                           project_id: Optional[int] = None,
                           date_from: Optional[datetime.date] = None,
                           date_to: Optional[datetime.date] = None,
                           status: Optional[str] = None):
    conditions = []
    args = []
    i = 1

    if project_id:
        conditions.append(f"t.project_id=${i}"); args.append(project_id); i+=1
    if date_from:
        conditions.append(f"t.deadline>=${i}"); args.append(date_from); i+=1
    if date_to:
        conditions.append(f"t.deadline<=${i}"); args.append(date_to); i+=1
    if status:
        conditions.append(f"t.status=${i}"); args.append(status); i+=1

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    query = f"""
        SELECT t.*, p.name AS project_name, s.name AS section_name
        FROM tasks t
        JOIN projects p ON p.id = t.project_id
        JOIN sections s ON s.id = t.section_id
        {where}
        ORDER BY t.deadline NULLS LAST, p.name, s.name
    """
    return await pool.fetch(query, *args)
