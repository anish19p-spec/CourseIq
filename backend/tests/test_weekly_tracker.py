import pytest

from engine import CourseAnalyzer, analyze_schedule
from extract import AssignmentCategory, SyllabusData
from course_store import save_course
from documents import CourseSummary, ExtractedDocument, ExtractedPage, DocumentChunk
from workload_store import CourseWorkload, save_workload
from fastapi.testclient import TestClient
from main import app


def syllabus(hours):
    return SyllabusData(course_name="Test course", total_projects=0, total_midterms=0,
                        total_homeworks=0, has_final_exam=False,
                        assignment_categories=[AssignmentCategory(category="Practice", weekly_frequency=1,
                                                                  hours_per_assignment=hours)])


def analyzer(hours):
    return CourseAnalyzer(syllabus(hours), {"comfort_level": 5})


@pytest.mark.parametrize("hours,band", [(0, "Small"), (14.99, "Small"), (15, "Medium"), (29.99, "Medium"), (30, "Large")])
def test_total_bands_have_explicit_boundaries(hours, band):
    result = analyze_schedule({"one": analyzer(hours)})
    assert result["total_known_weekly_hours"] == hours
    assert result["workload_level"] == band
    assert result["estimate_complete"] is True


@pytest.mark.parametrize("hours,rating", [(3, 3), (5, 2), (9, 1)])
def test_course_fit_is_workload_only_and_accounts_for_course_hours(hours, rating):
    result = analyze_schedule({"one": analyzer(hours)})
    fit = result["courses"][0]["workload_fit"]
    assert fit["rating"] == rating
    assert fit["weekly_hours_without_course"] == 0
    assert "not a difficulty score" in result["guidance_note"]


def test_added_courses_update_total_and_fit_without_gemini():
    result = analyze_schedule({str(i): analyzer(4) for i in range(4)})
    assert result["total_known_weekly_hours"] == 16
    assert result["workload_level"] == "Medium"
    assert all(course["workload_fit"]["rating"] == 2 for course in result["courses"])
    assert result["courses"][0]["workload_fit"]["weekly_hours_without_course"] == 12
    large = analyze_schedule({str(i): analyzer(4) for i in range(8)})
    assert large["workload_level"] == "Large"
    assert all(course["workload_fit"]["rating"] == 1 for course in large["courses"])


def test_pending_course_does_not_get_counted_as_zero_or_receive_rating():
    result = analyze_schedule({"one": analyzer(3)}, pending_course_count=1)
    assert result["total_known_weekly_hours"] == 3
    assert result["estimate_complete"] is False
    assert result["workload_level_is_provisional"] is True
    assert result["courses"][0]["workload_fit"]["rating"] is None


def test_unknown_and_partially_estimated_categories_do_not_receive_ratings():
    data = syllabus(3)
    data.assignment_categories.append(AssignmentCategory(category="Unscheduled reading"))
    result = analyze_schedule({"one": CourseAnalyzer(data, {})})
    assert result["total_known_weekly_hours"] == 3
    assert result["estimate_complete"] is False
    assert result["courses"][0]["workload_fit"]["rating"] is None
    empty = analyze_schedule({})
    assert empty["total_known_weekly_hours"] is None
    assert empty["workload_level"] == "Unknown"


def test_saved_tracker_counts_unestimated_courses_and_survives_reload(tmp_path, monkeypatch):
    monkeypatch.setenv("COURSEIQ_CHROMA_PATH", str(tmp_path))
    monkeypatch.setattr("main.parse_syllabus_with_ai", lambda _: pytest.fail("Reading tracker must not call Gemini"))
    for course_id in ("one", "two"):
        save_course(CourseSummary(course_id=course_id, course_name=course_id, filename="test.pdf", chunk_count=1))
    save_workload(CourseWorkload(course_id="one", syllabus=syllabus(4)))
    first = TestClient(app).get("/api/workload/schedule").json()
    assert first["pending_course_count"] == 1
    assert first["estimate_complete"] is False
    save_workload(CourseWorkload(course_id="two", syllabus=syllabus(5)))
    second = TestClient(app).get("/api/workload/schedule").json()
    assert second["pending_course_count"] == 0
    assert second["estimated_course_count"] == 2
    assert second["total_known_weekly_hours"] == 9
    assert second["estimate_complete"] is True
    assert TestClient(app).get("/api/workload/schedule").json() == second


def test_upload_estimate_and_add_second_course_update_persistent_total(tmp_path, monkeypatch):
    monkeypatch.setenv("COURSEIQ_CHROMA_PATH", str(tmp_path))
    monkeypatch.setattr("main.extract_text_from_pdf", lambda path, source_filename: ExtractedDocument(
        pages=[ExtractedPage(text="Weekly practice", filename=source_filename, page_number=1)]))
    monkeypatch.setattr("main.index_document_chunks", lambda chunks: len(chunks))
    monkeypatch.setattr("main.load_course_chunks", lambda course_id: [DocumentChunk(
        text="Weekly practice", course_id=course_id, filename="test.pdf", page_number=1, chunk_number=1)])
    calls = []
    def parse(text):
        calls.append(text)
        return syllabus(8)
    monkeypatch.setattr("main.parse_syllabus_with_ai", parse)
    client = TestClient(app)
    for index in range(2):
        uploaded = client.post("/api/courses", data={"course_name": f"Course {index}"},
                               files={"file": ("test.pdf", b"%PDF-test", "application/pdf")})
        assert uploaded.status_code == 201
        assert client.get("/api/workload/schedule").json()["pending_course_count"] == 1
        course_id = uploaded.json()["course_id"]
        assert client.post(f"/api/courses/{course_id}/workload", json={}).status_code == 200
        current = client.get("/api/workload/schedule").json()
        assert current["total_known_weekly_hours"] == 8 * (index + 1)
        assert current["pending_course_count"] == 0
    assert current["workload_level"] == "Medium"
    assert len(calls) == 2
    client.get("/api/workload/schedule")
    assert len(calls) == 2
