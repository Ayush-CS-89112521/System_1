import path from "node:path";
import { fileURLToPath } from "node:url";
import { randomUUID } from "node:crypto";
import express from "express";
import axios from "axios";
import Database from "better-sqlite3";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const workspaceRoot = path.resolve(__dirname, "..", "..", "..");

const PORT = Number(process.env.PORT || "3000");
const DB_PATH = process.env.SHARED_DB_PATH || path.join(workspaceRoot, ".ops", "shared.db");
const UPSTREAM_URL = process.env.LLM_UPSTREAM_URL || "https://api.openai.com/v1/chat/completions";
const UPSTREAM_API_KEY = process.env.LLM_UPSTREAM_API_KEY || "";
const MAX_DAILY_BUDGET = Number(process.env.MAX_DAILY_BUDGET || "20");
const MAX_TOKENS_PER_REQ = Number(process.env.MAX_TOKENS_PER_REQ || "8192");
const PROMPT_TOKEN_RATE = Number(process.env.PROMPT_TOKEN_RATE || "0.0000025");
const COMPLETION_TOKEN_RATE = Number(process.env.COMPLETION_TOKEN_RATE || "0.00001");

const app = express();
app.use(express.json({ limit: "2mb" }));

const db = new Database(DB_PATH);
db.pragma("journal_mode = WAL");
db.pragma("busy_timeout = 5000");

function ensureSchema() {
  db.exec(`
    CREATE TABLE IF NOT EXISTS automation_gates (
      gate_id TEXT PRIMARY KEY,
      is_active INTEGER NOT NULL CHECK (is_active IN (0, 1)),
      failure_count INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS budget_policy (
      policy_id TEXT PRIMARY KEY,
      max_daily_budget REAL NOT NULL,
      max_tokens_per_request INTEGER NOT NULL,
      prompt_token_rate REAL NOT NULL,
      completion_token_rate REAL NOT NULL,
      updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS spend_ledger (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      request_id TEXT,
      actor_id TEXT,
      prompt_tokens INTEGER NOT NULL DEFAULT 0,
      completion_tokens INTEGER NOT NULL DEFAULT 0,
      cost REAL NOT NULL DEFAULT 0.0,
      status TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS agent_logs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
      agent_id TEXT NOT NULL,
      action_type TEXT NOT NULL,
      file_path TEXT,
      diff_hash TEXT,
      intent_description TEXT
    );
  `);

  db.prepare(`
    INSERT INTO automation_gates (gate_id, is_active, failure_count)
    VALUES ('global_kill_switch', 1, 0)
    ON CONFLICT(gate_id) DO NOTHING
  `).run();

  db.prepare(`
    INSERT INTO budget_policy (
      policy_id,
      max_daily_budget,
      max_tokens_per_request,
      prompt_token_rate,
      completion_token_rate
    )
    VALUES ('default', @maxDailyBudget, @maxTokensPerRequest, @promptRate, @completionRate)
    ON CONFLICT(policy_id) DO UPDATE SET
      max_daily_budget = excluded.max_daily_budget,
      max_tokens_per_request = excluded.max_tokens_per_request,
      prompt_token_rate = excluded.prompt_token_rate,
      completion_token_rate = excluded.completion_token_rate,
      updated_at = CURRENT_TIMESTAMP
  `).run({
    maxDailyBudget: MAX_DAILY_BUDGET,
    maxTokensPerRequest: MAX_TOKENS_PER_REQ,
    promptRate: PROMPT_TOKEN_RATE,
    completionRate: COMPLETION_TOKEN_RATE
  });
}

function estimatePromptTokens(body) {
  const messages = Array.isArray(body?.messages) ? body.messages : [];
  const text = messages.map((m) => String(m?.content || "")).join("\n");
  return Math.ceil(text.length / 4);
}

function getPolicy() {
  return db.prepare(`
    SELECT max_daily_budget, max_tokens_per_request, prompt_token_rate, completion_token_rate
    FROM budget_policy
    WHERE policy_id = 'default'
  `).get();
}

function getTodaySpend() {
  const row = db.prepare(`
    SELECT COALESCE(SUM(cost), 0.0) AS total
    FROM spend_ledger
    WHERE date(timestamp) = date('now')
  `).get();
  return Number(row?.total || 0);
}

function isGateActive() {
  const row = db.prepare(`
    SELECT is_active
    FROM automation_gates
    WHERE gate_id = 'global_kill_switch'
  `).get();
  return Number(row?.is_active || 0) === 1;
}

