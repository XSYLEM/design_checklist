import datetime
from db.models import STATUS_LABELS


def fmt_date(d) -> str:
    if not d:
        return "—"
    if isinstance(d, (datetime.date, datetime.datetime)):
        return d.strftime("%d.%m.%Y")
    return str(d)


def parse_date(s: str):
    """Parse DD.MM.YYYY or YYYY-MM-DD"""
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            continue
    return None


def format_checklist(project, sections_with_tasks: list) -> str:
    """Render the full checklist message for a project chat."""
    lines = []
    p_start = fmt_date(project["start_date"])
    p_end   = fmt_date(project["end_date"])
    lines.append(f"📋 <b>{project['name']}</b>")
    lines.append(f"🗓 {p_start} → {p_end}")
    lines.append("")

    for section, tasks in sections_with_tasks:
        lines.append(f"<b>— {section['name'].upper()} —</b>")
        if not tasks:
            lines.append("  <i>нет задач</i>")
        for t in tasks:
            status = STATUS_LABELS.get(t["status"], t["status"])
            deadline = fmt_date(t["deadline"])
            lines.append(f"  • {t['title']}")
            lines.append(f"    {status}  |  📅 {deadline}  |  /task_{t['id']}")
        lines.append("")

    return "\n".join(lines)


def format_board(tasks, title="📊 Борд арт-директора") -> str:
    if not tasks:
        return f"{title}\n\n<i>Нет задач по выбранным фильтрам</i>"

    lines = [f"{title}\n"]
    current_project = None

    for t in tasks:
        if t["project_name"] != current_project:
            current_project = t["project_name"]
            lines.append(f"\n<b>📁 {current_project}</b>")

        status = STATUS_LABELS.get(t["status"], t["status"])
        deadline = fmt_date(t["deadline"])
        lines.append(f"  [{t['section_name']}] {t['title']}")
        lines.append(f"  {status}  |  📅 {deadline}")

    return "\n".join(lines)
