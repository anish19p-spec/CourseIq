# CourseIQ Knowledge Graph

Statuses progress as `seed → introduced → practicing → understood`. A concept cannot become `understood` on the day it is introduced.

## [[git-snapshots-and-staging]]

- status: practicing
- depends-on: none
- introduced: 2026-07-31
- last-reviewed: 2026-08-02
- evidence: Explained that `git add` queues changes until commit, distinguished untracked files from tracked diffs, predicted that newly staged files use `A`, and read the staged status correctly.

## [[branches-and-worktrees]]

- status: practicing
- depends-on: [[git-snapshots-and-staging]]
- introduced: 2026-07-31
- last-reviewed: 2026-07-31
- evidence: Correctly constructed a worktree command from a folder, branch name, and `main` base, then explained that edits stay isolated.

## [[git-remotes-and-push]]

- status: practicing
- depends-on: [[git-snapshots-and-staging]]
- introduced: 2026-07-31
- last-reviewed: 2026-07-31
- evidence: Correctly predicted that push uploads committed files rather than every local file.

## [[virtual-environments-and-requirements]]

- status: practicing
- depends-on: none
- introduced: 2026-07-31
- last-reviewed: 2026-08-01
- evidence: Explained that `requirements.txt` says what packages to install into `.venv`, predicted the worktree interpreter path, installed the declared packages, and verified imports in the isolated environment.

## [[python-module-imports]]

- status: introduced
- depends-on: [[virtual-environments-and-requirements]], [[python-control-flow]]
- introduced: 2026-08-01
- last-reviewed: 2026-08-01
- evidence: Needed help distinguishing module import-time setup from calling Gemini functions, then successfully verified the real backend imports.

## [[rag-retrieval-generation]]

- status: practicing
- depends-on: [[embeddings-and-vector-search]], [[document-metadata]]
- introduced: 2026-07-31
- last-reviewed: 2026-08-01
- evidence: Explained that retrieval avoids broad, costly whole-document prompting and provides a designed basis for relevant answers.

## [[pdf-text-extraction]]

- status: introduced
- depends-on: [[python-control-flow]]
- introduced: 2026-07-31
- last-reviewed: 2026-08-01
- evidence: Correctly identified that flattening whitespace can erase boundaries between homework, exam, and other syllabus sections.

## [[document-adapters]]

- status: introduced
- depends-on: [[pdf-text-extraction]], [[document-metadata]]
- introduced: 2026-07-31
- last-reviewed: 2026-07-31
- evidence: No independent explanation yet; introduced through the PDF, TXT, DOCX, Reddit, and RMP source-boundary discussion.

## [[document-metadata]]

- status: introduced
- depends-on: none
- introduced: 2026-07-31
- last-reviewed: 2026-07-31
- evidence: Chose filename and page number as the first citation metadata.

## [[recursive-chunking]]

- status: introduced
- depends-on: [[pdf-text-extraction]]
- introduced: 2026-07-31
- last-reviewed: 2026-08-01
- evidence: Explained that overlap supplies additional boundary context; needed help identifying duplicate retrieval costs and the non-advancing-loop edge case.

## [[embeddings-and-vector-search]]

- status: seed
- depends-on: [[recursive-chunking]]
- introduced: not yet
- last-reviewed: not yet
- evidence: Prior familiarity was self-reported but has not yet been demonstrated through a probe.

## [[chromadb-collections]]

- status: seed
- depends-on: [[embeddings-and-vector-search]], [[document-metadata]]
- introduced: not yet
- last-reviewed: not yet
- evidence: Prior familiarity was self-reported but has not yet been demonstrated through a probe.

## [[python-control-flow]]

- status: introduced
- depends-on: none
- introduced: 2026-07-31
- last-reviewed: 2026-07-31
- evidence: Correctly explained why a temporary path begins empty; needed help with `finally` cleanup and returned-empty versus raised-error behavior.

## [[temporary-file-lifecycle]]

- status: introduced
- depends-on: [[python-control-flow]], [[fastapi-request-flow]]
- introduced: 2026-07-31
- last-reviewed: 2026-07-31
- evidence: No independent explanation yet; introduced through the upload cleanup walkthrough.

## [[fastapi-request-flow]]

- status: practicing
- depends-on: [[python-control-flow]]
- introduced: 2026-08-01
- last-reviewed: 2026-08-01
- evidence: Explained that without a web framework the frontend would have no upload path into the Python functions.

## [[frontend-backend-boundary]]

- status: practicing
- depends-on: [[fastapi-request-flow]]
- introduced: 2026-08-01
- last-reviewed: 2026-08-02
- evidence: Explained that the frontend owns controls, uploading, and results display while the backend owns file and workload logic; then identified the frontend UI and backend health response in the browser.

## [[development-servers-and-ports]]

- status: practicing
- depends-on: [[frontend-backend-boundary]], [[fastapi-request-flow]]
- introduced: 2026-08-02
- last-reviewed: 2026-08-02
- evidence: Ran Next.js and Uvicorn concurrently, identified their separate ports, explained that a second process on port 3000 would fail because it was occupied, and stopped both processes cleanly.

## [[database-schema-and-records]]

- status: introduced
- depends-on: none
- introduced: 2026-08-01
- last-reviewed: 2026-08-01
- evidence: Explained that adding a schema column creates a place for a value rather than saving every user's value.

## [[structured-ai-output]]

- status: seed
- depends-on: [[pydantic-models]]
- introduced: not yet
- last-reviewed: not yet
- evidence: Not yet probed.

## [[pydantic-models]]

- status: seed
- depends-on: [[python-types]]
- introduced: not yet
- last-reviewed: not yet
- evidence: Not yet probed.

## [[python-types]]

- status: seed
- depends-on: none
- introduced: not yet
- last-reviewed: not yet
- evidence: Not yet probed.

## [[workload-estimation]]

- status: introduced
- depends-on: [[structured-ai-output]]
- introduced: 2026-07-31
- last-reviewed: 2026-07-31
- evidence: Defined intensity as absolute weekly hours and relative share across multiple uploaded courses, with category-level estimates.

## [[automated-testing]]

- status: practicing
- depends-on: [[python-control-flow]]
- introduced: 2026-08-01
- last-reviewed: 2026-08-01
- evidence: Authored status-code and JSON assertions, learned that one test can contain multiple assertions, ran pytest, and reported one clean passing test.

## [[http-test-client]]

- status: introduced
- depends-on: [[fastapi-request-flow]], [[automated-testing]]
- introduced: 2026-08-01
- last-reviewed: 2026-08-01
- evidence: Asked how the response API is known, distinguished `status_code` as an attribute from `json()` as a method, and predicted that TestClient would select the supported transport without test rewrites.

## [[npm-dependency-reproducibility]]

- status: introduced
- depends-on: [[git-snapshots-and-staging]]
- introduced: 2026-08-02
- last-reviewed: 2026-08-02
- evidence: Installed from the lock file, deliberately changed the requested Next version, and updated the installed tree and lock file rather than using a forced audit rewrite.

## [[typescript-type-checking]]

- status: practicing
- depends-on: [[frontend-backend-boundary]]
- introduced: 2026-08-02
- last-reviewed: 2026-08-02
- evidence: Correctly predicted that a successful no-emit type check would print nothing, recognized the first command produced help rather than results, and reported a silent successful project check.
