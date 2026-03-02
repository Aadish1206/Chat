from __future__ import annotations


def run_nl2sql(_: dict) -> dict:
    rows = [
        {"sku": "SKU-100", "sales": 180, "stock": 45, "stockouts": 4, "lead_time_days": 10},
        {"sku": "SKU-220", "sales": 120, "stock": 30, "stockouts": 2, "lead_time_days": 7},
        {"sku": "SKU-451", "sales": 210, "stock": 22, "stockouts": 5, "lead_time_days": 14},
    ]
    return {"rows": rows, "source": "warehouse.mock.sales_inventory"}
