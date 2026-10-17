# Initial syllabus ingestion benchmark

Measures the existing sequential pipeline before optimizing it. Uses real
pdfplumber extraction, recursive page-aware chunking and temporary Chroma storage.
This is a standalone diagnostic command; website responses are unchanged.

## Run

This feature lives in `.worktrees/ingestion-benchmark` on
`feature/ingestion-benchmark`. It was created from `main` and carries a copy of
the current uncommitted ingestion source because this benchmark depends on it.
The original `.worktrees/rag-ingestion` checkout, its secrets and database are
untouched. Review inherited ingestion changes separately when committing.

From the benchmark worktree root, reuse the existing Python environment:

```bash
../rag-ingestion/.venv/bin/python backend/benchmark_ingestion.py /absolute/path/syllabus.pdf
```

The default is **offline**: zero provider calls, deterministic fake vectors, real
extraction/chunking/storage. Its timings do not describe AI performance.

For an initial live scan (one run, each chunk sent to Gemini):

```bash
../rag-ingestion/.venv/bin/python backend/benchmark_ingestion.py /absolute/path/syllabus.pdf --live --env-file ../rag-ingestion/.env
```

Live mode incurs normal Gemini usage and sends the extracted text to Gemini.
It retains the current model and one SDK call per chunk behavior. A new client
is created per chunk, as in the current app. HTTP hooks observe retries and raw
response usage metadata; clients close after timing finishes. There are no
extra `count_tokens` requests, and the benchmark does not tune concurrency,
caching, batching, or retry defaults.

Reports are saved under `benchmark-results/` with unique UTC timestamps. Use
`--output benchmark-results/baseline.json` for an explicit output filename.
The directory is Git-ignored. `--chunk-size 500 --overlap 50` selects the same
default settings as the upload path. The temporary vector database is removed
after each run; existing courses are never indexed or deleted by the benchmark.

## Read the report

| Field | Meaning |
| --- | --- |
| `seconds.extraction` | Parsing the PDF and extracting readable pages, including page-count observation |
| `seconds.chunking` | Local recursive chunking only |
| `seconds.embedding_pipeline` | Creating clients, sequential embedding calls and response validation; excludes storage |
| `seconds.storage` | Opening a fresh Chroma database and upserting all chunk records |
| `seconds.indexing_total` | Embedding pipeline plus storage; do not add it to those component times |
| `seconds.total` | Local pipeline wall time including temporary storage cleanup; excludes imports, final client cleanup and report writing |
| `api.sdk_embedding_calls` | Calls to the embedding SDK method in live mode |
| `api.http_attempts` | Actual outgoing attempts, including automatic retries and failed requests |
| `api.provider_input_tokens` | Total only when every SDK call supplied usage; otherwise `null` |
| `api.reported_input_tokens_subtotal` | Sum of available token measurements when reporting is incomplete |
| `api.requests_with_reported_tokens` | Coverage of token usage reporting |
| `requests` | Per-call latency, character count, model, HTTP statuses and usage; no input text |
| `chunk_statistics` | Chunk count, length statistics, total characters sent, and character expansion ratio |
| `chunks` | Chunk number, real page number, length and text fingerprint |
| `pdf_sha256` / `source_sha256` | Fingerprints for matching input and implementation across runs |
| `environment` | Python/platform and installed package versions |

Character expansion includes overlap and splitter formatting; it is not a pure
overlap percentage. `estimated_input_tokens_chars_div_4` is a rough heuristic,
not measured tokens, exact tokenization, or cost. The installed SDK drops raw
embedding `usageMetadata`, so the benchmark reads `promptTokenCount` in an HTTP
response hook before SDK conversion. Missing metadata stays unknown. Usage
reported for successful attempts is not a full billing statement; retries that
fail may have unreported usage. Embedding vectors do not have generated-answer
completion tokens. No dollar cost is inferred.

On a provider or extraction failure, the JSON retains completed timings and
request attempts, marks `status=failed`, and the CLI exits with status 1. It
records error type/status instead of raw provider messages or credentials.
Reports omit the syllabus text, but retain its filename, fingerprints and counts.

## Reproducibility

Start with one live run to locate the bottleneck. Then run the same PDF three
times using identical chunk settings and compare median stage times, SDK calls,
HTTP attempts and reported tokens. Keep the JSON reports. Network latency and
provider retries vary, and even fresh database runs can use warm filesystem
caches. Never compare offline fake-embedding latency to live API latency.

Extraction is local; this benchmark covers the `/api/courses` ingestion work,
not the legacy `/api/analyze` structured-generation call, browser upload time,
course catalog writes or answering questions.

## Verification

```bash
../rag-ingestion/.venv/bin/python -m pytest backend/tests/test_ingestion_benchmark.py -q
```

Tests use a deterministic valid PDF and real extraction/storage. Mocked HTTP
responses pass through the real SDK transport and hooks, covering known tokens,
missing tokens, retries, failed calls, offline isolation, timers and JSON output.
No live provider calls run in pytest. The complete inherited suite plus the new
tests passes (68 tests).

Reference: [Gemini embedding usage metadata](https://ai.google.dev/api/embeddings#EmbeddingUsageMetadata).
