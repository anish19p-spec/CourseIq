"""Store shared reviews in the same local SQLite database as the course catalog."""

from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from uuid import uuid4

from reviews import ReviewPage, ReviewSubmission, StudentReview, normalize_course_code, normalize_institution
from vector_store import get_storage_path


def create_review(submission: ReviewSubmission, path: str | Path | None = None) -> StudentReview:
    review = StudentReview(**submission.model_dump(exclude={"consent_to_publish"}),
                           review_id=uuid4(), created_at=datetime.now(timezone.utc))
    directory = get_storage_path(path)
    directory.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(directory / "courses.sqlite3")) as connection:
        with connection:
            connection.execute("CREATE TABLE IF NOT EXISTS student_reviews ("
                               "review_id TEXT PRIMARY KEY, institution_key TEXT NOT NULL, "
                               "course_code TEXT NOT NULL, created_at TEXT NOT NULL, "
                               "publication_consent INTEGER NOT NULL CHECK(publication_consent = 1), "
                               "review_json TEXT NOT NULL)")
            connection.execute("CREATE INDEX IF NOT EXISTS reviews_course "
                               "ON student_reviews(institution_key, course_code, created_at DESC)")
            connection.execute("INSERT INTO student_reviews VALUES (?, ?, ?, ?, ?, ?)",
                               (str(review.review_id), review.institution.casefold(), review.course_code,
                                review.created_at.isoformat(), 1, review.model_dump_json()))
    return review


def list_reviews(*, course_code: str | None = None, institution: str | None = None,
                 limit: int = 20, offset: int = 0, path: str | Path | None = None) -> ReviewPage:
    if not 1 <= limit <= 50 or offset < 0:
        raise ValueError("Invalid review pagination.")
    clauses = []
    values = []
    if course_code:
        clauses.append("course_code = ?")
        values.append(normalize_course_code(course_code))
    if institution:
        clauses.append("institution_key = ?")
        values.append(normalize_institution(institution).casefold())
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    database = get_storage_path(path) / "courses.sqlite3"
    if not database.exists():
        return ReviewPage(items=[], total=0, limit=limit, offset=offset)
    with closing(sqlite3.connect(database)) as connection:
        if not connection.execute("SELECT name FROM sqlite_master WHERE name='student_reviews'").fetchone():
            return ReviewPage(items=[], total=0, limit=limit, offset=offset)
        total = connection.execute("SELECT COUNT(*) FROM student_reviews" + where, values).fetchone()[0]
        rows = connection.execute("SELECT review_json FROM student_reviews" + where +
                                  " ORDER BY created_at DESC, review_id DESC LIMIT ? OFFSET ?",
                                  [*values, limit, offset]).fetchall()
    return ReviewPage(items=[StudentReview.model_validate_json(row[0]) for row in rows],
                      total=total, limit=limit, offset=offset)
