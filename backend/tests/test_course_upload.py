from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

import main
import rag_pipeline
from documents import ExtractedDocument, ExtractedPage
from vector_store import get_collection

client = TestClient(main.app)


def fake_extractor(paths):
    def extract(pdf_path, source_filename=None):
        paths.append(pdf_path)
        assert Path(pdf_path).exists()
        return ExtractedDocument(pages=[
            ExtractedPage(text="Homework is 30%.", filename=source_filename, page_number=1),
            ExtractedPage(text="Exams are 40%.", filename=source_filename, page_number=3),
        ], warnings=["Page 2 could not be read."])
    return extract


def test_upload_indexes_original_filename_and_separate_course_ids(tmp_path, monkeypatch):
    monkeypatch.setenv("COURSEIQ_CHROMA_PATH", str(tmp_path / "store"))
    paths = []
    monkeypatch.setattr(main, "extract_text_from_pdf", fake_extractor(paths))
    monkeypatch.setattr(rag_pipeline, "_embed_text", lambda text: [1.0, 0.0])
    course_ids = []
    for _ in range(2):
        response = client.post("/api/courses", data={"course_name": " CS 101 "},
                               files={"file": ("cs101.pdf", b"%PDF-fake-parser-input", "application/pdf")})
        assert response.status_code == 201
        body = response.json()
        UUID(body["course_id"])
        course_ids.append(body["course_id"])
        assert body["course_name"] == "CS 101"
        assert body["filename"] == "cs101.pdf"
        assert body["chunk_count"] == 2
        assert body["warnings"] == ["Page 2 could not be read."]
    assert len(set(course_ids)) == 2
    assert all(not Path(path).exists() for path in paths)
    stored = get_collection().get(include=["metadatas"])
    assert len(stored["ids"]) == 4
    assert all(metadata["filename"] == "cs101.pdf" for metadata in stored["metadatas"])
    assert {metadata["page_number"] for metadata in stored["metadatas"]} == {1, 3}
    listing = client.get("/api/courses")
    assert listing.status_code == 200
    saved = listing.json()
    assert {course["course_id"] for course in saved} == set(course_ids)
    assert all(course["course_name"] == "CS 101" for course in saved)
    assert all(course["warnings"] == ["Page 2 could not be read."] for course in saved)


def test_upload_cleans_temporary_file_after_embedding_failure(tmp_path, monkeypatch):
    monkeypatch.setenv("COURSEIQ_CHROMA_PATH", str(tmp_path / "unused"))
    paths = []
    monkeypatch.setattr(main, "extract_text_from_pdf", fake_extractor(paths))

    def failed_embedding(text):
        raise RuntimeError("Private provider failure details")

    monkeypatch.setattr(rag_pipeline, "_embed_text", failed_embedding)
    response = client.post("/api/courses", data={"course_name": "CS 101"},
                           files={"file": ("cs101.pdf", b"%PDF-fake-parser-input", "application/pdf")})
    assert response.status_code == 500
    assert response.json()["detail"] == "Syllabus could not be indexed. Please try again."
    assert all(not Path(path).exists() for path in paths)
    assert not (tmp_path / "unused").exists()


def test_course_upload_rejects_fake_pdf():
    response = client.post("/api/courses", data={"course_name": "CS 101"},
                           files={"file": ("cs101.pdf", b"plain text", "application/pdf")})
    assert response.status_code == 400
    assert response.json()["detail"] == "Upload does not contain a valid PDF signature."


def test_course_upload_rejects_blank_name():
    response = client.post("/api/courses", data={"course_name": "   "},
                           files={"file": ("cs101.pdf", b"%PDF-fake-parser-input", "application/pdf")})
    assert response.status_code == 400


def test_upload_reports_missing_key_and_cleans_temp_file(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    paths = []
    monkeypatch.setattr(main, "extract_text_from_pdf", fake_extractor(paths))
    response = client.post("/api/courses", data={"course_name": "CS 101"},
                           files={"file": ("cs101.pdf", b"%PDF-test", "application/pdf")})
    assert response.status_code == 503
    assert "GEMINI_API_KEY is not configured" in response.json()["detail"]
    assert all(not Path(path).exists() for path in paths)
