// Transpile TSX for Node's test runner using the existing TypeScript dependency.
// These are validation and server-render checks, not browser interaction tests.
const fs = require("node:fs");
const assert = require("node:assert/strict");
const { test } = require("node:test");
const ts = require("typescript");
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");

require.extensions[".tsx"] = (module, filename) => {
  const { outputText, diagnostics } = ts.transpileModule(fs.readFileSync(filename, "utf8"), {
    reportDiagnostics: true,
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2017 },
  });
  assert.equal(diagnostics.filter(item => item.category === ts.DiagnosticCategory.Error).length, 0,
    ts.formatDiagnosticsWithColorAndContext(diagnostics, {
      getCanonicalFileName: name => name, getCurrentDirectory: () => process.cwd(), getNewLine: () => "\n",
    }));
  module._compile(outputText, filename);
};

const { default: CourseUpload, validateSyllabusFiles } = require("../src/app/CourseUpload.tsx");
const Page = require("../src/app/page.tsx").default;
const { saveCourseAndEstimate } = require("../src/app/CourseUpload.tsx");
const WorkloadTracker = require("../src/app/WorkloadTracker.tsx").default;
const file = (name, size = 1024) => ({ name, size });

test("accepts PDF extension including missing MIME metadata and uppercase names", () => {
  assert.equal(validateSyllabusFiles([file("SYLLABUS.PDF")]), null);
});
test("accepts the exact 10 MB boundary", () => {
  assert.equal(validateSyllabusFiles([file("course.pdf", 10 * 1024 * 1024)]), null);
});
test("rejects oversized files", () => {
  assert.match(validateSyllabusFiles([file("course.pdf", 10 * 1024 * 1024 + 1)]), /10 MB/);
});
test("rejects empty files", () => {
  assert.match(validateSyllabusFiles([file("course.pdf", 0)]), /empty/);
});
test("rejects non-PDF and misleading extensions", () => {
  for (const name of ["notes.txt", "syllabus.pdf.exe"]) assert.match(validateSyllabusFiles([file(name)]), /Choose a PDF/);
});
test("rejects multi-file drops rather than silently losing files", () => {
  assert.match(validateSyllabusFiles([file("a.pdf"), file("b.pdf")]), /one syllabus/);
});
test("requires one file", () => {
  assert.match(validateSyllabusFiles([]), /one syllabus/);
});
test("upload panel has one PDF input, named controls, limits, and a disabled initial submit", () => {
  const html = renderToStaticMarkup(React.createElement(CourseUpload, { apiBaseUrl: "", onSaved() {}, onClose() {} }));
  assert.equal((html.match(/type="file"/g) ?? []).length, 1);
  assert.match(html, /aria-labelledby="syllabus-label"/);
  assert.match(html, /aria-label="Close add course"/);
  assert.match(html, /10 MB/);
  assert.match(html, /<button disabled=""[^>]*>Save course/);
});
test("navigation has a single dashboard entry, not legacy Intake and Insights", () => {
  const html = renderToStaticMarkup(React.createElement(Page));
  assert.match(html, /My courses/);
  assert.match(html, /Student reviews/);
  assert.doesNotMatch(html, /Intake|Insights|Generate Semester Plan/);
  assert.equal((html.match(/>Add course<\/button>/g) ?? []).length, 1);
});

test("saving requests exactly one estimate with a neutral profile after the upload", async () => {
  const calls = [];
  let estimating = false;
  const result = await saveCourseAndEstimate("http://test", new FormData(), () => { estimating = true; }, async (url, options) => {
    calls.push({ url, options });
    if (calls.length === 1) return Response.json({ course_id: "one", course_name: "CSCE 120" }, { status: 201 });
    assert.equal(estimating, true);
    return Response.json({ weekly_hours: 3 });
  });
  assert.equal(result.course.course_id, "one");
  assert.equal(result.estimateError, undefined);
  assert.equal(calls.length, 2);
  assert.equal(calls[1].url, "http://test/api/courses/one/workload");
  assert.deepEqual(JSON.parse(calls[1].options.body), { comfort_level: 5, gpa: 0 });
});

test("provider failure keeps the saved course and never repeats its upload", async () => {
  const calls = [];
  const result = await saveCourseAndEstimate("", new FormData(), () => {}, async url => {
    calls.push(url);
    return calls.length === 1 ? Response.json({ course_id: "saved" }, { status: 201 }) : Response.json({}, { status: 503 });
  });
  assert.equal(result.course.course_id, "saved");
  assert.match(result.estimateError, /do not upload it again/);
  assert.deepEqual(calls, ["/api/courses", "/api/courses/saved/workload"]);
});

test("network failure during estimation still returns the saved course", async () => {
  let calls = 0;
  const result = await saveCourseAndEstimate("", new FormData(), () => {}, async () => {
    if (++calls === 1) return Response.json({ course_id: "saved" });
    throw new TypeError("Failed to fetch");
  });
  assert.equal(result.course.course_id, "saved");
  assert.ok(result.estimateError);
  assert.equal(calls, 2);
});

test("upload rejection does not request an estimate", async () => {
  let calls = 0;
  await assert.rejects(saveCourseAndEstimate("", new FormData(), () => assert.fail(), async () => {
    calls++;
    return Response.json({ detail: "No readable text" }, { status: 400 });
  }), /No readable text/);
  assert.equal(calls, 1);
});

const tracker = (overrides = {}) => ({
  courses: [{ course_id: "one", course_name: "CSCE 120", weekly_hours: 3, share_of_known_workload_percent: 100,
    workload_fit: { rating: 3, out_of: 3, label: "Favorable workload fit", reason: "Small schedule", weekly_hours_without_course: 0 } }],
  total_known_weekly_hours: 3, estimate_complete: true, pending_course_count: 0, workload_level: "Small",
  guidance_note: "Workload only; excludes scheduled class time.", ...overrides,
});
test("tracker renders total, course contribution, fit and without-course comparison", () => {
  const html = renderToStaticMarkup(React.createElement(WorkloadTracker, { schedule: tracker(), courseCount: 1 }));
  for (const text of ["3.0", "hours / week", "Small workload", "3/3", "Without this course:", "0.0 known hours/week"])
    assert.ok(html.includes(text), text);
});
test("pending course suppresses ratings and labels subtotal instead of assuming zero hours", () => {
  const html = renderToStaticMarkup(React.createElement(WorkloadTracker, { schedule: tracker({ estimate_complete: false, pending_course_count: 1 }), courseCount: 2 }));
  assert.match(html, /known subtotal only/);
  assert.match(html, /1 course\(s\) still need analysis/);
  assert.match(html, /Not rated/);
  assert.doesNotMatch(html, /3\/3/);
});
test("unknown total is not rendered as zero workload", () => {
  const html = renderToStaticMarkup(React.createElement(WorkloadTracker, { schedule: tracker({ courses: [], total_known_weekly_hours: null, workload_level: "Unknown", estimate_complete: false, pending_course_count: 1 }), courseCount: 1 }));
  assert.match(html, /Waiting for workload estimates/);
  assert.doesNotMatch(html, /Small workload/);
});
