import { defineConfig, devices } from "@playwright/test";

// Ports are non-default so a running dev stack does not collide with the tests.
const WEB = 3100;
const API = 8100;
const AUTH = 54321;
const DB_OWNER = "postgresql+psycopg://jobpilot_owner:dev_owner_pw@localhost:5432/jobpilot_e2e";
const DB_APP = "postgresql+psycopg://jobpilot_app:dev_app_pw@localhost:5432/jobpilot_e2e";

const publicEnv = {
  NEXT_PUBLIC_SUPABASE_URL: `http://localhost:${AUTH}`,
  NEXT_PUBLIC_SUPABASE_ANON_KEY: "test-anon-key",
  NEXT_PUBLIC_API_BASE_URL: `http://localhost:${API}`,
};

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: [["list"]],
  use: { baseURL: `http://localhost:${WEB}`, trace: "retain-on-failure" },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile", use: { ...devices["Pixel 7"] } },
  ],
  webServer: [
    {
      command: "node tests/e2e/fake-supabase.mjs",
      url: `http://localhost:${AUTH}/health`,
      reuseExistingServer: !process.env.CI,
    },
    {
      // Real backend: migrate the e2e database, then serve with JWKS pointing at the fake auth server.
      command: `uv run alembic upgrade head && uv run uvicorn app.main:create_app --factory --port ${API}`,
      cwd: "../api",
      url: `http://localhost:${API}/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
      env: {
        MIGRATION_DATABASE_URL: DB_OWNER,
        DATABASE_URL: DB_APP,
        SUPABASE_JWKS_URL: `http://localhost:${AUTH}/auth/v1/.well-known/jwks.json`,
        JWT_ISSUER: `http://localhost:${AUTH}/auth/v1`,
        CORS_ORIGINS: `http://localhost:${WEB}`,
      },
    },
    {
      command: `pnpm build && pnpm start -p ${WEB}`,
      url: `http://localhost:${WEB}/login`,
      reuseExistingServer: !process.env.CI,
      timeout: 240_000,
      env: publicEnv,
    },
  ],
});
