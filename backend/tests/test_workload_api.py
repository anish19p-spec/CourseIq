from pathlib import Path

from fastapi.testclient import TestClient

from documents import ExtractedDocument, ExtractedPage
from documents import CourseSummary, DocumentChunk
from extract import AssignmentCategory, SyllabusData, SyllabusConfigurationError
from course_store import save_course
from vector_store import store_chunks
from workload_store import list_workloads
from main import app


client = TestClient(app)


def syllabus():
    return SyllabusData(course_name="CSCE 120", total_projects=0, total_midterms=0,
                        total_homeworks=14, has_final_exam=False, credit_hours=3,
                        assignment_categories=[AssignmentCategory(category="homework", weekly_frequency=1)])


def test_analysis_returns_category_results_and_cleans_up_upload(monkeypatch):
    paths = []

    def extract(path, source_filename):
        paths.append(path)
        return ExtractedDocument(pages=[ExtractedPage(text="Homework weekly", filename=source_filename,
                                                     page_number=1)])

    monkeypatch.setattr("main.extract_text_from_pdf", extract)
    monkeypatch.setattr("main.parse_syllabus_with_ai", lambda text: syllabus())
    response = client.post("/api/analyze", data={"course_name": "CSCE 120", "gpa": 0,
                                                "comfort_level": 5, "target_grade": "A"},
                           files={"file": ("syllabus.pdf", b"%PDF-fake", "application/pdf")})
    assert response.status_code == 200
    result = response.json()
    assert result["category_estimates"][0]["weekly_hours"] == 3
    assert result["estimate_complete"] is True
    assert result["study_planning_range"]["high"] == 9
    assert paths and all(not Path(path).exists() for path in paths)


def test_schedule_comparison_uses_validated_data_without_ai(monkeypatch):
    def unexpected_call(*args, **kwargs):
        raise AssertionError("Schedule comparison must not call Gemini")

    monkeypatch.setattr("main.parse_syllabus_with_ai", unexpected_call)
    payload = syllabus().model_dump()
    response = client.post("/api/workload/schedule", json={"courses": [
        {"course_id": "one", "syllabus": payload}, {"course_id": "two", "syllabus": payload}]})
    assert response.status_code == 200
    result = response.json()
    assert result["total_known_weekly_hours"] == 6
    assert [course["share_of_known_workload_percent"] for course in result["courses"]] == [50, 50]


def test_schedule_rejects_duplicate_ids_instead_of_losing_a_course():
    course = {"course_id": "duplicate", "syllabus": syllabus().model_dump()}
    response = client.post("/api/workload/schedule", json={"courses": [course, course]})
    assert response.status_code == 422


def test_schedule_rejects_invalid_student_profile():
    response = client.post("/api/workload/schedule", json={"courses": [
        {"course_id": "one", "syllabus": syllabus().model_dump(), "comfort_level": 0}]})
    assert response.status_code == 422


def setup_saved_course(tmp_path, monkeypatch, with_chunks=True):
    monkeypatch.setenv("COURSEIQ_CHROMA_PATH", str(tmp_path / "store"))
    save_course(CourseSummary(course_id="saved", course_name="CSCE 120", filename="syllabus.pdf", chunk_count=2))
    if with_chunks:
        chunks = [DocumentChunk(text=text, course_id=course_id, filename="syllabus.pdf", page_number=1,
                                chunk_number=number) for course_id, number, text in [
                                    ("saved", 2, "Homework every week."), ("other", 1, "Private other course."),
                                    ("saved", 1, "CSCE 120 grading.")]]
        store_chunks(chunks, [[1.0, 0.0]] * len(chunks))


def test_saved_estimate_reads_ordered_course_chunks_once_then_reuses_facts(tmp_path, monkeypatch):
    setup_saved_course(tmp_path, monkeypatch)
    calls = []

    def parse(text):
        calls.append(text)
        return syllabus()

    monkeypatch.setattr("main.parse_syllabus_with_ai", parse)
    first = client.post("/api/courses/saved/workload", json={})
    assert first.status_code == 200
    assert first.json()["used_saved_extraction"] is False
    assert len(calls) == 1
    assert calls[0].index("CSCE 120 grading.") < calls[0].index("Homework every week.")
    assert "Private other course" not in calls[0]

    second = client.post("/api/courses/saved/workload", json={"comfort_level": 3})
    assert second.status_code == 200
    assert second.json()["weekly_hours"] == 3.6
    assert second.json()["used_saved_extraction"] is True
    assert len(calls) == 1
    assert len(list_workloads()) == 1
    assert client.get("/api/workload/schedule").json()["total_known_weekly_hours"] == 3.6

    refresh = client.post("/api/courses/saved/workload", json={"refresh": True})
    assert refresh.status_code == 200
    assert len(calls) == 2


def test_failed_refresh_keeps_previous_saved_workload(tmp_path, monkeypatch):
    setup_saved_course(tmp_path, monkeypatch)
    monkeypatch.setattr("main.parse_syllabus_with_ai", lambda text: syllabus())
    assert client.post("/api/courses/saved/workload", json={}).status_code == 200

    def fail(text):
        raise RuntimeError("private provider error")

    monkeypatch.setattr("main.parse_syllabus_with_ai", fail)
    response = client.post("/api/courses/saved/workload", json={"refresh": True})
    assert response.status_code == 502
    assert "private provider error" not in response.text
    assert client.get("/api/workload/schedule").json()["total_known_weekly_hours"] == 3


def test_missing_chunks_are_reported_before_gemini_is_called(tmp_path, monkeypatch):
    setup_saved_course(tmp_path, monkeypatch, with_chunks=False)
    monkeypatch.setattr("main.parse_syllabus_with_ai", lambda text: (_ for _ in ()).throw(AssertionError()))
    response = client.post("/api/courses/saved/workload", json={})
    assert response.status_code == 409
    assert list_workloads() == []


def test_missing_provider_configuration_is_actionable_and_does_not_save(tmp_path, monkeypatch):
    setup_saved_course(tmp_path, monkeypatch)

    def fail(text):
        raise SyllabusConfigurationError("GEMINI_API_KEY is required")

    monkeypatch.setattr("main.parse_syllabus_with_ai", fail)
    assert client.post("/api/courses/saved/workload", json={}).status_code == 503
    assert list_workloads() == []


def test_unknown_course_has_no_saved_estimate(tmp_path, monkeypatch):
    monkeypatch.setenv("COURSEIQ_CHROMA_PATH", str(tmp_path / "unused"))
    assert client.post("/api/courses/missing/workload", json={}).status_code == 404
    assert not (tmp_path / "unused").exists()
