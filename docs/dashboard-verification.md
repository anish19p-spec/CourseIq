# Combined dashboard verification

Checked October 28, 2026 in desktop Chrome against an isolated temporary database.
The data consisted of two synthetic saved courses and one explicitly synthetic
student review. Extraction was mocked; this check made no live Gemini calls and
did not use the application's real saved data.

Observed browser behavior:

- The Reviews form published a review with difficulty 3/5 and 6.5 reported hours.
  The feed immediately displayed it with the anonymous, unverified label.
- Filtering by an unrelated course hid the review. Filtering by `CSCE-120`
  returned the review saved under normalized `CSCE 120`.
- The review remained visible after restarting the API against the same database
  and reloading the browser.
- Saved workload estimates also reloaded after the restart. Updating subject
  comfort from 1 to 5 changed the synthetic CSCE course from 2.1 to 1.5 weekly
  hours. The combined total changed from 4.1 to 3.5, with shares of 42.86% and
  57.14%. The API reused saved extraction data; the mocked extraction function
  was not called for this update.

Automated checks cover review validation, public reads by separate clients,
SQLite persistence across processes, workload calculations, caching, and the
review-first database initialization case. `test_shared_dashboard.py` verifies
that reviews, saved courses, and saved workloads coexist in one SQLite file.

This verification does not establish live extraction accuracy, mobile layout,
account isolation, moderation, or public hosting. Those are separate checks or
future features. See the root README for setup and the API contracts.
