# Cogentiq Domain Layer PoC Chatbot

This project provides a working end-to-end chatbot runtime that uses local filesystem artifacts under `./data` and DomainLayer orchestration.

## How to run

1) Create sample local registry data
```bash
python3 setup_data.py
```

2) CLI mode
```bash
python3 chat.py
```

3) FastAPI web mode
```bash
uvicorn app:app --reload --port 8000
```

4) Example API call
```bash
curl -s -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"domain":"CPG","org":"UL","usecase":"SKUReorder","message":"How should I plan SKU reorder for January in EU region?"}'
```

## Runtime flow implemented
- Domain/org/usecase resolution via `DomainLayer.query_orchestrate_async(...)`
- Excludes `knowledgebase` and `evaluation-assets`
- Uses resolved `tools` as allowed toolset
- Validates tool input with JSON Schema
- Executes local demo tools (`nl2sql`, `reorder_planner`, `reorder_risk_simulator`)
- Returns final answer with Sources, tools, and trace
- Deterministic fallback when `OPENAI_API_KEY` is not set

## End-to-end example conversation
Selection:
- domain: `CPG`
- org: `UL`
- usecase: `SKUReorder`

User:
> How should I plan SKU reorder for January in EU region?

Tool calls:
1. `nl2sql` with question + data_context (tables + filters)
2. `reorder_planner` to format markdown plan

Assistant (example):
- Deterministic fallback analysis generated.
- Pseudo SQL references `sku_daily` and filters `region='EU'` and `month='January'`.
- Reorder guidance and tool output summaries included.

Sources:
- `domain/CPG/artifacts.json`
- `org/UL/artifacts.json`
- `usecase/SKUReorder/artifacts.json`
