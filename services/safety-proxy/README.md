# Safety Proxy

Fail-closed local proxy for AI model traffic.

## Endpoint

- `POST /v1/chat/completions`
- `GET /health`

## Safety Contract

1. Missing upstream API key: returns `401`
2. Request exceeds max tokens: returns `400`
3. Global automation gate off: returns `503`
4. Daily budget exceeded: returns `402`
5. Proxy unavailable: agents must fail, never bypass

## Environment Variables

- `PORT` default `3000`
- `SHARED_DB_PATH` default workspace `.ops/shared.db`
- `LLM_UPSTREAM_URL` default OpenAI-compatible URL
- `LLM_UPSTREAM_API_KEY` required
- `MAX_DAILY_BUDGET` default `20`
- `MAX_TOKENS_PER_REQ` default `8192`
- `PROMPT_TOKEN_RATE` default `0.0000025`
- `COMPLETION_TOKEN_RATE` default `0.00001`

## Run

```bash
pnpm --filter safety-proxy start
```
