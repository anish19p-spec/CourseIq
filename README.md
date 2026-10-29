# CourseIQ

CourseIQ is an AI-powered academic planning platform that parses syllabus PDFs, extracts structured workload signals with Gemini, and turns them into deterministic weekly workload predictions.

## Architecture

- `frontend/` - Next.js App Router + Tailwind UI for upload, profile capture, and analytics
- `backend/` - FastAPI service for PDF ingestion, Gemini extraction, and workload calculations
- `database/` - planned PostgreSQL schema; it is not used by the current app

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
These earlier smoke checks used substituted extraction and embeddings.

## Student reviews

Open **Reviews** to publish a first-hand course review or browse the shared feed.
No syllabus upload is required. Students enter their school, course code,
professor, optional term, difficulty (1–5), optional weekly hours outside class,
and a 20–3,000-character comment. The form requires agreement to publish.
Reviews are anonymous and labeled unverified; accounts and moderation are not
implemented in this version. Review text is displayed as plain text.

Reviews are grouped by school and normalized course code, independently of
syllabus-upload IDs. `csce120`, `CSCE 120`, and `CSCE-120` all normalize to
`CSCE 120`; TAMU school-name aliases normalize to `Texas A&M University`.
Professor and term remain visible so readers can distinguish experiences.

- `POST /api/reviews` publishes a review with status 201. Required JSON fields:
  `course_code`, `professor_name`, `difficulty`, `body`, and
  `consent_to_publish: true`. `institution` defaults to Texas A&M University;
  `term` and `weekly_hours` are optional. The server assigns the ID, UTC date,
  source (`student_submission`), and unverified status.
- `GET /api/reviews` returns `{items, total, offset, limit}`, newest first.
  Optional filters are `course_code` and `institution`. The default page size is
  20, with a maximum of 50; `offset` starts at zero.

The `student_reviews` table lives in `courses.sqlite3` under
`COURSEIQ_CHROMA_PATH` and survives backend restarts. Visitors connected to the
same backend see the same reviews. Separate local installations have separate
databases; making the GitHub repository public does not host this service.
This feature makes no Gemini calls and does not automatically add reviews to
the RAG index or workload calculations.

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

The current app stores course summaries in local SQLite and syllabus vectors in
ChromaDB under `COURSEIQ_CHROMA_PATH`; PostgreSQL is not required to run it.
`database/schema.sql` is a future schema proposal and is not connected to the
current runtime.

## Notes

- The Gemini integration uses structured output with `SyllabusData` to keep extraction deterministic.
- The workload engine is intentionally rule-based so predictions are explainable and stable.
- The uploaded PDF is always deleted after analysis, even on failures.
