import type { Metadata } from "next";

import { ComingSoon } from "@/components/coming-soon";

export const metadata: Metadata = { title: "Applications" };

export default function ApplicationsPage() {
  return (
    <ComingSoon title="Applications" phase="Phase 8">
      Your application pipeline, statuses, deadlines and follow-up reminders.
    </ComingSoon>
  );
}
