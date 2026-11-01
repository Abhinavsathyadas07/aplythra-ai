import type { Metadata } from "next";

import { ComingSoon } from "@/components/coming-soon";

export const metadata: Metadata = { title: "Jobs" };

export default function JobsPage() {
  return (
    <ComingSoon title="Jobs" phase="Phase 5">
      Ranked vacancies from permitted sources, each with an explainable match assessment.
    </ComingSoon>
  );
}
