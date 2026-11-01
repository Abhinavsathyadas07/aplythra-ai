// Minimal stand-in for Supabase Auth (GoTrue), used ONLY by the end-to-end tests.
// It signs real RS256 JWTs and serves a JWKS, so the real FastAPI backend verifies them
// exactly as it would with Supabase. Never used in the app itself.
import crypto from "node:crypto";
import http from "node:http";

const PORT = Number(process.env.FAKE_SUPABASE_PORT ?? 54321);
const BASE = `http://localhost:${PORT}`;
const ISSUER = `${BASE}/auth/v1`;
const KID = "e2e-key-1";

const { publicKey, privateKey } = crypto.generateKeyPairSync("rsa", { modulusLength: 2048 });
const jwk = { ...publicKey.export({ format: "jwk" }), kid: KID, alg: "RS256", use: "sig" };

const b64 = (value) => Buffer.from(typeof value === "string" ? value : JSON.stringify(value)).toString("base64url");

function sign(claims) {
  const input = `${b64({ alg: "RS256", typ: "JWT", kid: KID })}.${b64(claims)}`;
  const signature = crypto.sign("RSA-SHA256", Buffer.from(input), privateKey).toString("base64url");
  return `${input}.${signature}`;
}

function verify(token) {
  const [header, payload, signature] = (token ?? "").split(".");
  if (!header || !payload || !signature) return null;
  const ok = crypto.verify("RSA-SHA256", Buffer.from(`${header}.${payload}`), publicKey, Buffer.from(signature, "base64url"));
  if (!ok) return null;
  const claims = JSON.parse(Buffer.from(payload, "base64url").toString());
  return claims.exp > Math.floor(Date.now() / 1000) ? claims : null;
}

const users = new Map(); // email -> { id, email, password }
const refreshTokens = new Map(); // refresh token -> email

const publicUser = (user) => ({
  id: user.id,
  aud: "authenticated",
  role: "authenticated",
  email: user.email,
  app_metadata: { provider: "email" },
  user_metadata: {},
  created_at: user.createdAt,
});

function session(user) {
  const now = Math.floor(Date.now() / 1000);
  const expiresIn = Number(process.env.FAKE_TOKEN_TTL ?? 3600);
  const accessToken = sign({
    iss: ISSUER, aud: "authenticated", sub: user.id, email: user.email,
    role: "authenticated", iat: now, exp: now + expiresIn, session_id: crypto.randomUUID(),
  });
  const refreshToken = crypto.randomBytes(16).toString("hex");
  refreshTokens.set(refreshToken, user.email);
  return {
    access_token: accessToken, token_type: "bearer", expires_in: expiresIn,
    expires_at: now + expiresIn, refresh_token: refreshToken, user: publicUser(user),
  };
}

async function readJson(req) {
  const chunks = [];
  for await (const chunk of req) chunks.push(chunk);
  try { return JSON.parse(Buffer.concat(chunks).toString() || "{}"); } catch { return {}; }
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, BASE);
  const send = (status, body) => {
    res.writeHead(status, {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": req.headers.origin ?? "*",
      "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info, x-supabase-api-version",
      "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
      "Access-Control-Allow-Credentials": "true",
    });
    res.end(body === undefined ? undefined : JSON.stringify(body));
  };

  if (req.method === "OPTIONS") return send(204);
  if (url.pathname === "/health") return send(200, { ok: true });
  if (url.pathname === "/auth/v1/.well-known/jwks.json") return send(200, { keys: [jwk] });

  if (url.pathname === "/auth/v1/token" && req.method === "POST") {
    const body = await readJson(req);
    const grant = url.searchParams.get("grant_type");
    if (grant === "password") {
      const user = users.get(String(body.email ?? "").toLowerCase());
      if (!user || user.password !== body.password) {
        return send(400, { code: 400, error_code: "invalid_credentials", error: "invalid_grant", error_description: "Invalid login credentials", msg: "Invalid login credentials" });
      }
      return send(200, session(user));
    }
    if (grant === "refresh_token") {
      const email = refreshTokens.get(body.refresh_token);
      const user = email && users.get(email);
      if (!user) return send(400, { code: 400, error_code: "refresh_token_not_found", msg: "Invalid Refresh Token" });
      refreshTokens.delete(body.refresh_token);
      return send(200, session(user));
    }
    return send(400, { msg: "unsupported grant_type" });
  }

  if (url.pathname === "/auth/v1/signup" && req.method === "POST") {
    const body = await readJson(req);
    const email = String(body.email ?? "").toLowerCase();
    if (!email || String(body.password ?? "").length < 8) return send(422, { code: 422, error_code: "weak_password", msg: "Password too short" });
    if (users.has(email)) return send(422, { code: 422, error_code: "user_already_exists", msg: "User already registered" });
    const user = { id: crypto.randomUUID(), email, password: body.password, createdAt: new Date().toISOString() };
    users.set(email, user);
    return send(200, session(user)); // auto-confirm, like a Supabase project with confirmations off
  }

  if (url.pathname === "/auth/v1/user" && req.method === "GET") {
    const claims = verify((req.headers.authorization ?? "").replace(/^Bearer /, ""));
    const user = claims && [...users.values()].find((u) => u.id === claims.sub);
    return user ? send(200, publicUser(user)) : send(401, { code: 401, msg: "invalid JWT" });
  }

  if (url.pathname === "/auth/v1/logout" && req.method === "POST") return send(204);

  return send(404, { msg: "not found" });
});

server.listen(PORT, () => console.log(`fake supabase listening on ${BASE}`));
