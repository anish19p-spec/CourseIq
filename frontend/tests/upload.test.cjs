// Transpile TSX for Node's test runner using the existing TypeScript dependency.
// These are validation and server-render checks, not browser interaction tests.
const fs = require("node:fs");
const assert = require("node:assert/strict");
const { test } = require("node:test");
const ts = require("typescript");
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");

require.extensions[".tsx"] = (module, filename) => {
  const { outputText } = ts.transpileModule(fs.readFileSync(filename, "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, target: ts.ScriptTarget.ES2017 },
  });
  module._compile(outputText, filename);
};

const { default: CourseUpload, validateSyllabusFiles } = require("../src/app/CourseUpload.tsx");
const Page = require("../src/app/page.tsx").default;
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
