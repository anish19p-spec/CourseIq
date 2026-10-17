import os
from pathlib import Path
import subprocess
import sys

import pytest

from documents import DocumentChunk
from vector_store import chunk_record_id, get_collection, store_chunks, search_course_chunks


def test_chroma_record_survives_process_restart(tmp_path: Path) -> None:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1])
    environment["COURSEIQ_CHROMA_PATH"] = str(tmp_path / "restart-store")
    write_record = (
        "from vector_store import store_chunks; "
        "from documents import DocumentChunk; "
        "chunk = DocumentChunk(text='Homework is worth 30%.', course_id='course_a', "
        "filename='syllabus.pdf', page_number=2, chunk_number=1); "
        "store_chunks([chunk], [[1.0, 0.0]])"
    )
    read_record = (
        "from vector_store import search_course_chunks; "
        "from rag_pipeline import format_course_evidence; "
        "results = search_course_chunks([1.0, 0.0], 'course_a'); "
        "assert len(results) == 1; "
        "assert results[0]['page_number'] == 2; "
        "assert format_course_evidence(results) == '[syllabus.pdf, p. 2]\\nHomework is worth 30%.'; "
        "assert search_course_chunks([1.0, 0.0], 'course_b') == []"
    )
    for code in (write_record, read_record):
        subprocess.run(
            [sys.executable, "-c", code], env=environment,
            check=True, capture_output=True, text=True, timeout=30,
        )


def test_explicit_storage_path_isolated_from_configured_store(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("COURSEIQ_CHROMA_PATH", str(tmp_path / "configured"))
    configured = get_collection()
    configured.add(ids=["record-1"], embeddings=[[1.0, 0.0]], documents=["Exam details"])
    isolated = get_collection(tmp_path / "isolated")
    assert isolated.count() == 0
    assert configured.count() == 1


def test_empty_storage_path_rejected(monkeypatch) -> None:
    monkeypatch.setenv("COURSEIQ_CHROMA_PATH", "")
    with pytest.raises(ValueError, match="storage path cannot be empty"):
        get_collection()


def test_chunk_retry_updates_embedding_and_preserves_citation(tmp_path: Path) -> None:
    chunk = DocumentChunk(text="Homework is worth 30%.", course_id="course_a",
                          filename="syllabus.pdf", page_number=2, chunk_number=1)
    store_chunks([chunk], [[1.0, 0.0]], tmp_path)
    store_chunks([chunk], [[0.0, 1.0]], tmp_path)
    collection = get_collection(tmp_path)
    result = collection.get(ids=[chunk_record_id(chunk)], include=["documents", "metadatas", "embeddings"])
    assert collection.count() == 1
    assert result["documents"] == [chunk.text]
    assert result["metadatas"] == [{"course_id": "course_a", "filename": "syllabus.pdf",
                                    "page_number": 2, "chunk_number": 1}]
    assert result["embeddings"].tolist() == [[0.0, 1.0]]


def test_same_filename_in_different_courses_remains_separate(tmp_path: Path) -> None:
    first = DocumentChunk(text="Exam details", course_id="course_a",
                          filename="syllabus.pdf", chunk_number=1)
    second = first.model_copy(update={"course_id": "course_b"})
    store_chunks([first, second], [[1.0, 0.0], [0.0, 1.0]], tmp_path)
    result = get_collection(tmp_path).get(include=["metadatas"])
    assert len(result["ids"]) == 2
    assert {metadata["course_id"] for metadata in result["metadatas"]} == {"course_a", "course_b"}
    assert all("page_number" not in metadata for metadata in result["metadatas"])


def test_mismatched_embeddings_rejected_before_storage(tmp_path: Path) -> None:
    chunk = DocumentChunk(text="Exam details", course_id="course_a",
                          filename="syllabus.pdf", chunk_number=1)
    with pytest.raises(ValueError, match="exactly one embedding"):
        store_chunks([chunk], [], tmp_path / "unused")
    assert not (tmp_path / "unused").exists()


def test_rag_indexing_passes_chunk_text_to_embedding_function(tmp_path: Path, monkeypatch) -> None:
    import rag_pipeline

    chunk = DocumentChunk(text="Exam details", course_id="course_a",
                          filename="syllabus.pdf", page_number=3, chunk_number=1)
    seen = []

    def fake_embedding(text):
        seen.append(text)
        return [1.0, 0.0]

    monkeypatch.setattr(rag_pipeline, "_embed_text", fake_embedding)
    assert rag_pipeline.index_document_chunks([chunk], tmp_path) == 1
    assert seen == [chunk.text]
    assert get_collection(tmp_path).get()["documents"] == [chunk.text]


def test_search_filters_course_before_ranking(tmp_path: Path) -> None:
    chunks = [
        DocumentChunk(text=text, course_id=course, filename="syllabus.pdf",
                      page_number=page, chunk_number=page)
        for text, course, page in [("Homework", "course_a", 1),
                                   ("Exam", "course_a", 2), ("Other course", "course_b", 1)]
    ]
    store_chunks(chunks, [[0.9, 0.1], [0.0, 1.0], [1.0, 0.0]], tmp_path)
    results = search_course_chunks([1.0, 0.0], "course_a", 5, tmp_path)
    assert [result["text"] for result in results] == ["Homework", "Exam"]
    assert all(result["course_id"] == "course_a" for result in results)
    assert [result["page_number"] for result in results] == [1, 2]
    assert results[0]["distance"] < results[1]["distance"]
    assert search_course_chunks([1.0, 0.0], "missing_course", 5, tmp_path) == []


def test_search_caps_large_result_request(tmp_path: Path) -> None:
    chunks = [DocumentChunk(text=f"Activity {index}", course_id="course_a",
                            filename="syllabus.pdf", chunk_number=index + 1)
              for index in range(12)]
    store_chunks(chunks, [[1.0, float(index)] for index in range(12)], tmp_path)
    assert len(search_course_chunks([1.0, 0.0], "course_a", 100, tmp_path)) == 10
    assert len(search_course_chunks([1.0, 0.0], "course_a", 1, tmp_path)) == 1


@pytest.mark.parametrize("limit", [0, -1, True, 1.5])
def test_search_rejects_invalid_limits(tmp_path: Path, limit) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        search_course_chunks([1.0, 0.0], "course_a", limit, tmp_path)


def test_search_empty_store_returns_no_evidence(tmp_path: Path) -> None:
    assert search_course_chunks([1.0, 0.0], "course_a", path=tmp_path) == []


def test_question_retrieval_embeds_question_and_keeps_course_filter(tmp_path: Path, monkeypatch) -> None:
    import rag_pipeline

    chunks = [DocumentChunk(text="Exam details", course_id=course,
                            filename="syllabus.pdf", chunk_number=1)
              for course in ["course_a", "course_b"]]
    store_chunks(chunks, [[1.0, 0.0], [1.0, 0.0]], tmp_path)
    seen = []

    def fake_embedding(text):
        seen.append(text)
        return [1.0, 0.0]

    monkeypatch.setattr(rag_pipeline, "_embed_text", fake_embedding)
    results = rag_pipeline.retrieve_course_evidence("How are exams graded?", "course_a", path=tmp_path)
    assert seen == ["How are exams graded?"]
    assert len(results) == 1
    assert results[0]["course_id"] == "course_a"
