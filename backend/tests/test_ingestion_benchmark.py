import json
import os
from pathlib import Path
import subprocess
import sys

import httpx
import pytest

import benchmark_ingestion as benchmark
from benchmark_ingestion import EmbeddingRecorder, benchmark_pdf


@pytest.fixture
def syllabus_pdf(tmp_path):
    """Small deterministic text PDF; extraction uses the real pdfplumber parser."""
    text = "Homework requires weekly coding and written explanations. " * 8
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream",
    ]
    content = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, body in enumerate(objects, 1):
        offsets.append(len(content))
        content.extend(f"{index} 0 obj\n".encode() + body + b"\nendobj\n")
    xref = len(content)
    content.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        content.extend(f"{offset:010d} 00000 n \n".encode())
    content.extend(f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    path = tmp_path / "syllabus.pdf"
    path.write_bytes(content)
    return path


def install_mock_provider(monkeypatch, handler, retries=1):
    """Use the real SDK and HTTP event hooks, without any network traffic."""
    real_client = benchmark.genai.Client
    monkeypatch.setenv("GEMINI_API_KEY", "fake-benchmark-test-key")

    def client(**kwargs):
        options = kwargs["http_options"]
        options.client_args["transport"] = httpx.MockTransport(handler)
        options.retry_options = benchmark.types.HttpRetryOptions(
            attempts=retries, initial_delay=0.001, max_delay=0.001, jitter=0,
        )
        return real_client(**kwargs)

    monkeypatch.setattr(benchmark.genai, "Client", client)


def success_response(tokens=12):
    body = {"embeddings": [{"values": [1.0, 0.0]}]}
    if tokens is not None:
        body["usageMetadata"] = {"promptTokenCount": tokens}
    return httpx.Response(200, json=body)


def test_offline_benchmark_measures_real_extraction_chunking_and_storage(syllabus_pdf, monkeypatch):
    def unexpected_live_call(**kwargs):
        pytest.fail("Offline benchmark must never create a live client")

    monkeypatch.setattr(benchmark.genai, "Client", unexpected_live_call)
    report = benchmark_pdf(syllabus_pdf, chunk_size=100, overlap=20)
    assert report["status"] == "success"
    assert report["total_pdf_pages"] == report["readable_pages"] == 1
    assert report["chunk_statistics"]["count"] == report["stored_chunks"] > 1
    assert report["api"]["sdk_embedding_calls"] == report["api"]["http_attempts"] == 0
    assert report["api"]["simulated_embedding_calls"] == report["stored_chunks"]
    assert report["api"]["provider_input_tokens"] is None
    assert report["chunk_statistics"]["max_characters"] <= 100
    assert all(chunk["page_number"] == 1 for chunk in report["chunks"])
    assert {"validation", "extraction", "chunking", "indexing_total", "storage", "embedding_pipeline", "total"} <= report["seconds"].keys()
    assert all(seconds >= 0 for seconds in report["seconds"].values())
    assert "weekly coding" not in json.dumps(report)


def test_live_report_counts_calls_and_raw_provider_tokens(syllabus_pdf, monkeypatch):
    install_mock_provider(monkeypatch, lambda request: success_response(12))
    report = benchmark_pdf(syllabus_pdf, live=True, chunk_size=100, overlap=20)
    assert report["status"] == "success"
    count = report["stored_chunks"]
    assert report["api"]["sdk_embedding_calls"] == count
    assert report["api"]["http_attempts"] == count
    assert report["api"]["provider_input_tokens"] == count * 12
    assert report["api"]["token_usage_complete"] is True
    assert report["embedding_dimensions"] == [2]
    assert all(call["http_statuses"] == [200] for call in report["requests"])


def test_missing_usage_is_unknown_not_zero(syllabus_pdf, monkeypatch):
    install_mock_provider(monkeypatch, lambda request: success_response(None))
    report = benchmark_pdf(syllabus_pdf, live=True)
    assert report["status"] == "success"
    assert report["api"]["provider_input_tokens"] is None
    assert report["api"]["token_usage_complete"] is False
    assert report["api"]["requests_with_reported_tokens"] == 0


def test_http_retry_is_distinguished_from_sdk_call(syllabus_pdf, monkeypatch):
    attempts = []

    def handler(request):
        attempts.append(request)
        if len(attempts) == 1:
            return httpx.Response(429, json={"error": {"code": 429, "message": "Retry test", "status": "RESOURCE_EXHAUSTED"}})
        return success_response(9)

    install_mock_provider(monkeypatch, handler, retries=2)
    report = benchmark_pdf(syllabus_pdf, live=True, chunk_size=1000)
    assert report["status"] == "success"
    assert report["api"]["sdk_embedding_calls"] == 1
    assert report["api"]["http_attempts"] == 2
    assert report["requests"][0]["http_statuses"] == [429, 200]
    assert report["api"]["provider_input_tokens"] == 9


def test_provider_failure_produces_partial_report_without_private_details(syllabus_pdf, monkeypatch):
    install_mock_provider(monkeypatch, lambda request: httpx.Response(403, json={
        "error": {"code": 403, "message": "private provider failure details", "status": "PERMISSION_DENIED"}
    }))
    report = benchmark_pdf(syllabus_pdf, live=True)
    assert report["status"] == "failed"
    assert report["api"]["http_attempts"] == report["api"]["failed_sdk_calls"] == 1
    assert report["error"]["provider_status_code"] == 403
    assert "storage" not in report["seconds"]
    assert "private provider" not in json.dumps(report)


def test_invalid_pdf_causes_no_embedding_calls(tmp_path):
    path = tmp_path / "fake.pdf"
    path.write_bytes(b"not a PDF")
    report = benchmark_pdf(path, live=True)
    assert report["status"] == "failed"
    assert report["error"]["stage"] == "validation"
    assert report["api"]["http_attempts"] == 0


def test_partial_token_reporting_is_not_presented_as_complete_total():
    recorder = EmbeddingRecorder(live=True)
    recorder.calls = [
        {"provider_input_tokens": 8, "seconds": 0.1, "http_attempts": 1, "status": "success"},
        {"provider_input_tokens": None, "seconds": 0.2, "http_attempts": 1, "status": "success"},
    ]
    summary = recorder.summary()
    assert summary["provider_input_tokens"] is None
    assert summary["reported_input_tokens_subtotal"] == 8
    assert summary["token_usage_complete"] is False


def test_cli_writes_reproducible_report_without_live_calls(syllabus_pdf, tmp_path):
    output = tmp_path / "scan.json"
    script = Path(benchmark.__file__)
    environment = dict(os.environ)
    environment.pop("GEMINI_API_KEY", None)
    result = subprocess.run([sys.executable, str(script), str(syllabus_pdf), "--output", str(output)],
                            env=environment, check=True, capture_output=True, text=True, timeout=30)
    report = json.loads(output.read_text())
    console = json.loads(result.stdout)
    assert console["status"] == report["status"] == "success"
    assert console["api"]["sdk_embedding_calls"] == 0
    assert len(report["pdf_sha256"]) == 64
    assert report["settings"]["chunk_size_characters"] == 500
    assert set(report["source_sha256"]) == {"extract.py", "chunking.py", "rag_pipeline.py", "vector_store.py"}


def test_stage_timer_records_elapsed_time_even_when_stage_fails(monkeypatch):
    ticks = iter([10.0, 12.5])
    monkeypatch.setattr(benchmark, "perf_counter", lambda: next(ticks))
    report = {"seconds": {}}
    with pytest.raises(RuntimeError), benchmark.timed_stage(report, "test_stage"):
        raise RuntimeError("test failure")
    assert report == {"seconds": {"test_stage": 2.5}, "last_stage": "test_stage"}
