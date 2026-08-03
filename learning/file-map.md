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
| `README.md` | parked | Gives humans the current setup and architecture overview; reclaim when the documented workflow changes. |
| `.vscode/settings.json` | parked | Points VS Code at the project Python interpreter; reclaim during environment setup. → [[virtual-environments-and-requirements]] |
| `pytest.ini` | known | Tells pytest where backend modules and test files live; generated and toured during the smoke-test lesson. → [[automated-testing]] |

## Backend

| Path | Status | Why it exists |
| --- | --- | --- |
| `backend/main.py` | parked | Receives HTTP uploads, calls extraction and analysis, returns JSON, and cleans up temporary files; reclaim during API integration. → [[fastapi-request-flow]], [[temporary-file-lifecycle]] |
| `backend/extract.py` | known | Converts a PDF into text and asks Gemini for validated syllabus fields; its current whitespace cleanup loses useful structure. → [[pdf-text-extraction]], [[structured-ai-output]] |
| `backend/rag_pipeline.py` | known | Demonstrates chunking, embeddings, Chroma retrieval, and answer generation; it is borrowed reference code that will be replaced or reclaimed in tested pieces. → [[recursive-chunking]], [[embeddings-and-vector-search]] |
| `backend/engine.py` | parked | Applies deterministic workload rules to structured syllabus data; reclaim when category-level estimates are redesigned. → [[workload-estimation]] |
| `backend/requirements.txt` | known | Declares reproducible Python dependencies that are installed into a virtual environment. → [[virtual-environments-and-requirements]] |
| `backend/requirements-dev.txt` | known | Extends runtime requirements with reproducible development-only test dependencies; authored and revised during the smoke-test lesson. → [[automated-testing]] |
| `backend/tests/test_health.py` | known | Sends an in-process request to `/health` and verifies the status code and JSON response; its assertions were authored during the lesson. → [[automated-testing]] |
| `backend/__init__.py` | parked | Marks the backend directory as a Python package; reclaim when imports and tests are organized. |
| `__pycache__/`, `*.pyc` | generated | Python bytecode caches; never edit and safe to regenerate. |

## Frontend

| Path | Status | Why it exists |
| --- | --- | --- |
| `frontend/src/app/page.tsx` | parked | Implements the main upload and analysis interface; reclaim when multi-course uploads are connected. |
| `frontend/src/app/layout.tsx` | parked | Defines shared page metadata, font setup, and root HTML layout. |
| `frontend/src/app/globals.css` | parked | Defines global visual styles. |
| `frontend/package.json` | known | Declares frontend dependencies and runnable npm scripts; the Next version was deliberately upgraded during dependency setup. → [[npm-dependency-reproducibility]] |
| `frontend/package-lock.json` | generated | Locks exact npm dependency versions; it was regenerated through npm after the deliberate Next upgrade and should not be hand-edited. → [[npm-dependency-reproducibility]] |
| `frontend/next.config.mjs`, `postcss.config.mjs`, `tailwind.config.ts`, `tsconfig.json`, `next-env.d.ts` | parked | Configure Next.js, CSS processing, Tailwind, and TypeScript; reclaim when frontend tooling becomes relevant. |
| `frontend/.env.local.example` | parked | Documents the frontend environment variable needed to reach the backend. |
| `frontend/tsconfig.tsbuildinfo` | generated | TypeScript incremental-build cache; it is currently tracked but should eventually be removed from Git and ignored. |
| `frontend/node_modules/`, `frontend/.next/` | generated | Installed packages and Next.js build output; never edit and safe to regenerate. |

## Data

| Path | Status | Why it exists |
| --- | --- | --- |
| `database/schema.sql` | parked | Defines planned PostgreSQL tables; reclaim when analysis becomes persistent. |
| `docs/` | parked | Intended document input area for the borrowed RAG script; replace with upload-driven ingestion. |
| `.venv/` | generated | Holds locally installed Python packages and the project interpreter; recreate from requirements instead of committing it. → [[virtual-environments-and-requirements]] |
