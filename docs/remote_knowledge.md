# Optional remote knowledge service

PharmDS can proxy informational RAG/LLM queries to a separate server. This
service is intentionally isolated from deterministic interaction analysis.
`/analyze` never calls the remote knowledge service.

Environment variables:

- `PHARMDS_RAG_ENABLED=true` enables the integration.
- `PHARMDS_RAG_BASE_URL=http://<vlan-host>:<port>` points PharmDS to the server.
- `PHARMDS_RAG_API_KEY=<token>` is optional and sent as a Bearer token.
- `PHARMDS_RAG_TIMEOUT_SECONDS=5` controls the request timeout.

Remote service contract:

- `GET /health` returns JSON and may include `model` and `detail`.
- `POST /query` accepts `{"query": "...", "top_k": 5}`.
- `/query` returns `{"answer": "...", "sources": [...], "model": "..."}`.

RAG output is informational only and must not alter deterministic PharmDS rule
results or mechanism-pipeline output.
