"use client";

import { DragEvent, FormEvent, useRef, useState } from "react";
import { ArrowRight, FileText, LoaderCircle, UploadCloud, X } from "lucide-react";

export type Course = {
  course_id: string; course_name: string; filename: string; chunk_count: number; warnings: string[];
};

export function validateSyllabusFiles(files: Pick<File, "name" | "size">[]): string | null {
  if (files.length !== 1) return "Add one syllabus at a time.";
  const candidate = files[0];
  if (!candidate.name.toLowerCase().endsWith(".pdf")) return "Choose a PDF syllabus. Other file types are not supported yet.";
  if (candidate.size === 0) return "This file is empty. Choose another PDF.";
  if (candidate.size > 10 * 1024 * 1024) return "This PDF is too large. The limit is 10 MB.";
  return null;
}

export async function saveCourseAndEstimate(apiBaseUrl: string, data: FormData, onEstimating: () => void, request: typeof fetch = fetch): Promise<{ course: Course; estimateError?: string }> {
  const response = await request(`${apiBaseUrl}/api/courses`, { method: "POST", body: data });
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new Error(typeof body?.detail === "string" ? body.detail : "Syllabus could not be saved. Please try again.");
  if (!body?.course_id) throw new Error("The server returned an unreadable response. Refresh saved courses before uploading again.");
  onEstimating();
  try {
    const estimate = await request(`${apiBaseUrl}/api/courses/${encodeURIComponent(body.course_id)}/workload`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ comfort_level: 5, gpa: 0 }),
    });
    if (!estimate.ok) throw new Error("Workload estimate failed.");
    return { course: body as Course };
  } catch {
    // Saving already succeeded. Never repeat the upload after an estimation failure.
    return { course: body as Course, estimateError: "The syllabus was saved, but its workload could not be estimated. Use Estimate and save workload below to retry—do not upload it again." };
  }
}

