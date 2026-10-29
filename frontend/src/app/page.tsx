"use client";

import { ChangeEvent, DragEvent, FormEvent, useRef, useState } from "react";
import CourseWorkspace from "./CourseWorkspace";
import StudentReviews from "./StudentReviews";
import {
  ArrowRight,
  BadgeCheck,
  CalendarRange,
  CircleAlert,
  CircleCheckBig,
  FileUp,
  RotateCcw,
  Sparkles,
  UploadCloud,
} from "lucide-react";

type SyllabusData = {
  course_name: string;
  total_projects: number;
  total_midterms: number;
  total_homeworks: number;
  has_final_exam: boolean;
};

type AnalysisResponse = {
  course_name: string;
  target_grade: string;
  weekly_hours: number;
  risk_level: string;
  student_multiplier: number;
  syllabus: SyllabusData;
  assignment_inventory: {
    projects: number;
    midterms: number;
    homeworks: number;
    has_final_exam: boolean;
  };
  semester_weeks: number;
};

const GRADE_OPTIONS = ["A", "A-", "B+", "B", "B-", "C+", "C"];
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function riskTone(riskLevel: string) {
  if (riskLevel === "High Risk") {
    return "border-rose-400/30 bg-rose-500/15 text-rose-100";
  }
  if (riskLevel === "Manageable") {
    return "border-amber-400/30 bg-amber-500/15 text-amber-100";
  }
  return "border-emerald-400/30 bg-emerald-500/15 text-emerald-100";
}

function cardShell(extraClass = "") {
  return `rounded-3xl border border-white/10 bg-slate-950/60 shadow-glow backdrop-blur-xl ${extraClass}`;
}

function MetricCard({
  label,
  value,
  detail,
  icon,
}: {
  label: string;
  value: string;
  detail: string;
  icon: React.ReactNode;
}) {
  return (
    <div className={cardShell("p-6") }>
      <div className="mb-4 flex items-center gap-3 text-slate-300">
        <span className="grid h-11 w-11 place-items-center rounded-2xl border border-white/10 bg-white/5 text-amber-300">
          {icon}
        </span>
        <p className="text-sm font-medium uppercase tracking-[0.28em] text-slate-400">{label}</p>
      </div>
      <div className="space-y-2">
        <div className="text-4xl font-semibold tracking-tight text-white">{value}</div>
        <p className="max-w-sm text-sm leading-6 text-slate-300">{detail}</p>
      </div>
    </div>
  );
}

