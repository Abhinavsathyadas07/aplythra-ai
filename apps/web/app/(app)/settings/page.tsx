import type { Metadata } from "next";

import { SignOutButton } from "@/components/sign-out-button";
import { createClient } from "@/lib/supabase/server";

export const metadata: Metadata = { title: "Settings" };

export default async function SettingsPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>

      <section aria-labelledby="account-title" className="rounded-xl border border-border bg-card p-5">
        <h2 id="account-title" className="text-sm font-medium text-muted">
          Account
        </h2>
        <p className="mt-2 text-sm font-medium [overflow-wrap:anywhere]" data-testid="account-email">
          {user?.email}
        </p>
        <div className="mt-4">
          <SignOutButton />
        </div>
      </section>

      <section aria-labelledby="privacy-title" className="rounded-xl border border-dashed border-border bg-card p-5">
        <h2 id="privacy-title" className="text-sm font-medium text-accent">
          Privacy controls · planned
        </h2>
        <p className="mt-2 text-sm text-muted">
          Data export, account deletion and retention settings arrive with the privacy work in
          Phase 10. Until then your data is stored only for the features that exist.
        </p>
      </section>
    </div>
  );
}
