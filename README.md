# CourseIQ

CourseIQ analyzes course syllabi to help students estimate weekly workload and plan their schedules.

## Features

- Upload text-based syllabus PDFs and retrieve source passages with page citations.
- Estimate weekly hours with Gemini-extracted facts and adjustable subject comfort.
- Track combined course hours, workload bands, and provisional workload-fit ratings.
- Publish and browse anonymous, unverified student course reviews.

## Run from source

Requires Python, Node.js, npm, and a Gemini API key.

### Install

```bash
git clone https://github.com/anish19p-spec/CourseIq.git
cd CourseIq
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
npm ci --prefix frontend
cp -n backend/.env.example backend/.env
```

### Configure your API key

Open `backend/.env` and replace the placeholder with your own key:

```dotenv
GEMINI_API_KEY=your_gemini_api_key
```

This file is ignored by Git. Keep the key on the backend; never put it in frontend code or a `NEXT_PUBLIC_` variable.

### Start the backend

From the repository root, with the virtual environment activated:

```bash
python -m uvicorn main:app --reload --port 8000 --app-dir backend --env-file backend/.env
```

Restart the backend after changing the key. Health check: <http://localhost:8000/health>.

### Start the frontend

In a second terminal, from the repository root:

```bash
npm run dev --prefix frontend
```

Open the local URL printed in that terminal, usually <http://localhost:3000>. Keep both servers running.

## Storage and limitations

Data stays locally in `.data/chroma/` using SQLite and ChromaDB; original PDFs are not retained. Accounts and private per-student storage are not implemented.

Workload estimates and ratings are provisional, not academic recommendations. Uploads and estimates use your Gemini quota; reading saved totals does not.

## Development

See the [technical guide](docs/technical-guide.md) for architecture, API details, tests, and benchmarks.
