from __future__ import annotations


def run_reorder_planner(payload: dict) -> dict:
    rows = payload.get("rows", [])
    output_rows = []
    for row in rows:
        reorder_qty = max(int(row["sales"] * (row["lead_time_days"] / 30.0) + row["stockouts"] * 10 - row["stock"]), 0)
        output_rows.append({"sku": row["sku"], "reorder_qty": reorder_qty, "reason": "Lead time + stockout risk"})

    md = "| SKU | Reorder Qty | Reason |\n|---|---:|---|\n"
    for row in output_rows:
        md += f"| {row['sku']} | {row['reorder_qty']} | {row['reason']} |\n"
    return {"table_markdown": md, "rows": output_rows, "source": "reorder-planner.stub"}
