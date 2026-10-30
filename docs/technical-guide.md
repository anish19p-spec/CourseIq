# CourseIQ technical guide

See the [README](../README.md) for the short installation instructions.

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

The frontend opens on **My courses**. Choose **Add course** to upload a PDF
(up to 10 MB) through the single saved-course flow, then set subject comfort
and estimate workload from the saved syllabus. Each new upload automatically
requests a Gemini workload estimate with neutral subject comfort (5/10) and no
GPA adjustment. Saving and estimating are separate: if estimation fails, the
course remains saved and can be estimated again without re-uploading. There is no separate Intake
upload or temporary Insights screen. The dashboard stays mounted when switching
to reviews so an active upload is not discarded. Saved courses load from the
API when the dashboard mounts. A controlled two-course Chrome check verified upload,
course switching, citations, and backend restart persistence. Extraction and
embeddings were substituted; real-PDF/live-provider checks remain pending.
The saved-course workload controls described below reuse indexed syllabi.
The combined review/workload browser flow was also checked with isolated synthetic
data; see [dashboard verification](dashboard-verification.md) for its scope.

## Workload estimates

The **Projected weekly total** tracker sums saved course estimates and updates
after uploads and profile changes. Provisional outside-class bands are **Small**
(under 15 hours), **Medium** (15–under 30), and **Large** (30+). Unestimated courses
are counted as pending, not zero; missing category details keep the total partial.
The tracker does not make Gemini calls when loaded or refreshed.

For complete listed-activity estimates across all saved courses, workload-fit
ratings are 3/3 (total <15 and course <5 hours), 2/3 (total >=15 or course >=5),
or 1/3 (total >=30 or course >=9). Lower ratings suggest planning carefully or
considering a lighter alternative. These are uncalibrated workload-only heuristics,
not student-review ratings, measured difficulty, or academic suitability advice.
The displayed without-course total shows the marginal impact of each course.
All saved courses on this shared installation are included; accounts, term
filtering, and personal time budgets are not implemented yet. Scheduled class
time and unstated study time are not included.

Select a saved course and choose **Estimate and save workload**. The first estimate
reads its indexed excerpts with Gemini (`gemini-2.5-flash`) and saves the extracted
facts and student profile in SQLite. Profile updates reuse those facts. Selecting
**Re-read syllabus with Gemini** explicitly requests another extraction. Loading
the dashboard and comparing courses make no AI calls or new embeddings.
Structured extraction uses Gemini 2.5 Flash with `thinking_budget=0` to reduce
optional reasoning work during fact extraction; the JSON schema and validation
still apply. Difficult syllabi may need a higher budget, so extraction quality
should be checked alongside latency when adjusting this setting.
If a category count is omitted but a positive course-wide count is available,
the engine reuses it only when exactly one activity category matches. Explicit
category counts remain unchanged, and ambiguous totals stay unknown.
See [the workload extraction timing comparison](../backend/benchmarks/workload-extraction.md)
for measured latency, token usage, and the observed extraction-quality tradeoff.

- `POST /api/courses/{course_id}/workload` accepts `{"comfort_level": 5, "gpa": 0}`;
  optional `"refresh": true` re-extracts the saved syllabus.
- `GET /api/workload/schedule` reloads saved estimates, the total known weekly
  hours, and each course's percentage of that known total.
- `POST /api/workload/schedule` compares already-extracted data without saving it;
  its `courses` list contains distinct `course_id`, `syllabus`, and profile fields.

For each activity, weekly hours = assignments per week × hours per assignment ×
student adjustment. Explicit weekly frequency takes precedence; otherwise a
semester count is divided by the stated term length (default: 14 weeks).
Submission cadence is retained separately: "submitted weekly" alone does not
establish how many assignments occur per week.
Syllabus-stated hours take precedence over provisional defaults: 3 hours per
homework, 12 per project, 8 per exam, and 10 per final exam. Other activity types
remain unknown unless a time requirement is stated. These defaults, the existing
comfort/GPA adjustment, and the 5/9-hour intensity thresholds are uncalibrated
product assumptions, not measured class difficulty.

Grade weights show grading importance separately from time. Course type and level
are saved as context for later calibration; no subject-specific multipliers have
been validated. When credits are available, a separate 2–3 study-hours-per-credit
planning range links to [TAMU Academic Success Center guidance](https://asc.tamu.edu/courses-presentations/ten-tips.html).
It is not added to the activity estimate.

Unknown activity time stays `null`. A partial total is labeled a known subtotal;
shares are percentages of known workload. `estimate_complete` means all listed
categories can be estimated and no skipped-page warning is present; it does not
prove that the syllabus describes all study time. Legacy aggregate counts remain
supported but are flagged as partial because their missing values were recorded
as zero. Saved estimates survive restarts. Accounts and per-user ownership are
still pending; this dashboard is shared by the local installation.

`backend/tests/fixtures/csce120_workload_facts.json` contains manually reviewed
numeric facts from one summer syllabus, with its file hash and reviewed pages.
It tests the 10-week term and missing category data without distributing the PDF
or contacting Gemini. This is an engine regression case, not validation of live
AI extraction quality.

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

The legacy `POST /api/analyze` endpoint accepts a `multipart/form-data` request with (the current dashboard uses saved-course endpoints instead):

- `course_name`
- `gpa`
- `comfort_level`
- `target_grade`
- `file` (PDF syllabus)

The backend responds with JSON similar to:

```json
{
  "course_name": "Computer Systems",
  "weekly_hours": 3.0,
  "estimate_complete": true,
  "risk_level": "Low Risk",
  "student_multiplier": 1.0,
  "category_estimates": [{
    "category": "Homework",
    "grade_weight_percent": 40,
    "weekly_frequency": 1,
    "hours_per_assignment": 3,
    "hours_basis": "provisional_default",
    "weekly_hours": 3
  }],
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
cp -n backend/.env.example backend/.env
# Edit backend/.env and replace the placeholder with your own key.
python -m pytest
python -m uvicorn main:app --reload --port 8000 --app-dir backend --env-file backend/.env
```

RAG storage is created on first use in `.data/chroma/` in this checkout. Set
`COURSEIQ_CHROMA_PATH` to choose a different persistent directory. Reuse the
same directory after restarting the backend to retain indexed evidence.
Tests use temporary directories. Chroma data files are excluded from Git.

Embedding requests use `gemini-embedding-2`. Set `GEMINI_API_KEY` in the
backend environment or `backend/.env` and restart the backend. The startup command
above explicitly loads `backend/.env`; existing environment variables take precedence.
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
