"""Repeatable ingestion measurements. Offline by default; --live contacts Gemini."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
from hashlib import sha256
from importlib.metadata import version
import json
import math
import os
from pathlib import Path
import platform
from statistics import mean, median
from tempfile import TemporaryDirectory
from time import perf_counter
from types import SimpleNamespace
from unittest.mock import patch

from dotenv import load_dotenv
from google import genai
from google.genai import types

import extract
import rag_pipeline
from chunking import chunk_document
from extract import MAX_PDF_SIZE_BYTES, validate_pdf_upload


class EmbeddingRecorder:
    """Observe SDK calls and HTTP retries without persisting request content."""

    def __init__(self, live: bool = False):
        self.live = live
        self.calls: list[dict] = []
        self.current: dict | None = None
        self.clients: list = []

    def on_request(self, request):
        self.current["http_attempts"] += 1

    def on_response(self, response):
        self.current["http_statuses"].append(response.status_code)
        if not response.is_success:
            return
        response.read()
        try:
            usage = response.json().get("usageMetadata", {})
            tokens = usage.get("promptTokenCount")
            if isinstance(tokens, int) and not isinstance(tokens, bool) and tokens >= 0:
                self.current["provider_input_tokens"] = tokens
        except (ValueError, AttributeError, TypeError):
            pass

    def make_client(self):
        if self.live:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise rag_pipeline.EmbeddingConfigurationError("GEMINI_API_KEY is required for --live")
            client = genai.Client(api_key=api_key, http_options=types.HttpOptions(
                client_args={"event_hooks": {"request": [self.on_request], "response": [self.on_response]}}
            ))
            self.clients.append(client)
            target = client.models.embed_content
        else:
            def target(**kwargs):
                digest = sha256(kwargs["contents"].encode("utf-8")).digest()
                return SimpleNamespace(embeddings=[SimpleNamespace(values=[byte / 255 for byte in digest[:8]])])

        def measured_embed(**kwargs):
            call = {"number": len(self.calls) + 1, "model": kwargs["model"],
                    "input_characters": len(kwargs["contents"]), "http_attempts": 0,
                    "http_statuses": [], "provider_input_tokens": None, "status": "started"}
            self.calls.append(call)
            self.current = call
            started = perf_counter()
            try:
                response = target(**kwargs)
                call["status"] = "success"
                return response
            except Exception as error:
                call["status"] = "failed"
                call["error_type"] = type(error).__name__
                raise
            finally:
                call["seconds"] = perf_counter() - started
                self.current = None

        return SimpleNamespace(models=SimpleNamespace(embed_content=measured_embed))

    def close(self):
        for client in self.clients:
            client.close()

    def summary(self) -> dict:
        reported = [call["provider_input_tokens"] for call in self.calls if call["provider_input_tokens"] is not None]
        latencies = [call["seconds"] for call in self.calls]
        complete = self.live and bool(self.calls) and len(reported) == len(self.calls)
        return {
            "sdk_embedding_calls": len(self.calls) if self.live else 0,
            "models": sorted({call["model"] for call in self.calls if "model" in call}),
            "simulated_embedding_calls": 0 if self.live else len(self.calls),
            "http_attempts": sum(call["http_attempts"] for call in self.calls),
            "failed_sdk_calls": sum(call["status"] == "failed" for call in self.calls),
            "requests_with_reported_tokens": len(reported),
            "provider_input_tokens": sum(reported) if complete else None,
            "reported_input_tokens_subtotal": sum(reported) if reported else None,
            "token_usage_complete": complete,
            "latency_seconds": {"mean": mean(latencies), "median": median(latencies),
                                "max": max(latencies)} if latencies else None,
        }


@contextmanager
def timed_stage(report: dict, name: str):
    report["last_stage"] = name
    started = perf_counter()
    try:
        yield
    finally:
        report["seconds"][name] = perf_counter() - started


def benchmark_pdf(pdf_path: str | Path, *, live: bool = False, chunk_size: int = 500, overlap: int = 50) -> dict:
    """Measure the current sequential pipeline against isolated, fresh storage."""
    pdf_path = Path(pdf_path)
    report = {
        "schema_version": 1, "started_at": datetime.now(timezone.utc).isoformat(),
        "mode": "live" if live else "offline", "filename": pdf_path.name,
        "status": "started", "seconds": {}, "chunks": [], "warnings": [],
        "settings": {"chunk_size_characters": chunk_size, "requested_overlap_characters": overlap,
                     "embedding_execution": "sequential", "storage": "fresh temporary directory"},
        "environment": {"python": platform.python_version(), "platform": platform.platform(),
                        **{package: version(package) for package in ("google-genai", "chromadb", "pdfplumber")}},
        "source_sha256": {name: sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                          for name in ("extract.py", "chunking.py", "rag_pipeline.py", "vector_store.py")},
        "scope": "Local file validation, extraction, chunking, embeddings and Chroma writes. Excludes browser upload/network, course catalog, question answering and report writing.",
        "measurement_notes": [
            "Offline vectors and latencies do not represent Gemini performance or semantic quality.",
            "Characters divided by four is a rough token heuristic, not provider usage or a billing estimate.",
            "Missing provider usage is null, never zero; subtotals may omit unreported or failed attempts.",
            "HTTP attempts include SDK retries. Token usage reflects reported successful responses, not an invoice.",
            "Indexing total includes storage; embedding_pipeline subtracts storage. Do not sum overlapping timings.",
            "Total includes temporary storage cleanup but excludes Python imports and final client cleanup.",
            "Reports omit syllabus text, API keys, request headers and raw provider errors.",
        ],
    }
    recorder = EmbeddingRecorder(live)
    started = perf_counter()
    try:
        if chunk_size < 1 or overlap < 0:
            raise ValueError("chunk_size must be positive and overlap nonnegative")
        with timed_stage(report, "validation"):
            with pdf_path.open("rb") as source:
                content = source.read(MAX_PDF_SIZE_BYTES + 1)
            validate_pdf_upload(pdf_path.name, content)
            report["file_bytes"] = len(content)
            report["pdf_sha256"] = sha256(content).hexdigest()
        original_open = extract.pdfplumber.open

        def counted_open(*args, **kwargs):
            pdf = original_open(*args, **kwargs)
            try:
                report["total_pdf_pages"] = len(pdf.pages)
            except Exception:
                pdf.close()
                raise
            return pdf

        with timed_stage(report, "extraction"), patch.object(extract.pdfplumber, "open", counted_open):
            document = extract.extract_text_from_pdf(str(pdf_path))
        report["readable_pages"] = len(document.pages)
        report["warnings"] = document.warnings
        report["extracted_characters"] = sum(len(page.text) for page in document.pages)
        report["extracted_words"] = sum(len(page.text.split()) for page in document.pages)
        with timed_stage(report, "chunking"):
            chunks = chunk_document(document, "benchmark-course", chunk_size, overlap)
        report["chunks"] = [{"chunk_number": chunk.chunk_number, "page_number": chunk.page_number,
                             "characters": len(chunk.text), "words": len(chunk.text.split()),
                             "text_sha256": sha256(chunk.text.encode("utf-8")).hexdigest()} for chunk in chunks]
        lengths = [len(chunk.text) for chunk in chunks]
        report["chunk_statistics"] = {
            "count": len(chunks), "min_characters": min(lengths, default=0),
            "max_characters": max(lengths, default=0), "mean_characters": mean(lengths) if lengths else 0,
            "submitted_characters": sum(lengths),
            "character_expansion_ratio": sum(lengths) / report["extracted_characters"] if report["extracted_characters"] else None,
            "estimated_input_tokens_chars_div_4": sum(math.ceil(length / 4) for length in lengths),
        }
        original_store = rag_pipeline.store_chunks

        def measured_store(chunks, embeddings, path):
            report["embedding_dimensions"] = sorted({len(vector) for vector in embeddings})
            with timed_stage(report, "storage"):
                return original_store(chunks, embeddings, path)

        with TemporaryDirectory(prefix="courseiq-benchmark-") as storage:
            with timed_stage(report, "indexing_total"), \
                    patch.object(rag_pipeline, "_get_genai_client", recorder.make_client), \
                    patch.object(rag_pipeline, "store_chunks", measured_store):
                report["stored_chunks"] = rag_pipeline.index_document_chunks(chunks, storage)
        report["status"] = "success"
    except Exception as error:
        report["status"] = "failed"
        report["error"] = {"type": type(error).__name__, "stage": report.get("last_stage"),
                           "provider_status_code": getattr(error, "code", None)}
    finally:
        report["seconds"]["total"] = perf_counter() - started
        if "indexing_total" in report["seconds"]:
            report["seconds"]["embedding_pipeline"] = report["seconds"]["indexing_total"] - report["seconds"].get("storage", 0)
        report["requests"] = recorder.calls
        report["api"] = recorder.summary()
        recorder.close()
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--live", action="store_true", help="Send each chunk to Gemini; incurs provider usage")
    parser.add_argument("--env-file", type=Path, help="Read credentials from this .env without copying it")
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--overlap", type=int, default=50)
    parser.add_argument("--output", type=Path, help="Defaults to a unique timestamped JSON report")
    arguments = parser.parse_args()
    if arguments.env_file:
        load_dotenv(arguments.env_file)
    if arguments.output is None:
        arguments.output = Path("benchmark-results") / (datetime.now(timezone.utc).strftime("ingestion-%Y%m%dT%H%M%S%fZ") + ".json")
    report = benchmark_pdf(arguments.pdf, live=arguments.live, chunk_size=arguments.chunk_size, overlap=arguments.overlap)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    # The report is a generated benchmark artifact, not application source.
    arguments.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "mode": report["mode"],
                      "readable_pages": report.get("readable_pages"),
                      "chunks": report.get("chunk_statistics", {}).get("count"),
                      "chunk_statistics": report.get("chunk_statistics"),
                      "seconds": report["seconds"], "api": report["api"],
                      "report": str(arguments.output)}, indent=2))
    return 0 if report["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
