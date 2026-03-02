# Backend-first Chatbot Service (FastAPI)

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn apps.api.main:app --reload --port 8000
```

## Sample chat request

```bash
curl -s -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "session_id":"s1",
    "domain":"CPG",
    "org":"PG",
    "usecase":"SKUReorder",
    "message":"Recommend reorder quantities for risky SKUs this month"
  }' | jq
```

## Endpoints

- `GET /catalog/domains`
- `GET /catalog/orgs?domain=CPG`
- `GET /catalog/usecases?domain=CPG&org=PG`
- `POST /chat`
