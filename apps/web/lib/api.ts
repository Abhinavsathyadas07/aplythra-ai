import { createClient } from "@/lib/supabase/client";
import { env } from "@/lib/env";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number | null,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const TIMEOUT_MS = 8000;

/** Calls the JobPilot API with the signed-in user's access token. Never logs the token. */
export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const {
    data: { session },
  } = await createClient().auth.getSession();

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const response = await fetch(`${env.apiBaseUrl}${path}`, {
      ...init,
      signal: controller.signal,
      headers: {
        Accept: "application/json",
        ...(session ? { Authorization: `Bearer ${session.access_token}` } : {}),
        ...init.headers,
      },
    });
    if (!response.ok) {
      throw new ApiError(
        response.status === 401 ? "Your session has expired. Please sign in again." : "Request failed",
        response.status,
      );
    }
    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError("Cannot reach the server", null);
  } finally {
    clearTimeout(timer);
  }
}

export type Me = { id: string; email: string | null; created_at: string };
export type Readiness = { status: "ok" | "unavailable" };

export const getMe = () => apiFetch<Me>("/me");
export const getReadiness = () => apiFetch<Readiness>("/health/ready");
