"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { createClient } from "@/lib/supabase/client";

type Mode = "signin" | "signup";

export function LoginForm({ next }: { next: string }) {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("signin");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") ?? "").trim();
    const password = String(form.get("password") ?? "");

    setBusy(true);
    setError(null);
    setNotice(null);
    const supabase = createClient();

    try {
      if (mode === "signin") {
        const { error: authError } = await supabase.auth.signInWithPassword({ email, password });
        if (authError) {
          // One generic message: never reveal whether an email is registered.
          setError("Invalid email or password.");
          return;
        }
      } else {
        const { data, error: authError } = await supabase.auth.signUp({ email, password });
        if (authError) {
          setError("Could not create the account. Check your details and try again.");
          return;
        }
        if (!data.session) {
          setNotice("Check your email to confirm your account, then sign in.");
          setMode("signin");
          return;
        }
      }
      router.replace(next);
      router.refresh();
    } catch {
      setError("Cannot reach the sign-in service. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  const signingIn = mode === "signin";

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4 rounded-xl border border-border bg-card p-5">
      <h2 className="text-lg font-semibold">{signingIn ? "Sign in" : "Create account"}</h2>

      <label className="flex flex-col gap-1 text-sm font-medium">
        Email
        <input
          name="email"
          type="email"
          required
          autoComplete="email"
          inputMode="email"
          className="min-h-11 rounded-lg border border-border bg-background px-3 text-base font-normal"
        />
      </label>

      <label className="flex flex-col gap-1 text-sm font-medium">
        Password
        <input
          name="password"
          type="password"
          required
          minLength={signingIn ? undefined : 8}
          autoComplete={signingIn ? "current-password" : "new-password"}
          className="min-h-11 rounded-lg border border-border bg-background px-3 text-base font-normal"
        />
        {!signingIn && <span className="text-xs font-normal text-muted">At least 8 characters.</span>}
      </label>

      <div aria-live="polite">
        {error && (
          <p role="alert" data-testid="form-error" className="text-sm font-medium text-danger">
            {error}
          </p>
        )}
        {notice && <p className="text-sm font-medium text-success">{notice}</p>}
      </div>

      <button
        type="submit"
        disabled={busy}
        className="min-h-11 rounded-lg bg-accent px-4 text-sm font-semibold text-accent-foreground disabled:opacity-60"
      >
        {busy ? "Please wait…" : signingIn ? "Sign in" : "Create account"}
      </button>

      <button
        type="button"
        onClick={() => {
          setMode(signingIn ? "signup" : "signin");
          setError(null);
          setNotice(null);
        }}
        className="min-h-11 text-sm font-medium text-accent"
      >
        {signingIn ? "Need an account? Create one" : "Already registered? Sign in"}
      </button>
    </form>
  );
}
