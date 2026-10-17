# CourseIQ Knowledge Graph

Statuses progress as `seed → introduced → practicing → understood`. A concept cannot become `understood` on the day it is introduced.

## [[git-snapshots-and-staging]]

- status: understood
- depends-on: none
- introduced: 2026-07-31
- last-reviewed: 2026-09-03
- evidence: After a month, independently recalled that `git add` queues the current changes, `git commit` creates the local snapshot that can be pushed, and then staged the full PDF checkpoint correctly.

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

- status: practicing
- depends-on: [[python-control-flow]]
- introduced: 2026-07-31
- last-reviewed: 2026-08-15
- evidence: Summarized that the revised extractor records document warnings when a page is skipped, then ran the seven-test suite successfully.

## [[extraction-error-policy]]

- status: practicing
- depends-on: [[pdf-text-extraction]], [[document-metadata]]
- introduced: 2026-08-14
- last-reviewed: 2026-08-15
- evidence: Chose to retain readable pages while reporting failed page numbers, correctly expected pages 1 and 3 when page 2 failed, and summarized the resulting behavior.

## [[pdf-upload-validation]]

- status: practicing
- depends-on: [[pdf-text-extraction]], [[extraction-error-policy]]
- introduced: 2026-08-17
- last-reviewed: 2026-08-18
- evidence: Explained that a renamed file is not a true PDF, chose a 10 MB limit and HTTP 400 for malformed input, set the exact one-byte-over boundary, and ran the twelve-test suite successfully.

## [[python-bytes]]

- status: introduced
- depends-on: [[python-types]]
- introduced: 2026-08-17
- last-reviewed: 2026-08-18
- evidence: Initially described the PDF signature as a raw file, then used a provided bytes literal to model plain-text upload contents; no independent explanation yet.

## [[exception-mapping]]

- status: practicing
- depends-on: [[pdf-upload-validation]], [[fastapi-request-flow]]
- introduced: 2026-08-18
- last-reviewed: 2026-08-18
- evidence: Chose HTTP 400 for invalid and malformed PDFs, predicted the malformed test would fail before parser-error conversion, and requested a specific no-text-found message.

## [[async-await]]

- status: introduced
- depends-on: [[fastapi-request-flow]]
- introduced: 2026-08-15
- last-reviewed: 2026-08-15
- evidence: Asked what `async` means while reviewing the upload endpoint; no independent explanation yet.

## [[test-doubles-and-monkeypatching]]

- status: introduced
- depends-on: [[automated-testing]], [[python-module-imports]]
- introduced: 2026-08-03
- last-reviewed: 2026-08-03
- evidence: Asked what `MagicMock` means and used a provided fake-page test, but has not yet explained test isolation independently.

## [[document-adapters]]

- status: introduced
- depends-on: [[pdf-text-extraction]], [[document-metadata]]
- introduced: 2026-07-31
- last-reviewed: 2026-07-31
- evidence: No independent explanation yet; introduced through the PDF, TXT, DOCX, Reddit, and RMP source-boundary discussion.

## [[document-metadata]]

- status: practicing
- depends-on: none
- introduced: 2026-07-31
- last-reviewed: 2026-09-27
- evidence: Chose a stable generated course ID, distinguished professor-specific offerings as separate records, and filled the document-wide chunk number in a tested model.

## [[document-chunk-model]]

- status: practicing
- depends-on: [[document-metadata]], [[pydantic-models]], [[recursive-chunking]]
- introduced: 2026-09-27
- last-reviewed: 2026-09-30
- evidence: Connected chunks to recursive splitting, corrected document-wide numbering from list length to length plus one after guidance, and ran the full 21-test suite successfully.

## [[recursive-chunking]]

- status: practicing
- depends-on: [[pdf-text-extraction]]
- introduced: 2026-07-31
- last-reviewed: 2026-10-08
- evidence: Recalled that overlap preserves context between chunks, wired the legacy RAG entry point to the recursive splitter, and ran the full 22-test suite successfully.

## [[process-isolation-in-tests]]

