from documents import DocumentChunk
from rag_pipeline import format_course_evidence, retrieve_cited_course_evidence
from vector_store import store_chunks


def test_formatter_retains_text_and_uses_actual_page_numbers() -> None:
    results = [
        {"text": "Homework\nWeekly coding problems.", "filename": "cs101.pdf", "page_number": 1},
        {"text": "Exams are worth 40%.", "filename": "cs101.pdf", "page_number": 3},
    ]
    assert format_course_evidence(results) == (
        "[cs101.pdf, p. 1]\nHomework\nWeekly coding problems.\n\n"
        "[cs101.pdf, p. 3]\nExams are worth 40%."
    )


def test_formatter_does_not_invent_a_missing_page() -> None:
    for result in [
        {"text": "Course policies", "filename": "policies.txt"},
        {"text": "Course policies", "filename": "policies.txt", "page_number": None},
    ]:
        assert format_course_evidence([result]) == "[policies.txt]\nCourse policies"


def test_empty_evidence_has_clear_message() -> None:
    assert format_course_evidence([]) == "No syllabus evidence found for the selected course."


def test_cited_retrieval_uses_selected_course(tmp_path, monkeypatch) -> None:
    import rag_pipeline

    chunks = [
        DocumentChunk(text="Homework is 30%.", course_id="course_a",
                      filename="cs101.pdf", page_number=2, chunk_number=1),
        DocumentChunk(text="Homework is 70%.", course_id="course_b",
                      filename="cs102.pdf", page_number=4, chunk_number=1),
    ]
    store_chunks(chunks, [[1.0, 0.0], [1.0, 0.0]], tmp_path)
    monkeypatch.setattr(rag_pipeline, "_embed_text", lambda text: [1.0, 0.0])
    assert retrieve_cited_course_evidence("What is homework worth?", "course_a", path=tmp_path) == (
        "[cs101.pdf, p. 2]\nHomework is 30%."
    )
