import type { Metadata } from "next";

import { ApiStatus } from "@/components/api-status";

export const metadata: Metadata = { title: "Dashboard" };

const NEXT_STEPS = [
  { title: "Candidate profile", phase: "Phase 4", text: "Verified qualifications and your master CV." },
  { title: "Job discovery", phase: "Phase 5", text: "Ranked vacancies with explainable matches." },
  { title: "CV tailoring", phase: "Phase 6", text: "ATS-friendly CVs built only from verified facts." },
];

export default function DashboardPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
        <p className="mt-1 text-sm text-muted">Quality applications over mass submissions.</p>
      </div>

      <ApiStatus />

      <section aria-labelledby="coming-title">
        <h2 id="coming-title" className="text-sm font-medium text-muted">
          Coming next
        </h2>
        <ul className="mt-2 grid gap-3 md:grid-cols-3">
          {NEXT_STEPS.map((step) => (
            <li key={step.title} className="rounded-xl border border-border bg-card p-4">
              <p className="font-medium">{step.title}</p>
              <p className="mt-1 text-xs font-medium text-accent">{step.phase}</p>
              <p className="mt-2 text-sm text-muted">{step.text}</p>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