function writeLog(actionType, intentDescription, actorId = "safety-proxy") {
  db.prepare(`
    INSERT INTO agent_logs (agent_id, action_type, file_path, intent_description)
    VALUES (@agentId, @actionType, @filePath, @intentDescription)
  `).run({
    agentId: actorId,
    actionType,
    filePath: "/v1/chat/completions",
    intentDescription
  });
}

app.get("/health", (_req, res) => {
  try {
    const spend = getTodaySpend();
    const policy = getPolicy();
    res.json({
      ok: true,
      gateActive: isGateActive(),
      spendToday: spend,
      maxDailyBudget: policy?.max_daily_budget ?? MAX_DAILY_BUDGET
    });
  } catch (error) {
    res.status(503).json({ ok: false, error: `health check failed: ${error.message}` });
  }
});

app.post("/v1/chat/completions", async (req, res) => {
  const actorId = String(req.header("x-agent-id") || "agent");
  const requestId = String(req.header("x-request-id") || randomUUID());

  try {
    if (!UPSTREAM_API_KEY) {
      writeLog("proxy_reject", "missing upstream API key", actorId);
      res.status(401).json({ error: "Missing upstream API key" });
      return;
    }

    if (!isGateActive()) {
      writeLog("proxy_reject", "automation gate is inactive", actorId);
      res.status(503).json({ error: "Automation gate is disabled" });
      return;
    }

    const policy = getPolicy();
    const reqPromptTokens = estimatePromptTokens(req.body);
    const reqMaxTokens = Number(req.body?.max_tokens || 0);
    const effectiveMaxTokens = reqMaxTokens > 0 ? reqMaxTokens : reqPromptTokens;

    if (effectiveMaxTokens > Number(policy?.max_tokens_per_request || MAX_TOKENS_PER_REQ)) {
      writeLog(
        "proxy_reject",
        `request exceeds max tokens per request (${effectiveMaxTokens})`,
        actorId
      );
      res.status(400).json({ error: "Request exceeds MAX_TOKENS_PER_REQ" });
      return;
    }

    const spendToday = getTodaySpend();
    const maxBudget = Number(policy?.max_daily_budget || MAX_DAILY_BUDGET);
    if (spendToday > maxBudget) {
      writeLog("proxy_reject", `budget exceeded: spend=${spendToday} max=${maxBudget}`, actorId);
      res.status(402).json({ error: "Daily budget exceeded" });
      return;
    }

    const upstream = await axios.post(UPSTREAM_URL, req.body, {
      headers: {
        Authorization: `Bearer ${UPSTREAM_API_KEY}`,
        "Content-Type": "application/json"
      },
      timeout: 60000
    });

    const usage = upstream.data?.usage || {};
    const promptTokens = Number(usage.prompt_tokens || reqPromptTokens || 0);
    const completionTokens = Number(usage.completion_tokens || 0);

    const promptRate = Number(policy?.prompt_token_rate || PROMPT_TOKEN_RATE);
    const completionRate = Number(policy?.completion_token_rate || COMPLETION_TOKEN_RATE);
    const cost = (promptTokens * promptRate) + (completionTokens * completionRate);

    db.prepare(`
      INSERT INTO spend_ledger (
        request_id,
        actor_id,
        prompt_tokens,
        completion_tokens,
        cost,
        status
      ) VALUES (@requestId, @actorId, @promptTokens, @completionTokens, @cost, @status)
    `).run({
      requestId,
      actorId,
      promptTokens,
      completionTokens,
      cost,
      status: "ok"
    });

    writeLog(
      "proxy_forward",
      `forwarded request cost=${cost.toFixed(6)} prompt=${promptTokens} completion=${completionTokens}`,
      actorId
    );

    res.status(upstream.status).json(upstream.data);
  } catch (error) {
    const status = Number(error?.response?.status || 503);
    const message = String(error?.response?.data?.error?.message || error?.message || "proxy failure");

    db.prepare(`
      INSERT INTO spend_ledger (
        request_id,
        actor_id,
        prompt_tokens,
        completion_tokens,
        cost,
        status
      ) VALUES (@requestId, @actorId, 0, 0, 0.0, @status)
    `).run({
      requestId,
      actorId,
      status: `error:${status}`
    });

    writeLog("proxy_error", `upstream error status=${status} message=${message}`, actorId);
    res.status(status).json({ error: message });
  }
});

function start() {
  ensureSchema();
  app.listen(PORT, "127.0.0.1", () => {
    // Safety-by-failure model: agents must call this local endpoint.
    // If this service is down, requests fail and do not bypass.
    console.log(`Safety proxy listening on http://127.0.0.1:${PORT}`);
    console.log(`SQLite DB: ${DB_PATH}`);
  });
}

start();
