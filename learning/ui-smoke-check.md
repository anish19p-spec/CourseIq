# Courses UI smoke check — 2026-10-16

## Scope

Executed through native Chrome against the actual Next.js frontend and FastAPI
routes. Used isolated Chroma/SQLite storage and a temporary backend harness that
substituted extraction and embeddings. No Gemini calls were made.

The uploaded `.pdf` fixtures were synthetic harness inputs with a PDF signature,
not valid parser-tested PDFs. The harness extracted their fixture text and
assigned page 2 plus an unreadable-page-1 warning. Therefore this check verifies
UI/API integration, not PDF parser quality or embedding relevance.

## Observed results

1. Opening Courses loaded the empty catalog.
2. Uploaded Coding Test / coding-test.pdf. The course became selected and its
   extraction warning appeared.
3. Asked “What is homework worth?” and saw the coding passage: 30%, citation
   `coding-test.pdf, p. 2`.
4. Uploaded History Test / history-test.pdf. The question and previous evidence
   cleared when the newly uploaded course became selected.
5. Asked the same question and saw the history passage: 60%, citation
   `history-test.pdf, p. 2`.
6. Selected Coding Test in the dropdown. History evidence cleared.
7. Restarted the isolated backend with the same storage directory, then reloaded
   Chrome. The catalog loaded and a new coding question returned the same saved
   coding passage and page citation.
8. Inspected the rendered desktop layout; controls and evidence were visible.

Both temporary servers were stopped after verification. The harness, fixtures,
and isolated storage remain under `/private/tmp/courseiq-ui-smoke.Oa64rE` for
inspection; they are not part of the application or its real course catalog.

## Remaining checks

Live-upload follow-up: the borrowed `text-embedding-004` model was retired.
Updated requests to `gemini-embedding-2` and added missing-key 503 responses;
59 tests pass. A local configuration check found no GEMINI_API_KEY in the tool
process. The user's server environment and successful live retry are still
unverified. No API key was read or printed.

- Valid real PDFs through the production extractor and live embedding provider.
- Semantic retrieval quality and answers generated from retrieved evidence.
- Mobile layout and request-failure paths in the browser.

Backend automated tests cover invalid inputs, provider failures, and isolation;
the prior full run passed 57 tests. Frontend TypeScript checks passed before this
browser verification. No application code changed during this smoke check.
