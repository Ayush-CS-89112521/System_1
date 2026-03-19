# Safety Proxy

## Objective

Create a local financial and logic guardrail between agents and upstream LLM providers.

## Runtime Contract

1. Agents call `http://127.0.0.1:3000/v1/chat/completions`
2. Agents do not bypass the proxy
3. If proxy is down, agent requests fail by design

## Endpoint Behavior

`POST /v1/chat/completions`

1. Missing upstream API key: `401`
2. Request exceeds max token policy: `400`
3. Global automation gate is off: `503`
4. Daily budget exceeded: `402`
5. Allowed request: forwards upstream and returns provider response

`GET /health`

- Returns gate status and spend summary

## Budget Sources

SQLite database `.ops/shared.db`:

- `budget_policy`
- `spend_ledger`
- `automation_gates`

## Cost Formula

`cost = prompt_tokens * prompt_token_rate + completion_tokens * completion_token_rate`

Rates are read from `budget_policy` and can be updated without code changes.

## Environment

- `PORT` default `3000`
- `SHARED_DB_PATH` default workspace `.ops/shared.db`
- `LLM_UPSTREAM_URL` OpenAI-compatible completion endpoint
- `LLM_UPSTREAM_API_KEY` required
- `MAX_DAILY_BUDGET` default `20`
- `MAX_TOKENS_PER_REQ` default `8192`
- `PROMPT_TOKEN_RATE` default `0.0000025`
- `COMPLETION_TOKEN_RATE` default `0.00001`

## Startup

```bash
pnpm --filter safety-proxy start
```

## Fail-Closed Requirement

Keep all agent configs pinned to local proxy URL. Do not permit direct upstream API URL in agent runtime for normal operation.
