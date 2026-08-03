# CourseIQ

CourseIQ is an AI-powered academic planning platform that parses syllabus PDFs, extracts structured workload signals with Gemini, and turns them into deterministic weekly workload predictions.

## Architecture

- `frontend/` - Next.js App Router + Tailwind UI for upload, profile capture, and analytics
- `backend/` - FastAPI service for PDF ingestion, Gemini extraction, and workload calculations
- `database/` - PostgreSQL schema for users, courses, syllabi, and student history

## Runtime Contract

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
