# CourseIQ File Map

Statuses: `known` means its purpose was explained in conversation, `parked` means it is scheduled for a later lesson, and `generated` means a tool owns it.

This map is intentionally parked-heavy. That is an honest learning backlog, not a judgment.

## Repository and Learning Workflow

| Path | Status | Why it exists |
| --- | --- | --- |
| `.git` / shared Git data | generated | Stores commits, branches, staging state, and worktree bookkeeping. Never edit manually. → [[git-snapshots-and-staging]] |
| `.gitignore` | known | Excludes secrets, dependencies, build output, and nested worktrees from commits. → [[git-snapshots-and-staging]] |
| `AGENTS.md` | known | Requires each feature or fix to use a fresh Git worktree. → [[branches-and-worktrees]] |
| `.github/prompts/grilling.prompt.md` | known | Defines the one-question-at-a-time design pressure-test used before implementation. |
| `.agents/skills/` | parked | Contains the project-local learning workflows; revisit when maintaining the learning system. |
| `skills-lock.json` | parked | Records installed project-local skill versions; revisit when updating skills. |
| `learning/project.md` | known | Records the adopted product scope, background, MVP, frozen work, and triage decision. |
| `learning/file-map.md` | known | Keeps every project area accounted for so there are no mystery boxes. |
| `learning/knowledge-graph.md` | known | Records demonstrated understanding and the dependencies between concepts. |
| `learning/plan.md` | known | Sequences visible product improvements while scheduling one existing mystery area to reclaim in each section. |
| `learning/ui-smoke-check.md` | known | Records observed two-course browser behavior, restart verification, controlled substitutions, and remaining live checks. |
| `README.md` | known | Gives humans the verified commands for installing, testing, and running the frontend and backend locally. |
| `.vscode/settings.json` | parked | Points VS Code at the project Python interpreter; reclaim during environment setup. → [[virtual-environments-and-requirements]] |
| `pytest.ini` | known | Tells pytest where backend modules and test files live; generated and toured during the smoke-test lesson. → [[automated-testing]] |

## Backend

| Path | Status | Why it exists |
| --- | --- | --- |
| `backend/main.py` | known | Receives analysis and course-ingestion uploads; validates PDFs, preserves uploaded filenames, indexes course-specific chunks, reports warnings, and cleans up temporary files. → [[fastapi-request-flow]], [[temporary-file-lifecycle]] |
| `backend/extract.py` | known | Extracts readable PDF pages without flattening their layout, records page-level warnings, and asks Gemini for validated syllabus fields. → [[pdf-text-extraction]], [[structured-ai-output]] |
| `backend/documents.py` | known | Defines validated extracted pages, document warnings, and RAG chunks with stable course and citation identity. → [[document-metadata]], [[pydantic-models]], [[document-chunk-model]] |
| `backend/chunking.py` | known | Recursively splits each extracted page, adds capped overlap, and creates globally ordered chunks with course and page citation metadata. → [[recursive-chunking]], [[document-chunk-model]] |
| `backend/vector_store.py` | known | Stores chunk records persistently and retrieves the nearest vectors within one course, returning source metadata and raw distance. → [[chromadb-collections]], [[persistent-vector-storage]] |
| `backend/benchmark_ingestion.py` | known | Measures real scan/chunk/storage stages, observes embedding calls/HTTP retries, and writes content-free JSON usage reports. → [[ingestion-performance-measurement]] |
| `backend/benchmarks/README.md` | known | Explains offline/live commands, report fields, limits, and reproducible comparisons. → [[ingestion-performance-measurement]] |
| `backend/tests/test_ingestion_benchmark.py` | known | Exercises real synthetic-PDF extraction, isolated storage, raw token metadata, retries, failures, timers and CLI reports without network calls. → [[ingestion-performance-measurement]] |
| `benchmark-results/` | generated | Git-ignored per-run JSON performance reports; can regenerate and compare using identical inputs/settings. |
| `backend/course_store.py` | known | Saves course summaries in a local SQLite catalog and lists them after restart using the shared storage directory. → [[course-catalog-persistence]] |
| `backend/rag_pipeline.py` | known | Embeds chunks and questions, retrieves course-filtered evidence, and formats source citations; borrowed chatbot functions still require integration. → [[recursive-chunking]], [[embeddings-and-vector-search]], [[course-filtered-vector-retrieval]] |
| `backend/engine.py` | parked | Applies deterministic workload rules to structured syllabus data; reclaim when category-level estimates are redesigned. → [[workload-estimation]] |
| `backend/requirements.txt` | known | Declares reproducible Python dependencies that are installed into a virtual environment. → [[virtual-environments-and-requirements]] |
| `backend/requirements-dev.txt` | known | Extends runtime requirements with reproducible development-only test dependencies; authored and revised during the smoke-test lesson. → [[automated-testing]] |
| `backend/tests/test_health.py` | known | Sends an in-process request to `/health` and verifies the status code and JSON response; its assertions were authored during the lesson. → [[automated-testing]] |
| `backend/tests/test_extract.py` | known | Proves PDF page structure, human page numbers, all-unreadable rejection, and partial-extraction warnings using controlled fake pages. → [[pdf-text-extraction]], [[test-doubles-and-monkeypatching]] |
| `backend/tests/test_documents.py` | known | Proves pages and chunks preserve source identity, serialize predictably, and reject invalid page or chunk numbers. → [[document-metadata]], [[pydantic-models]], [[document-chunk-model]] |
| `backend/tests/test_pdf_validation.py` | known | Proves filename, 10 MB boundary, and PDF-signature validation using controlled upload bytes. → [[pdf-upload-validation]], [[python-bytes]] |
| `backend/tests/test_chunking.py` | known | Tests recursive boundaries, preserved section formatting, long explanations, safe overlap, RAG compatibility, and page-to-chunk citation metadata. → [[recursive-chunking]], [[document-chunk-model]] |
| `backend/tests/test_vector_store.py` | known | Verifies persistent indexing, duplicate retries, course filtering, result bounds, and cited retrieval across separate processes. → [[chromadb-collections]] |
| `backend/tests/test_citations.py` | known | Verifies actual page numbers, filename-only citations for pageless sources, empty evidence messages, and course-filtered citation formatting. → [[source-citation-formatting]] |
| `backend/tests/test_course_upload.py` | known | Verifies upload-to-storage metadata, distinct course IDs, warnings, invalid input rejection, and cleanup after embedding failure with controlled extraction/embedding substitutes. → [[fastapi-request-flow]] |
| `backend/tests/test_course_questions.py` | known | Verifies question API course isolation, citations, input validation before embeddings, empty evidence, and provider failures. → [[question-api-validation]] |
| `backend/tests/test_course_store.py` | known | Tests unique course IDs, same-name courses, metadata updates, empty storage, and the course-list API across process restarts. → [[course-catalog-persistence]] |
| `backend/tests/test_embeddings.py` | known | Checks the embedding request model and response handling with a controlled provider substitute. |
| `backend/__init__.py` | parked | Marks the backend directory as a Python package; reclaim when imports and tests are organized. |
| `__pycache__/`, `*.pyc` | generated | Python bytecode caches; never edit and safe to regenerate. |

