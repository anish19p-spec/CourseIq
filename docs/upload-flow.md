# Course upload flow

The dashboard has one **Add course** entry point. It opens an inline form rather
than a second upload tab. Saving automatically requests a Gemini workload estimate
with neutral comfort (5/10) and no GPA adjustment. Then use the saved-workload
controls to personalize subject comfort and GPA. Removing the old Intake/Insights UI does not
remove the legacy backend `/api/analyze` endpoint.

The uploader supports choosing or dropping one PDF, replacing/removing a selection,
and showing its name and size. Empty, oversized (>10 MiB), non-PDF-extension, and
multiple-file selections are rejected locally. The backend remains responsible
for checking whether the contents are actually a readable PDF. A `.pdf` filename
is not proof of a PDF.

Save uses `POST /api/courses`, shows an indeterminate loading state (not fabricated
progress), and keeps the chosen file/name on a failed request. Success selects
the saved course and prompts for a workload estimate. Navigation to Student reviews
keeps the dashboard mounted so it cannot discard a pending upload. Closing the
form returns keyboard focus to Add course; successful save focuses course selection.
If Gemini fails after saving, the course remains saved, a separate warning points
to the estimate retry control, and no duplicate upload is attempted. The tracker
reloads when the saved-course IDs change or an estimate is updated.

## Verification

Run from `frontend/`:

```bash
npm test
npx tsc --noEmit
npm run build
```

The Node tests use the existing TypeScript and React dependencies for
file-validation and server-render checks (limits, controls, and removal of legacy
navigation). They do not simulate browser events or verify responsive layout.
The existing backend suite also covers upload validation and persistence.

The upload cleanup previously passed nine frontend tests, 131 backend tests,
TypeScript, and the production build. A live browser layout/interaction check could not be
completed because native capture failed and the in-app browser was unavailable.
Before merging, manually check file picking/drop, invalid-file errors, successful
save, failed-save retry, tab switching during save, and narrow-screen layout.
