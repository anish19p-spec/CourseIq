import os
from pathlib import Path
import subprocess
import sys

from course_store import list_courses, save_course
from documents import CourseSummary


def test_catalog_updates_by_id_and_preserves_same_named_courses(tmp_path):
    course = CourseSummary(course_id="a", course_name="CS 101", filename="syllabus.pdf",
                           chunk_count=2, warnings=["Page 2 could not be read."])
    save_course(course, tmp_path)
    save_course(course.model_copy(update={"chunk_count": 3}), tmp_path)
    save_course(course.model_copy(update={"course_id": "b"}), tmp_path)
    saved = list_courses(tmp_path)
    assert [record.course_id for record in saved] == ["a", "b"]
    assert saved[0].chunk_count == 3
    assert saved[0].warnings == course.warnings
    assert saved[1].course_name == course.course_name


def test_catalog_read_does_not_create_empty_storage(tmp_path):
    directory = tmp_path / "unused"
    assert list_courses(directory) == []
    assert not directory.exists()


def test_course_list_api_survives_process_restart(tmp_path):
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    environment["COURSEIQ_CHROMA_PATH"] = str(tmp_path / "catalog")
    write = (
        "from course_store import save_course; from documents import CourseSummary; "
        "save_course(CourseSummary(course_id='course_a', course_name='CS 101', "
        "filename='cs101.pdf', chunk_count=2, warnings=['Page 2 could not be read.']))"
    )
    read = (
        "from main import app; from fastapi.testclient import TestClient; "
        "response = TestClient(app).get('/api/courses'); "
        "assert response.status_code == 200; "
        "assert response.json() == [{'course_id': 'course_a', 'course_name': 'CS 101', "
        "'filename': 'cs101.pdf', 'chunk_count': 2, 'warnings': ['Page 2 could not be read.']}]"
    )
    for code in (write, read):
        subprocess.run([sys.executable, "-c", code], env=environment,
                       check=True, capture_output=True, text=True, timeout=30)
