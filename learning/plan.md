# CourseIQ Learning and Build Plan

## Product Direction

CourseIQ helps students compare class difficulty and understand professor feedback before planning their schedule. The plan builds syllabus-based evidence first, then persistence and external student-review evidence.

## Inherited Decisions

| Decision | Current understanding | Revisit |
| --- | --- | --- |
| Python backend | Practicing: can explain that it receives syllabus data, runs extraction and workload logic, and returns results. | Throughout backend sections |
| FastAPI HTTP layer | Practicing: can explain that browser uploads need an HTTP endpoint around Python functions. | Section 5 |
| Next.js frontend | Practicing: can explain that it owns upload controls and displays backend results. | Section 5 |
| Next.js dependency line | Next 15.5.22 installed as a maintained backport; its Sharp 0.34.5 dependency still has a known advisory, so a deliberate Next 16 compatibility upgrade is required before deployment rather than a forced audit rewrite. | Section 5 |
| Gemini SDK | Fuzzy: existing code calls Gemini directly for structured extraction and generation. | Sections 4 and 6 |
| ChromaDB vector store | Conceptually familiar but not yet demonstrated through code. | Section 4 |
| PostgreSQL schema | Introduced: understands that a schema defines places and rules for records rather than storing the records itself. | Section 7 |
| Git branches, worktrees, and pull requests | Practicing: created the RAG worktree and can reconstruct the worktree command. | Every section |

## Section 1 — Make the Ground Solid

**Deliverable:** Your project can never be lost again: the app has a verified baseline, Git and GitHub are connected, the learning artifacts are committed, and the feature environment can run tests from its own worktree.

**Payload receipt:** Required foundation for adopting an unversioned AI-generated project; Git initialization and the first worktree were completed during adoption.

**Reclaim exactly one:** `README.md` — verify its setup instructions against the real frontend and backend startup commands, correct drift, and explain the complete local run path.

### Tasks

- [x] Create the worktree-specific Python environment, install declared backend dependencies, and verify backend imports.
- [x] Add a minimal automated-test setup and a backend smoke test.
- [x] Install the frontend dependencies in the worktree and verify a type check.
- [x] Run the frontend and backend together and verify the health path from the browser.
- [x] Reclaim and correct `README.md`, then commit the learning foundation and verified setup.

## Section 2 — Extract Trustworthy Documents

**Deliverable:** Given a text-based PDF, TXT, or DOCX syllabus, CourseIQ returns a common list of document pages with clean text, filename, page number when available, and clear errors for unsupported or unreadable files.

**Payload receipt:** Requested directly for the first RAG implementation; PDF is primary, with TXT and DOCX included now and OCR postponed.

**Reclaim exactly one:** `backend/extract.py` — explain its current PDF loop, break an extraction case deliberately, predict the failure, and replace the flatten-to-one-string behavior with tested document adapters.

## Section 3 — Chunk Syllabi Without Losing Their Structure

**Deliverable:** Extracted pages become deterministic, recursively split chunks that preserve headings, page citations, course identity, and safe overlap behavior.

**Payload receipt:** Requested recursive chunking, revised through grilling to use section-aware splitting because syllabus order alone does not encode importance.

**Reclaim exactly one:** `backend/rag_pipeline.py::chunk_text` — explain its boundary logic, reproduce the non-advancing overlap bug, and replace it with validated recursive chunking.

## Section 4 — Retrieve Relevant, Citable Syllabus Evidence

**Deliverable:** A question retrieves the most relevant chunks from the correct uploaded course and returns filename/page citations; indexed content survives a normal backend restart.

**Payload receipt:** Requested syllabus RAG with simple sources; persistence is required so multiple uploaded courses are not lost between requests.

**Reclaim exactly one:** `backend/rag_pipeline.py` collection and search setup — explain embedding, storage, distance, and metadata behavior, break one retrieval assumption, and rebuild it with tests.

## Section 5 — Upload and Compare Multiple Courses

**Deliverable:** A student can upload multiple syllabi through the UI, ask syllabus questions, select the intended course, and see cited answers.

**Payload receipt:** Requested multiple syllabus/class uploads and workload comparison.

**Reclaim exactly one:** `backend/main.py` — trace one upload from browser to cleanup, break content-type validation deliberately, and replace the single-PDF handoff with the tested ingestion interface.

## Section 6 — Estimate Explainable Category Workload

**Deliverable:** Each course shows category-level estimated weekly hours and intensity using grading weight, course level, credit hours, course type, assignment count, and weekly frequency; the schedule also shows each course's relative share.

**Payload receipt:** Requested temporary syllabus-based estimates until external review evidence can calibrate them.

**Reclaim exactly one:** `backend/engine.py` — explain every current workload rule, break one input assumption, and replace it with transparent category-level calculations and tests.

## Section 7 — Add Accounts and Saved Course Plans

**Deliverable:** Students can create accounts, sign in, save uploaded courses and analyses, and retrieve their own plans after restarting the application.

**Payload receipt:** Requested as a later feature; the repository already contains an unused PostgreSQL schema.

**Reclaim exactly one:** `database/schema.sql` — explain its tables and relationships, test one constraint failure, and revise it for accounts, ownership, courses, source documents, and analyses.

## Section 8 — Calibrate With External Student Evidence

**Deliverable:** Approved Reddit and professor-review inputs enter the same document model, retrieve through source-aware hybrid search, and visibly distinguish reported experiences from CourseIQ estimates.

**Payload receipt:** Requested as the long-term completion of difficulty and professor-review analysis; deferred until syllabus retrieval is reliable.

**Reclaim exactly one:** `.env.local.example` and the external-service configuration boundary — explain what may safely be public, test a missing configuration value, and document source credentials without exposing secrets.