export default function Page() {
  const [activeView, setActiveView] = useState<"courses" | "reviews" | "ingestion" | "analytics">("courses");
  const [courseName, setCourseName] = useState("");
  const [gpa, setGpa] = useState("3.50");
  const [comfortLevel, setComfortLevel] = useState(5);
  const [targetGrade, setTargetGrade] = useState("A-");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelection = (incomingFile: File | null) => {
    if (!incomingFile) {
      return;
    }

    if (incomingFile.type !== "application/pdf") {
      setErrorMessage("Please upload a PDF syllabus.");
      return;
    }

    setErrorMessage(null);
    setSelectedFile(incomingFile);
  };

  const onInputChange = (event: ChangeEvent<HTMLInputElement>) => {
    handleFileSelection(event.target.files?.[0] ?? null);
  };

  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    handleFileSelection(event.dataTransfer.files?.[0] ?? null);
  };

  const onDragOver = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => setIsDragging(false);

  const submitAnalysis = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrorMessage(null);

    if (!selectedFile) {
      setErrorMessage("Attach a syllabus PDF before generating a plan.");
      return;
    }

    const formData = new FormData();
    formData.append("course_name", courseName.trim());
    formData.append("gpa", gpa);
    formData.append("comfort_level", String(comfortLevel));
    formData.append("target_grade", targetGrade);
    formData.append("file", selectedFile);

    setIsSubmitting(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/analyze`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorBody = await response.json().catch(() => null);
        throw new Error(errorBody?.detail ?? "Unable to generate a semester plan.");
      }

      const data: AnalysisResponse = await response.json();
      setAnalysis(data);
      setActiveView("analytics");
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Unexpected analysis failure.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const currentComfortLabel = comfortLevel <= 3 ? "low" : comfortLevel <= 7 ? "steady" : "confident";

  return (
    <main className="relative overflow-hidden px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] w-full max-w-7xl flex-col gap-8">
        <header className="flex flex-col gap-5 rounded-[2rem] border border-white/10 bg-white/5 p-6 shadow-glow backdrop-blur-xl lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.3em] text-emerald-100">
              <Sparkles className="h-3.5 w-3.5" />
              CourseIQ
            </div>
            <div>
              <h1 className="text-3xl font-semibold tracking-tight text-white sm:text-5xl">
                Academic planning that feels immediate, structured, and explainable.
              </h1>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-300 sm:text-base">
                Drop in a syllabus PDF, set your student profile, and get a deterministic workload forecast with a semester heatmap in one pass.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-white/10 bg-slate-950/60 p-2">
            <button type="button" onClick={() => setActiveView("courses")}
              className={`rounded-xl px-4 py-2 text-sm font-semibold ${activeView === "courses" ? "bg-emerald-400 text-slate-950" : "text-slate-300 hover:bg-white/5"}`}>
              Courses
            </button>
            <button type="button" onClick={() => setActiveView("reviews")} aria-pressed={activeView === "reviews"}
              className={`rounded-xl px-4 py-2 text-sm font-semibold ${activeView === "reviews" ? "bg-emerald-400 text-slate-950" : "text-slate-300 hover:bg-white/5"}`}>
              Reviews
            </button>
            <button
              type="button"
              onClick={() => setActiveView("ingestion")}
              className={`rounded-xl px-4 py-2 text-sm font-semibold transition ${
                activeView === "ingestion"
                  ? "bg-emerald-400 text-slate-950"
                  : "text-slate-300 hover:bg-white/5 hover:text-white"
              }`}
            >
              Intake
            </button>
            <button
              type="button"
              onClick={() => setActiveView("analytics")}
              disabled={!analysis}
              className={`rounded-xl px-4 py-2 text-sm font-semibold transition ${
                activeView === "analytics"
                  ? "bg-sky-400 text-slate-950"
                  : analysis
                    ? "text-slate-300 hover:bg-white/5 hover:text-white"
                    : "cursor-not-allowed text-slate-500"
              }`}
            >
              Insights
            </button>
          </div>
        </header>

        {activeView === "reviews" ? <StudentReviews apiBaseUrl={API_BASE_URL} /> : activeView === "courses" ? <CourseWorkspace apiBaseUrl={API_BASE_URL} /> : activeView === "ingestion" ? (
          <section className="grid gap-6 lg:grid-cols-[1.25fr_0.75fr]">
            <form onSubmit={submitAnalysis} className={cardShell("p-6 sm:p-8") }>
              <div
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                onDrop={onDrop}
                className={`group rounded-[1.75rem] border border-dashed p-6 transition sm:p-8 ${
                  isDragging
                    ? "border-emerald-300 bg-emerald-500/10"
                    : "border-white/15 bg-white/5 hover:border-sky-300/40 hover:bg-white/7"
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="application/pdf"
                  className="hidden"
                  onChange={onInputChange}
                />
                <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
                  <div className="max-w-xl space-y-3">
                    <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-semibold uppercase tracking-[0.3em] text-slate-300">
                      <UploadCloud className="h-3.5 w-3.5 text-amber-300" />
                      Syllabus ingestion
                    </div>
                    <h2 className="text-2xl font-semibold text-white">Upload a syllabus PDF to generate a semester forecast.</h2>
                    <p className="text-sm leading-6 text-slate-300">
                      The upload zone accepts drag-and-drop or a direct file picker, and the backend returns structured workload metrics after Gemini extraction and rule-based scoring.
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="inline-flex items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white px-4 py-3 text-sm font-semibold text-slate-950 transition hover:-translate-y-0.5 hover:bg-amber-300"
                  >
                    <FileUp className="h-4 w-4" />
                    Choose PDF
                  </button>
                </div>

                <div className="mt-6 rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-4 text-sm text-slate-300">
                  {selectedFile ? (
                    <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                      <span className="font-medium text-white">{selectedFile.name}</span>
                      <span className="text-emerald-300">Ready to analyze</span>
                    </div>
                  ) : (
                    <p>Drop a syllabus PDF here or use the button above. PDF only.</p>
                  )}
                </div>
              </div>

              <div className="mt-8 grid gap-5 md:grid-cols-2">
                <label className="space-y-2">
                  <span className="text-sm font-medium text-slate-300">Course Name</span>
                  <input
                    value={courseName}
                    onChange={(event) => setCourseName(event.target.value)}
                    placeholder="CSCE 221: Data Structures"
                    className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none ring-0 placeholder:text-slate-500 focus:border-sky-300/50"
                  />
                </label>

                <label className="space-y-2">
                  <span className="text-sm font-medium text-slate-300">GPA</span>
                  <input
                    value={gpa}
                    onChange={(event) => setGpa(event.target.value)}
                    type="number"
                    step="0.01"
                    min="0"
                    max="4"
                    placeholder="3.50"
                    className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none ring-0 placeholder:text-slate-500 focus:border-sky-300/50"
                  />
                </label>

                <label className="space-y-2 md:col-span-2">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-sm font-medium text-slate-300">Comfort Level</span>
                    <span className="rounded-full border border-amber-400/20 bg-amber-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.3em] text-amber-100">
                      {comfortLevel} / 10 · {currentComfortLabel}
                    </span>
                  </div>
                  <input
                    value={comfortLevel}
                    onChange={(event) => setComfortLevel(Number(event.target.value))}
                    type="range"
                    min="1"
                    max="10"
                    className="h-2 w-full cursor-pointer appearance-none rounded-full bg-white/10 accent-emerald-400"
                  />
                </label>

                <label className="space-y-2 md:col-span-2">
                  <span className="text-sm font-medium text-slate-300">Target Grade</span>
                  <select
                    value={targetGrade}
                    onChange={(event) => setTargetGrade(event.target.value)}
                    className="w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 py-3 text-white outline-none focus:border-sky-300/50"
                  >
                    {GRADE_OPTIONS.map((grade) => (
                      <option key={grade} value={grade}>
                        {grade}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              <div className="mt-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-center gap-3 text-sm text-slate-400">
                  <CircleCheckBig className="h-4 w-4 text-emerald-300" />
                  The frontend posts a native multipart form to the FastAPI backend.
                </div>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="inline-flex items-center justify-center gap-2 rounded-2xl bg-amber-300 px-5 py-3 font-semibold text-slate-950 transition hover:-translate-y-0.5 hover:bg-amber-200 disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {isSubmitting ? "Generating..." : "Generate Semester Plan"}
                  <ArrowRight className="h-4 w-4" />
                </button>
              </div>

              {errorMessage ? (
                <div className="mt-5 flex items-start gap-3 rounded-2xl border border-rose-400/20 bg-rose-500/10 p-4 text-sm text-rose-100">
                  <CircleAlert className="mt-0.5 h-4 w-4" />
                  <span>{errorMessage}</span>
                </div>
              ) : null}
            </form>

            <aside className={cardShell("p-6 sm:p-8")}>
              <div className="flex items-center justify-between gap-4">
                <h3 className="text-lg font-semibold text-white">Pipeline snapshot</h3>
                <BadgeCheck className="h-5 w-5 text-emerald-300" />
              </div>
              <div className="mt-5 space-y-4 text-sm text-slate-300">
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Step 1</p>
                  <p className="mt-1 text-white">Parse syllabus text from PDF with pdfplumber.</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Step 2</p>
                  <p className="mt-1 text-white">Use Gemini structured output to extract assignment counts.</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Step 3</p>
                  <p className="mt-1 text-white">Apply a deterministic workload engine and return the plan.</p>
                </div>
              </div>

              <div className="mt-6 rounded-2xl border border-sky-400/15 bg-sky-500/10 p-4 text-sm text-sky-100">
                <p className="font-medium">Comfort-aware modeling</p>
                <p className="mt-1 text-sky-100/80">
                  Lower comfort levels increase predicted hours, while higher GPAs modestly reduce workload stress.
                </p>
              </div>
            </aside>
          </section>
        ) : (
          <section className="space-y-6">
            {analysis ? (
              <>
                <div className="grid gap-6 lg:grid-cols-2">
                  <MetricCard
                    label="Estimated Weekly Workload"
                    value={`${analysis.weekly_hours.toFixed(1)} hrs`}
                    detail={`Based on ${analysis.syllabus.course_name} and a ${analysis.student_multiplier.toFixed(2)}x student adjustment.`}
                    icon={<CalendarRange className="h-5 w-5" />}
                  />

                  <div className={cardShell("p-6") }>
                    <div className="mb-4 flex items-center gap-3 text-slate-300">
                      <span className="grid h-11 w-11 place-items-center rounded-2xl border border-white/10 bg-white/5 text-sky-300">
                        <Sparkles className="h-5 w-5" />
                      </span>
                      <p className="text-sm font-medium uppercase tracking-[0.28em] text-slate-400">Semester Risk Level</p>
                    </div>
                    <div className="space-y-3">
                      <div className={`inline-flex rounded-full border px-4 py-2 text-sm font-semibold ${riskTone(analysis.risk_level)}`}>
                        {analysis.risk_level}
                      </div>
                      <p className="max-w-lg text-sm leading-6 text-slate-300">
                        The badge updates directly from the backend string response, so the UI reflects the deterministic engine without a second local rule layer.
                      </p>
                    </div>
                  </div>
                </div>

                <div className={cardShell("p-6 sm:p-8") }>
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                    <div>
                      <h3 className="text-xl font-semibold text-white">Semester heatmap</h3>
                      <p className="mt-1 text-sm text-slate-400">Weeks 6 and 12 are marked as peak workload checkpoints for midterms and crunch periods.</p>
                    </div>
                    <div className="inline-flex items-center gap-2 rounded-full border border-amber-400/20 bg-amber-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.28em] text-amber-100">
                      <CircleAlert className="h-3.5 w-3.5" />
                      Peak workload weeks highlighted
                    </div>
                  </div>

                  <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7 xl:grid-cols-14">
                    {Array.from({ length: 14 }, (_, index) => {
                      const week = index + 1;
                      const isPeak = week === 6 || week === 12;
                      return (
                        <div
                          key={week}
                          className={`rounded-2xl border p-3 text-center transition ${
                            isPeak
                              ? "border-amber-300/40 bg-amber-500/15 shadow-[0_12px_30px_rgba(245,158,11,0.18)]"
                              : "border-white/10 bg-white/5"
                          }`}
                        >
                          <div className="text-xs uppercase tracking-[0.24em] text-slate-500">Week</div>
                          <div className="mt-1 text-2xl font-semibold text-white">{week}</div>
                          <div className={`mt-3 rounded-full px-2 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] ${isPeak ? "bg-amber-300 text-slate-950" : "bg-white/10 text-slate-300"}`}>
                            {isPeak ? "Peak" : "Normal"}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                <div className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
                  <div className={cardShell("overflow-hidden") }>
                    <div className="border-b border-white/10 px-6 py-5 sm:px-8">
                      <h3 className="text-xl font-semibold text-white">Assignment inventory</h3>
                      <p className="mt-1 text-sm text-slate-400">Structured counts returned from the JSON payload.</p>
                    </div>
                    <div className="overflow-x-auto px-6 py-4 sm:px-8">
                      <table className="min-w-full divide-y divide-white/10 text-left text-sm">
                        <thead className="text-xs uppercase tracking-[0.28em] text-slate-500">
                          <tr>
                            <th className="pb-4 pr-4">Type</th>
                            <th className="pb-4 pr-4">Count</th>
                            <th className="pb-4">Signal</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5 text-slate-300">
                          <tr>
                            <td className="py-4 pr-4 text-white">Projects</td>
                            <td className="py-4 pr-4">{analysis.assignment_inventory.projects}</td>
                            <td className="py-4">Long-form deliverables</td>
                          </tr>
                          <tr>
                            <td className="py-4 pr-4 text-white">Midterms</td>
                            <td className="py-4 pr-4">{analysis.assignment_inventory.midterms}</td>
                            <td className="py-4">Peak checkpoints</td>
                          </tr>
                          <tr>
                            <td className="py-4 pr-4 text-white">Homeworks</td>
                            <td className="py-4 pr-4">{analysis.assignment_inventory.homeworks}</td>
                            <td className="py-4">Weekly repetition</td>
                          </tr>
                          <tr>
                            <td className="py-4 pr-4 text-white">Final exam</td>
                            <td className="py-4 pr-4">{analysis.assignment_inventory.has_final_exam ? "Yes" : "No"}</td>
                            <td className="py-4">Cumulative prep load</td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <div className={cardShell("p-6 sm:p-8") }>
                    <h3 className="text-xl font-semibold text-white">Course summary</h3>
                    <div className="mt-5 space-y-4 text-sm text-slate-300">
                      <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                        <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Course</p>
                        <p className="mt-1 text-white">{analysis.course_name}</p>
                      </div>
                      <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                        <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Target grade</p>
                        <p className="mt-1 text-white">{analysis.target_grade}</p>
                      </div>
                      <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                        <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Semester length</p>
                        <p className="mt-1 text-white">{analysis.semester_weeks} weeks</p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => setActiveView("ingestion")}
                      className="mt-6 inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-semibold text-white transition hover:bg-white/10"
                    >
                      <RotateCcw className="h-4 w-4" />
                      Analyze another syllabus
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <div className={cardShell("p-8 text-center") }>
                <p className="text-lg font-semibold text-white">No analysis yet.</p>
                <p className="mt-2 text-sm text-slate-400">Upload a syllabus PDF from the intake view to populate this dashboard.</p>
              </div>
            )}
          </section>
        )}
      </div>
    </main>
  );
}
