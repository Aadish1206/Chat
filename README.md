# Backend-first Chatbot Service (FastAPI)

## Environment setup

Create a local `.env` file (already included in this repo for convenience) and update values as needed:

```bash
cp .env.example .env
```

Set `OPENAI_API_KEY` if you want LLM-backed planning. Leaving it blank keeps deterministic fallback behavior.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn apps.api.main:app --reload --port 8000
# Optional richer web UI
uvicorn app:app --reload --port 8000
```

## Sample chat request

```bash
curl -s -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "domain":"CPG",
    "org":"UL",
    "usecase":"SKUReorder",
    "message":"Recommend reorder quantities for risky SKUs this month",
    "top_n": 5
  }' | jq
```

## Endpoints

- `GET /catalog/domains`
- `GET /catalog/orgs?domain=CPG`
- `GET /catalog/usecases?domain=CPG&org=PG`
- `POST /chat`

## Architecture note

- **Canonical runtime path (active API):** `apps/api/*` -> `runtime/*` -> `domain_layer.py` -> `data/*`.
- The legacy `core/*` path remains in the repo for reference, but new endpoint behavior is implemented on the runtime path above.
- Domain/org/usecase compatibility filtering is driven by `data/compatibility.json`.

## Artifact compatibility

The runtime supports both:
- the lightweight PoC artifact payloads currently in `data/*/artifacts.json`, and
- the canonical envelope format (including glossary `content.terms`, data_bindings `tables` + `columns`, and prompt_assets `content.prompts`).

