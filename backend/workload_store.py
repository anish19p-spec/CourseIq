"""Save extracted workload facts and profiles alongside the local course catalog."""

from contextlib import closing
from pathlib import Path
import sqlite3

from pydantic import BaseModel, ConfigDict, Field

from extract import SyllabusData
from vector_store import get_storage_path


class StudentProfile(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    comfort_level: int = Field(default=5, ge=1, le=10)
    gpa: float = Field(default=0, ge=0, le=4, allow_inf_nan=False)


class CourseWorkload(StudentProfile):
    course_id: str = Field(min_length=1)
    syllabus: SyllabusData
    warnings: list[str] = Field(default_factory=list)


def save_workload(record: CourseWorkload, path: str | Path | None = None) -> None:
    directory = get_storage_path(path)
    directory.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(directory / "courses.sqlite3")) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        with connection:
            connection.execute("CREATE TABLE IF NOT EXISTS workloads ("
                               "course_id TEXT PRIMARY KEY REFERENCES courses(course_id), report TEXT NOT NULL)")
            connection.execute("INSERT INTO workloads (course_id, report) VALUES (?, ?) "
                               "ON CONFLICT(course_id) DO UPDATE SET report=excluded.report",
                               (record.course_id, record.model_dump_json()))


def list_workloads(path: str | Path | None = None) -> list[CourseWorkload]:
    database = get_storage_path(path) / "courses.sqlite3"
    if not database.exists():
        return []
    with closing(sqlite3.connect(database)) as connection:
        if not connection.execute("SELECT name FROM sqlite_master WHERE name='workloads'").fetchone():
            return []
        rows = connection.execute("SELECT report FROM workloads ORDER BY course_id").fetchall()
    return [CourseWorkload.model_validate_json(row[0]) for row in rows]
