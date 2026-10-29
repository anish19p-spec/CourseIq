"""Persist the course list independently of individual searchable chunks."""

from contextlib import closing
from pathlib import Path
import sqlite3

from documents import CourseSummary
from vector_store import get_storage_path


def save_course(course: CourseSummary, path: str | Path | None = None) -> None:
    directory = get_storage_path(path)
    directory.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(directory / "courses.sqlite3")) as connection:
        with connection:
            connection.execute("CREATE TABLE IF NOT EXISTS courses (course_id TEXT PRIMARY KEY, summary TEXT NOT NULL)")
            connection.execute(
                "INSERT INTO courses (course_id, summary) VALUES (?, ?) "
                "ON CONFLICT(course_id) DO UPDATE SET summary=excluded.summary",
                (course.course_id, course.model_dump_json()),
            )


def list_courses(path: str | Path | None = None) -> list[CourseSummary]:
    database = get_storage_path(path) / "courses.sqlite3"
    if not database.exists():
        return []
    with closing(sqlite3.connect(database)) as connection:
        if not connection.execute("SELECT name FROM sqlite_master WHERE name='courses'").fetchone():
            return []
        rows = connection.execute("SELECT summary FROM courses ORDER BY course_id").fetchall()
    return [CourseSummary.model_validate_json(row[0]) for row in rows]
