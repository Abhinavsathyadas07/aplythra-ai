import type { Metadata } from "next";

import { LoginForm } from "@/app/login/login-form";
import { safeNextPath } from "@/lib/safe-redirect";

export const metadata: Metadata = { title: "Sign in" };

export default async function LoginPage({ searchParams }: PageProps<"/login">) {
  const params = await searchParams;
  const next = safeNextPath(typeof params.next === "string" ? params.next : null);

  return (
    <main className="mx-auto flex min-h-dvh w-full max-w-sm flex-col justify-center gap-6 px-4 py-10">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">JobPilot AI</h1>
        <p className="mt-1 text-sm text-muted">Sign in to your private workspace.</p>
      </div>
      <LoginForm next={next} />
    </main>
  );
}
