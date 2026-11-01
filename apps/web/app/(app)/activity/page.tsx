import type { Metadata } from "next";

import { ComingSoon } from "@/components/coming-soon";

export const metadata: Metadata = { title: "Activity" };

export default function ActivityPage() {
  return (
    <ComingSoon title="Activity" phase="Phase 5">
      A history of what the agent did, with the sources and decisions behind each step.
    </ComingSoon>
  );
}