## Frontend

| Path | Status | Why it exists |
| --- | --- | --- |
| `frontend/src/app/page.tsx` | known | Provides Courses, Intake, and Insights tabs; mounts the saved-course workspace alongside the original workload-analysis flow. → [[frontend-course-api-integration]] |
| `frontend/src/app/CourseWorkspace.tsx` | known | Loads saved courses, uploads PDFs, selects course IDs, and displays question evidence with citations, warnings, and errors; switching courses resets answers. → [[frontend-course-api-integration]] |
| `frontend/src/app/layout.tsx` | parked | Defines shared page metadata, font setup, and root HTML layout. |
| `frontend/src/app/globals.css` | parked | Defines global visual styles. |
| `frontend/package.json` | known | Declares frontend dependencies and runnable npm scripts; the Next version was deliberately upgraded during dependency setup. → [[npm-dependency-reproducibility]] |
| `frontend/package-lock.json` | generated | Locks exact npm dependency versions; it was regenerated through npm after the deliberate Next upgrade and should not be hand-edited. → [[npm-dependency-reproducibility]] |
| `frontend/next.config.mjs`, `postcss.config.mjs`, `tailwind.config.ts`, `tsconfig.json`, `next-env.d.ts` | parked | Configure Next.js, CSS processing, Tailwind, and TypeScript; reclaim when frontend tooling becomes relevant. |
| `frontend/.env.local.example` | parked | Documents the frontend environment variable needed to reach the backend. |
| `frontend/tsconfig.tsbuildinfo` | generated | TypeScript incremental-build cache; it is ignored by Git, never hand-edited, and safe to regenerate. |
| `frontend/node_modules/`, `frontend/.next/` | generated | Installed packages and Next.js build output; never edit and safe to regenerate. |

## Data

| Path | Status | Why it exists |
| --- | --- | --- |
| `database/schema.sql` | parked | Defines planned PostgreSQL tables; reclaim when analysis becomes persistent. |
| `docs/` | parked | Intended document input area for the borrowed RAG script; replace with upload-driven ingestion. |
| `.venv/` | generated | Holds locally installed Python packages and the project interpreter; recreate from requirements instead of committing it. → [[virtual-environments-and-requirements]] |
| `.data/chroma/` | generated | Persistent Chroma files and the `courses.sqlite3` catalog; excluded from Git and retained across restarts. → [[chromadb-collections]], [[course-catalog-persistence]] |
