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

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export GEMINI_API_KEY="your-key"
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` in `frontend/.env.local` when running the UI locally.

## Database

Apply `database/schema.sql` to a PostgreSQL database with `pgcrypto` enabled.

## Notes

- The Gemini integration uses structured output with `SyllabusData` to keep extraction deterministic.
- The workload engine is intentionally rule-based so predictions are explainable and stable.
- The uploaded PDF is always deleted after analysis, even on failures.
