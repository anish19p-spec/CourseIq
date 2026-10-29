"use client";

import { useState } from "react";
import { BookOpen, MessageSquare } from "lucide-react";
import CourseWorkspace from "./CourseWorkspace";
import StudentReviews from "./StudentReviews";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function Page() {
  const [activeView, setActiveView] = useState<"courses" | "reviews">("courses");
  return <main className="px-4 py-6 sm:px-6 lg:px-8 lg:py-10">
    <div className="mx-auto w-full max-w-7xl space-y-8">
      <header className="flex flex-col gap-6 border-b border-white/10 pb-6 sm:flex-row sm:items-center sm:justify-between">
        <div><a href="/" className="text-2xl font-semibold tracking-tight text-white">Course<span className="text-emerald-300">IQ</span></a>
          <p className="mt-1 text-sm text-slate-400">Know your courses. Plan your week.</p></div>
        <nav aria-label="Main navigation" className="flex gap-1 self-start rounded-2xl border border-white/10 bg-slate-950/60 p-1.5">
          {([
            { id: "courses", label: "My courses", icon: BookOpen },
            { id: "reviews", label: "Student reviews", icon: MessageSquare },
          ] as const).map(({ id, label, icon: Icon }) => <button key={id} type="button" onClick={() => setActiveView(id)} aria-pressed={activeView === id}
            className={`inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-300 ${activeView === id ? "bg-white/10 text-white" : "text-slate-400 hover:bg-white/5 hover:text-white"}`}>
            <Icon className="h-4 w-4" aria-hidden="true" />{label}</button>)}
        </nav>
      </header>
      {/* Keep uploads mounted when switching navigation tabs. */}
      <div hidden={activeView !== "courses"}><CourseWorkspace apiBaseUrl={API_BASE_URL} /></div>
      {activeView === "reviews" && <StudentReviews apiBaseUrl={API_BASE_URL} />}
    </div>
  </main>;
}
