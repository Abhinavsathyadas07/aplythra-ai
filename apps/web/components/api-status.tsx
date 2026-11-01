"use client";

import { useEffect, useState } from "react";

import { ApiError, getMe, getReadiness, type Me } from "@/lib/api";

type State =
  | { kind: "loading" }
  | { kind: "ready"; me: Me }
  | { kind: "error"; message: string };

export function ApiStatus() {
  const [state, setState] = useState<State>({ kind: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await getReadiness();
        const me = await getMe();
        if (!cancelled) setState({ kind: "ready", me });
      } catch (error) {
        const message =
          error instanceof ApiError ? error.message : "Something went wrong. Please try again.";
        if (!cancelled) setState({ kind: "error", message });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [attempt]);

  return (
    <section aria-labelledby="api-status-title" className="rounded-xl border border-border bg-card p-5">
      <h2 id="api-status-title" className="text-sm font-medium text-muted">
        Backend connection
      </h2>
      <div aria-live="polite" className="mt-2">
        {state.kind === "loading" && <p className="text-sm text-muted">Checking…</p>}
        {state.kind === "ready" && (
          <p className="text-sm" data-testid="api-connected">
            <span className="font-semibold text-success">Connected</span>
            <span className="text-muted"> · signed in as </span>
            <span className="font-medium [overflow-wrap:anywhere]">{state.me.email ?? "your account"}</span>
          </p>
        )}
        {state.kind === "error" && (
          <div className="flex flex-wrap items-center gap-3">
            <p role="alert" data-testid="api-error" className="text-sm font-medium text-danger">
              {state.message}
            </p>
            <button
              type="button"
              onClick={() => {
                setState({ kind: "loading" });
                setAttempt((n) => n + 1);
              }}
              className="min-h-11 rounded-lg border border-border px-4 text-sm font-medium hover:bg-background"
            >
              Retry
            </button>
          </div>
        )}
      </div>
    </section>
  );
}
