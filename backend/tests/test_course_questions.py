import pytest
from fastapi.testclient import TestClient

import main
import rag_pipeline
from documents import DocumentChunk
from vector_store import store_chunks

client = TestClient(main.app)


def test_question_api_returns_only_selected_course_with_citations(tmp_path, monkeypatch):
    monkeypatch.setenv("COURSEIQ_CHROMA_PATH", str(tmp_path / "store"))
    chunks = [
        DocumentChunk(text="Homework is 30%.", course_id="course_a", filename="cs101.pdf", page_number=2, chunk_number=1),
        DocumentChunk(text="Homework is 70%.", course_id="course_b", filename="cs102.pdf", page_number=3, chunk_number=1),
    ]
    store_chunks(chunks, [[1.0, 0.0], [1.0, 0.0]])
    questions = []

    def fake_embedding(text):
        questions.append(text)
        return [1.0, 0.0]

    monkeypatch.setattr(rag_pipeline, "_embed_text", fake_embedding)
    response = client.post("/api/courses/course_a/questions", json={"question": " What is homework worth? "})
    assert response.status_code == 200
    body = response.json()
    assert questions == ["What is homework worth?"]
    assert body["course_id"] == "course_a"
    assert len(body["evidence"]) == 1
    assert body["evidence"][0]["page_number"] == 2
    assert body["evidence"][0]["course_id"] == "course_a"
    assert body["cited_evidence"] == "[cs101.pdf, p. 2]\nHomework is 30%."


@pytest.mark.parametrize("body", [
    {"question": "   "}, {"question": "x" * 2001}, {},
    {"question": "Homework?", "n_results": 0},
    {"question": "Homework?", "n_results": 11},
    {"question": "Homework?", "n_results": True},
])
def test_question_api_rejects_invalid_input_before_embedding(body, monkeypatch):
    def unexpected_embedding(text):
        pytest.fail("Invalid input should not call the embedding provider")

    monkeypatch.setattr(rag_pipeline, "_embed_text", unexpected_embedding)
    response = client.post("/api/courses/course_a/questions", json=body)
    assert response.status_code == 422


def test_question_api_returns_empty_evidence_when_no_records_match(tmp_path, monkeypatch):
    monkeypatch.setenv("COURSEIQ_CHROMA_PATH", str(tmp_path / "store"))
    monkeypatch.setattr(rag_pipeline, "_embed_text", lambda text: [1.0, 0.0])
    response = client.post("/api/courses/unknown/questions", json={"question": "Homework?"})
    assert response.status_code == 200
    assert response.json()["evidence"] == []
    assert response.json()["cited_evidence"] == "No syllabus evidence found for the selected course."


def test_question_api_reports_provider_failure_without_exposing_details(monkeypatch):
    def failed_embedding(text):
        raise RuntimeError("Private provider diagnostics")

    monkeypatch.setattr(rag_pipeline, "_embed_text", failed_embedding)
    response = client.post("/api/courses/course_a/questions", json={"question": "Homework?"})
    assert response.status_code == 500
    assert response.json()["detail"] == "Course evidence could not be retrieved. Please try again."
