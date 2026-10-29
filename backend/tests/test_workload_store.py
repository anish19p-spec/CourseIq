import os
from pathlib import Path
import subprocess
import sys

from course_store import save_course
from documents import CourseSummary
from extract import AssignmentCategory, SyllabusData
from workload_store import CourseWorkload, list_workloads, save_workload


def test_empty_workload_read_does_not_create_storage(tmp_path):
    directory = tmp_path / "unused"
    assert list_workloads(directory) == []
    assert not directory.exists()


def test_workload_reloads_after_restart_without_provider_calls(tmp_path):
    save_course(CourseSummary(course_id="one", course_name="CS 101", filename="one.pdf", chunk_count=1), tmp_path)
    syllabus = SyllabusData(course_name="CS 101", total_projects=0, total_midterms=0,
                            total_homeworks=14, has_final_exam=False,
                            assignment_categories=[AssignmentCategory(category="homework", weekly_frequency=1)])
    record = CourseWorkload(course_id="one", syllabus=syllabus)
    save_workload(record, tmp_path)
    save_workload(record.model_copy(update={"comfort_level": 3}), tmp_path)
    assert len(list_workloads(tmp_path)) == 1
    environment = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1]),
                       COURSEIQ_CHROMA_PATH=str(tmp_path))
    environment.pop("GEMINI_API_KEY", None)
    subprocess.run([sys.executable, "-c",
        "from main import app; from fastapi.testclient import TestClient; "
        "response=TestClient(app).get('/api/workload/schedule'); "
        "assert response.status_code==200; "
        "assert response.json()['total_known_weekly_hours']==3.6; "
        "assert response.json()['courses'][0]['course_id']=='one'"],
        env=environment, check=True, capture_output=True, text=True, timeout=30)
