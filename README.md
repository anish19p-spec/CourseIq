# CourseIQ

CourseIQ is an AI-powered academic planning platform that parses syllabus PDFs, extracts structured workload signals with Gemini, and turns them into deterministic weekly workload predictions.

## Architecture

- `frontend/` - Next.js App Router + Tailwind UI for upload, profile capture, and analytics
- `backend/` - FastAPI service for PDF ingestion, Gemini extraction, and workload calculations
- `database/` - PostgreSQL schema for users, courses, syllabi, and student history

## Runtime Contract

`POST /api/courses` accepts multipart `course_name` and a PDF `file`. It indexes
readable pages under a new course ID and returns `course_id`, `course_name`,
`filename`, `chunk_count`, and extraction `warnings` with status 201. Citations
use the uploaded filename. Each request creates a separate course record.
This endpoint requires Gemini credentials; automated upload tests substitute
extraction and embeddings while using real temporary Chroma storage.

`GET /api/courses` returns saved course summaries as a JSON array. The catalog
is stored in `courses.sqlite3` inside the configured Chroma storage folder and
survives backend restarts. It records successful uploads from this version
onward; existing chunks without catalog entries are not backfilled. This local
MVP catalog is shared and does not yet implement user accounts.

The frontend opens on the Courses tab: upload a PDF, select a saved course,
and ask questions to display retrieved excerpts with citations. Courses reload
from the API when this tab opens. Intake and Insights retain the separate
workload-analysis flow. A controlled two-course Chrome check verified upload,
course switching, citations, and backend restart persistence. Extraction and
embeddings were substituted; real-PDF/live-provider checks remain pending.
See `learning/ui-smoke-check.md` for the scope and observed results.

`POST /api/courses/{course_id}/questions` accepts JSON:
`{"question": "What is homework worth?", "n_results": 5}`. Questions must be
1–2000 characters after trimming; `n_results` is an integer from 1 to 10.
The response includes `course_id`, `question`, structured `evidence`, and
`cited_evidence` excerpts. These are retrieved source excerpts, not generated
answers. No matching records returns an empty list and an explanatory message.

The frontend submits a `multipart/form-data` request to `POST /api/analyze` with:

- `course_name`
- `gpa`
- `comfort_level`
- `target_grade`
- `file` (PDF syllabus)

The backend responds with JSON similar to:

```json
{
  "course_name": "Computer Systems",
  "weekly_hours": 8.5,
  "risk_level": "Manageable",
  "student_multiplier": 1.0,
  "assignment_inventory": {
    "projects": 2,
    "midterms": 1,
    "homeworks": 6,
    "has_final_exam": true
  },
  "syllabus": {
    "course_name": "Computer Systems",
    "total_projects": 2,
    "total_midterms": 1,
    "total_homeworks": 6,
    "has_final_exam": true
  },
  "target_grade": "A-"
}
```

## Ingestion Performance Benchmark

`backend/benchmark_ingestion.py` produces stage timings, chunk statistics,
per-request latencies, API/HTTP counts and provider token usage when reported.
It defaults to offline mode; `--live` enables Gemini calls. Reports and vector
storage are isolated from saved courses. See `backend/benchmarks/README.md` for
commands, reproducibility notes and measurement limits.

## Local Setup

### Backend

Run these commands from the repository or worktree root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements-dev.txt
export GEMINI_API_KEY="your-key"
python -m pytest
python -m uvicorn main:app --reload --port 8000 --app-dir backend
```

RAG storage is created on first use in `.data/chroma/` in this checkout. Set
`COURSEIQ_CHROMA_PATH` to choose a different persistent directory. Reuse the
same directory after restarting the backend to retain indexed evidence.
Tests use temporary directories. Chroma data files are excluded from Git.

Embedding requests use `gemini-embedding-2`. Set `GEMINI_API_KEY` in the
backend environment or a worktree-root `.env` file and restart the backend.
The upload/question API returns an actionable 503 if the key is missing.
Vectors from different embedding models must not be mixed; existing older-model
indexes need a separate storage directory and reindexing when migrating models.

### Frontend

Run these commands from a second terminal at the repository or worktree root:

```bash
npm ci --prefix frontend
npm exec --prefix frontend -- tsc --noEmit --project frontend/tsconfig.json
npm run dev --prefix frontend
```

Set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` in `frontend/.env.local` when running the UI locally.

Verify the running services at:

- Frontend: `http://localhost:3000`
- Backend health: `http://localhost:8000/health`

## Feature Worktrees

Create each feature or fix from the latest `main` branch in a fresh worktree:

```bash
git pull --ff-only
git worktree add .worktrees/<task> -b feature/<task> main
```

Develop, test, commit, and push inside that worktree. After its pull request is merged, remove the worktree instead of reusing it for another task.

## Database

Apply `database/schema.sql` to a PostgreSQL database with `pgcrypto` enabled.

## Notes

- The Gemini integration uses structured output with `SyllabusData` to keep extraction deterministic.
- The workload engine is intentionally rule-based so predictions are explainable and stable.
- The uploaded PDF is always deleted after analysis, even on failures.
