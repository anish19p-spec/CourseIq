from fastapi.testclient import TestClient

from course_store import save_course
from documents import CourseSummary
from extract import AssignmentCategory, SyllabusData
from main import app
from workload_store import CourseWorkload, save_workload


def test_reviews_courses_and_saved_workloads_share_the_database(tmp_path, monkeypatch):
    monkeypatch.setenv("COURSEIQ_CHROMA_PATH", str(tmp_path))
    client = TestClient(app)
    response = client.post("/api/reviews", json={
        "course_code": "CSCE120", "professor_name": "Example Instructor", "difficulty": 3,
        "body": "Synthetic integration review about weekly coding practice.", "consent_to_publish": True,
    })
    assert response.status_code == 201
    assert client.get("/api/workload/schedule").json()["courses"] == []
    save_course(CourseSummary(course_id="course", course_name="CSCE 120", filename="test.pdf", chunk_count=1))
    syllabus = SyllabusData(course_name="CSCE 120", total_projects=0, total_midterms=0,
                            total_homeworks=14, has_final_exam=False,
                            assignment_categories=[AssignmentCategory(category="homework", weekly_frequency=1)])
    save_workload(CourseWorkload(course_id="course", syllabus=syllabus))
    assert client.get("/api/courses").json()[0]["course_id"] == "course"
    assert client.get("/api/workload/schedule").json()["total_known_weekly_hours"] == 3
    assert client.get("/api/reviews").json()["total"] == 1