- status: introduced
- depends-on: [[automated-testing]], [[python-control-flow]]
- introduced: 2026-09-27
- last-reviewed: 2026-09-27
- evidence: Asked whether the child-process timeout checks an infinite loop and explained that one test covers character overlap while the other covers overlap equal to chunk size.

## [[embeddings-and-vector-search]]

- status: practicing
- depends-on: [[recursive-chunking]]
- introduced: 2026-10-09
- last-reviewed: 2026-10-09
- evidence: Explained that embeddings let retrieval compare wording similarity for contextual meaning.

## [[chromadb-collections]]

- status: introduced
- depends-on: [[embeddings-and-vector-search]], [[document-metadata]]
- introduced: 2026-10-09
- last-reviewed: 2026-10-09
- evidence: Used Chroma's `is_persistent` setting to characterize the borrowed client as memory-only and ran the 23-test suite successfully.

## [[frontend-course-api-integration]]

- status: introduced
- depends-on: [[frontend-backend-boundary]], [[question-api-validation]]
- introduced: 2026-10-16
- last-reviewed: 2026-10-16
- evidence: React component state, effects, course-key resets, API requests, and cancellation were explained; independent recall remains pending.

## [[course-catalog-persistence]]

- status: introduced
- depends-on: [[database-schema-and-records]], [[pydantic-models]], [[persistent-vector-storage]]
- introduced: 2026-10-16
- last-reviewed: 2026-10-16
- evidence: CourseSummary, a local SQLite catalog, unique course IDs, and transactions were explained; independent recall remains pending.

## [[question-api-validation]]

- status: introduced
- depends-on: [[pydantic-models]], [[course-filtered-vector-retrieval]], [[source-citation-formatting]]
- introduced: 2026-10-09
- last-reviewed: 2026-10-09
- evidence: JSON question requests, whitespace trimming, bounded result limits, and structured evidence responses were explained; independent recall remains pending.

## [[upload-to-index-integration]]

- status: introduced
- depends-on: [[fastapi-request-flow]], [[document-chunk-model]], [[persistent-vector-storage]]
- introduced: 2026-10-09
- last-reviewed: 2026-10-09
- evidence: Generated upload course IDs, original filename preservation, and thread-pool execution were explained; independent recall remains pending.

## [[source-citation-formatting]]

- status: introduced
- depends-on: [[document-metadata]], [[course-filtered-vector-retrieval]]
- introduced: 2026-10-09
- last-reviewed: 2026-10-09
- evidence: Source-faithful filename/page formatting and joining excerpts were explained; independent recall remains pending.

## [[course-filtered-vector-retrieval]]

- status: introduced
- depends-on: [[embeddings-and-vector-search]], [[document-metadata]]
- introduced: 2026-10-09
- last-reviewed: 2026-10-09
- evidence: Course filtering, bounded result counts, and raw distance were explained; independent explanation remains pending.

## [[deterministic-record-ids-and-upsert]]

- status: introduced
- depends-on: [[document-metadata]], [[chromadb-collections]]
- introduced: 2026-10-09
- last-reviewed: 2026-10-09
- evidence: Agreed to deterministic IDs and upsert for duplicate indexing; hashing and exact-retry behavior were explained, with independent explanation still pending.

## [[persistent-vector-storage]]

- status: introduced
- depends-on: [[chromadb-collections]]
- introduced: 2026-10-09
- last-reviewed: 2026-10-09
- evidence: Accepted local persistence for the MVP; persistent paths and temporary test storage were explained, with independent recall still pending.

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

- status: practicing
- depends-on: [[python-types]]
- introduced: 2026-08-06
- last-reviewed: 2026-08-12
- evidence: Correctly predicted that page zero should raise a validation error and ran three model tests plus the six-test suite successfully.

## [[python-types]]

- status: introduced
- depends-on: none
- introduced: 2026-08-06
- last-reviewed: 2026-08-06
- evidence: Explained that a missing optional page number becomes `None` after learning the `int | None = None` annotation and default.

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
- last-reviewed: 2026-08-18
- evidence: Predicted the twelve-test total, observed the intentional 500-versus-400 assertion failure, and reran the repaired full suite successfully.

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