export default function CourseUpload({ apiBaseUrl, onSaved, onClose }: {
  apiBaseUrl: string; onSaved: (course: Course, estimateError?: string) => void; onClose: () => void;
}) {
  const [name, setName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [estimating, setEstimating] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  function selectFiles(files: File[]) {
    if (busy || files.length === 0) return;
    setError("");
    const validation = validateSyllabusFiles(files);
    if (validation) { setError(validation); return; }
    setFile(files[0]);
  }

  function drop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault(); setDragging(false);
    selectFiles(Array.from(event.dataTransfer.files));
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    if (!file || !name.trim()) { setError("Enter a course name and choose a PDF syllabus."); return; }
    const data = new FormData();
    data.set("course_name", name.trim()); data.set("file", file);
    setBusy(true); setError("");
    try {
      const { course, estimateError } = await saveCourseAndEstimate(apiBaseUrl, data, () => setEstimating(true));
      onSaved(course, estimateError);
    } catch (failure) { setError(failure instanceof Error ? failure.message : "Unable to save this syllabus."); }
    finally { setBusy(false); setEstimating(false); }
  }

  return <section aria-labelledby="add-course-title" className="overflow-hidden rounded-3xl border border-emerald-300/20 bg-slate-950/80 shadow-glow">
    <div className="flex items-start justify-between gap-4 border-b border-white/10 px-6 py-5 sm:px-8">
      <div><p className="mb-1 text-xs font-semibold uppercase tracking-widest text-emerald-300">Build your schedule</p>
        <h2 id="add-course-title" className="text-2xl font-semibold text-white">Add a course</h2>
        <p className="mt-2 text-sm text-slate-400">Save your syllabus once. Come back to it anytime.</p></div>
      <button type="button" onClick={onClose} disabled={busy} aria-label="Close add course"
        className="rounded-full p-2 text-slate-400 hover:bg-white/10 hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-emerald-300 disabled:opacity-40"><X className="h-5 w-5" /></button>
    </div>
    <form onSubmit={save} aria-busy={busy} className="grid gap-8 p-6 sm:p-8 lg:grid-cols-[1.2fr_0.8fr]">
      <div className="space-y-5">
        <div className="space-y-2"><label htmlFor="saved-course-name" className="block text-sm font-medium text-slate-200">Course name</label>
          <input autoFocus id="saved-course-name" value={name} onChange={event => setName(event.target.value)} required maxLength={200} disabled={busy}
            placeholder="e.g. CSCE 120 · Fall 2026" className="w-full rounded-xl border border-white/15 bg-slate-900/80 px-4 py-3 text-white placeholder:text-slate-500 focus:border-emerald-300 focus:outline-none focus:ring-2 focus:ring-emerald-300/20 disabled:opacity-60" /></div>
        <div><p id="syllabus-label" className="mb-2 text-sm font-medium text-slate-200">Syllabus</p>
          <div onDragOver={event => { event.preventDefault(); if (!busy) setDragging(true); }}
            onDragLeave={event => { if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setDragging(false); }} onDrop={drop}
            className={`rounded-2xl border border-dashed px-5 py-6 transition ${dragging ? "border-emerald-300 bg-emerald-400/10" : "border-white/20 bg-white/[0.025]"}`}>
            <input ref={fileInput} id="saved-course-file" type="file" accept=".pdf,application/pdf" disabled={busy} className="sr-only"
              aria-labelledby="syllabus-label" aria-describedby="syllabus-help" tabIndex={-1}
              onChange={event => { selectFiles(Array.from(event.target.files ?? [])); event.target.value = ""; }} />
            {file ? <div className="flex items-center gap-3">
              <div className="rounded-xl bg-emerald-400/10 p-3 text-emerald-300"><FileText className="h-6 w-6" /></div>
              <div className="min-w-0 flex-1"><p className="break-all text-sm font-medium text-white">{file.name}</p>
                <p className="mt-1 text-xs text-slate-400">{(file.size / 1024 / 1024).toFixed(2)} MB · PDF</p></div>
              <button type="button" disabled={busy} onClick={() => { setFile(null); setError(""); }} aria-label="Remove selected syllabus"
                className="rounded-lg p-2 text-slate-400 hover:bg-white/10 hover:text-white focus-visible:outline focus-visible:outline-emerald-300 disabled:opacity-40"><X className="h-4 w-4" /></button>
            </div> : <div className="text-center"><UploadCloud className="mx-auto mb-3 h-8 w-8 text-emerald-300" aria-hidden="true" />
              <p className="text-sm font-medium text-slate-200">Drop your syllabus here</p><p className="mt-1 text-xs text-slate-500">or choose a file from your device</p></div>}
            <button type="button" disabled={busy} onClick={() => fileInput.current?.click()}
              className="mx-auto mt-4 block rounded-xl border border-white/15 bg-white/5 px-4 py-2 text-sm font-medium text-white hover:bg-white/10 focus-visible:outline focus-visible:outline-2 focus-visible:outline-emerald-300 disabled:opacity-40">
              {file ? "Choose a different PDF" : "Choose PDF"}</button>
          </div>
          <p id="syllabus-help" className="mt-2 text-xs text-slate-500">Text-based PDF only · Up to 10 MB · One syllabus per course</p>
        </div>
        {error && <p role="alert" className="rounded-xl border border-rose-400/20 bg-rose-400/10 px-4 py-3 text-sm text-rose-200">{error}</p>}
        <button disabled={busy || !file || !name.trim()} className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-300 px-5 py-3 text-sm font-semibold text-slate-950 hover:bg-emerald-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-300 disabled:cursor-not-allowed disabled:opacity-40 sm:w-auto">
          {busy ? <><LoaderCircle className="h-4 w-4 animate-spin" />{estimating ? "Estimating workload…" : "Saving syllabus…"}</> : <>Save course<ArrowRight className="h-4 w-4" /></>}
        </button>
        <p role="status" aria-live="polite" className="text-xs leading-5 text-slate-400">{busy ? estimating ? "Syllabus saved. Gemini is reviewing it to estimate weekly hours. Keep this page open." : "Reading pages and indexing your syllabus. Keep this page open; this can take a moment." : "Saving also requests a Gemini workload estimate using neutral comfort (5/10) and no GPA adjustment. You can personalize it afterward. Each upload creates a separate course."}</p>
      </div>
      <aside className="rounded-2xl border border-white/10 bg-white/[0.025] p-5 sm:p-6">
        <h3 className="font-medium text-white">One upload, a clearer plan</h3>
        <ol className="mt-5 space-y-6 text-sm">{[
          ["Save your syllabus", "We keep readable text and page references for later."],
          ["Get a weekly estimate", "Gemini reviews the saved syllabus. Personalize the estimate with your subject comfort afterward."],
          ["Compare your courses", "See your combined workload and find evidence in each syllabus."],
        ].map(([title, detail], index) => <li key={title} className="flex gap-3">
          <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-emerald-300/10 text-xs text-emerald-300">{index + 1}</span>
          <div><p className="font-medium text-slate-200">{title}</p><p className="mt-1 leading-6 text-slate-400">{detail}</p></div>
        </li>)}</ol>
        <p className="mt-6 border-t border-white/10 pt-4 text-xs leading-5 text-slate-400">Saved courses are shared on this installation. Private accounts are not available yet.</p>
      </aside>
    </form>
  </section>;
}
