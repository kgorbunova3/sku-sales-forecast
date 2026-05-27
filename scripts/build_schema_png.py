"""Генерує PNG ER-діаграми через Graphviz."""
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_PNG = ROOT / "docs" / "db_schema.png"
OUT_DOT = ROOT / "docs" / "db_schema.dot"

NAVY = "#0E2D5C"
ACCENT = "#E76F51"
MUTED = "#666666"
BG = "#F5F5F5"

TABLES = {
    "dim_category": [
        ("category_id", "INT", "PK"),
        ("category_name", "VARCHAR(50)", ""),
        ("m_path", "VARCHAR(50)", ""),
    ],
    "dim_sku": [
        ("sku_id", "INT", "PK"),
        ("sku_name", "VARCHAR(80)", ""),
        ("category_id", "INT", "FK"),
        ("brand", "VARCHAR(50)", ""),
        ("weight_kg", "DECIMAL(6,2)", ""),
        ("unit_price", "DECIMAL(10,2)", ""),
        ("is_active", "BOOLEAN", ""),
    ],
    "dim_store": [
        ("store_id", "INT", "PK"),
        ("store_name", "VARCHAR(80)", ""),
        ("city", "VARCHAR(50)", ""),
        ("region", "VARCHAR(50)", ""),
        ("manager_name", "VARCHAR(80)", ""),
        ("manager_email", "VARCHAR(80)", ""),
    ],
    "dim_holidays": [
        ("holiday_date", "DATE", "PK"),
        ("holiday_name", "VARCHAR(80)", ""),
        ("country", "CHAR(2)", ""),
        ("is_promo_period", "BOOLEAN", ""),
    ],
    "dim_promo_calendar": [
        ("promo_id", "INT", "PK"),
        ("sku_id", "INT", "FK"),
        ("store_id", "INT", "FK"),
        ("start_date", "DATE", ""),
        ("end_date", "DATE", ""),
        ("discount_pct", "INT", ""),
        ("reason", "VARCHAR(80)", ""),
    ],
    "sales_fact": [
        ("sales_id", "BIGINT", "PK"),
        ("sales_date", "DATE", ""),
        ("sku_id", "INT", "FK"),
        ("store_id", "INT", "FK"),
        ("qty", "INT", ""),
        ("price", "DECIMAL(10,2)", ""),
        ("promo", "BOOLEAN", ""),
        ("amount", "DECIMAL(12,2)", ""),
    ],
    "inventory_snapshot": [
        ("inventory_id", "BIGINT", "PK"),
        ("snapshot_date", "DATE", ""),
        ("sku_id", "INT", "FK"),
        ("store_id", "INT", "FK"),
        ("qty_on_hand", "INT", ""),
        ("qty_in_transit", "INT", ""),
        ("last_updated_ts", "TIMESTAMP", ""),
    ],
    "dataset": [
        ("sales_date", "DATE", ""),
        ("week_start_date", "DATE", ""),
        ("sku_id", "INT", "FK"),
        ("store_id", "INT", "FK"),
        ("category_id", "INT", "FK"),
        ("category_name", "VARCHAR(50)", ""),
        ("brand", "VARCHAR(50)", ""),
        ("weight_kg", "DECIMAL(6,2)", ""),
        ("city", "VARCHAR(50)", ""),
        ("region", "VARCHAR(50)", ""),
        ("qty", "INT", ""),
        ("price", "DECIMAL(10,2)", ""),
        ("amount", "DECIMAL(12,2)", ""),
        ("promo", "BOOLEAN", ""),
        ("is_holiday", "BOOLEAN", ""),
    ],
}

EDGES = [
    ("dim_sku", "category_id", "dim_category", "category_id"),
    ("dim_promo_calendar", "sku_id", "dim_sku", "sku_id"),
    ("dim_promo_calendar", "store_id", "dim_store", "store_id"),
    ("sales_fact", "sku_id", "dim_sku", "sku_id"),
    ("sales_fact", "store_id", "dim_store", "store_id"),
    ("inventory_snapshot", "sku_id", "dim_sku", "sku_id"),
    ("inventory_snapshot", "store_id", "dim_store", "store_id"),
]
# JOIN-зв'язки до dataset (підсвічуємо помаранчевим)
JOIN_EDGES = [
    ("dataset", "sku_id", "sales_fact", "sku_id"),
    ("dataset", "category_id", "dim_category", "category_id"),
    ("dataset", "store_id", "dim_store", "store_id"),
]


def html_label(name: str, cols: list[tuple[str, str, str]], header_color: str) -> str:
    lines = [
        f'<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="6">',
        f'  <TR><TD BGCOLOR="{header_color}" COLSPAN="3"><FONT COLOR="white"><B>{name}</B></FONT></TD></TR>',
    ]
    for col, type_, key in cols:
        key_html = f'<FONT COLOR="{ACCENT}"><B>{key}</B></FONT>' if key else ""
        lines.append(
            f'  <TR>'
            f'<TD WIDTH="40" ALIGN="CENTER" PORT="{col}">{key_html}</TD>'
            f'<TD ALIGN="LEFT">{col}</TD>'
            f'<TD ALIGN="LEFT"><FONT COLOR="{MUTED}">{type_}</FONT></TD>'
            f'</TR>'
        )
    lines.append("</TABLE>>")
    return "\n".join(lines)


dot_lines = [
    'digraph DB {',
    '  rankdir=LR;',
    '  graph [bgcolor="white", pad="0.5", nodesep="0.8", ranksep="1.6", splines="spline", concentrate=false];',
    '  node [shape=plaintext, fontname="Helvetica", fontsize=12];',
    '  edge [fontname="Helvetica", fontsize=10, color="' + NAVY + '", penwidth=1.4];',
    '',
]

for name, cols in TABLES.items():
    color = ACCENT if name == "dataset" else NAVY
    dot_lines.append(f'  {name} [label={html_label(name, cols, color)}];')

dot_lines.append('')
for src_t, src_c, dst_t, dst_c in EDGES:
    dot_lines.append(
        f'  {src_t}:{src_c}:e -> {dst_t}:{dst_c}:w '
        f'[label="N : 1", arrowhead=crow, arrowtail=none];'
    )

for src_t, src_c, dst_t, dst_c in JOIN_EDGES:
    dot_lines.append(
        f'  {src_t}:{src_c}:e -> {dst_t}:{dst_c}:w '
        f'[label="JOIN", color="{ACCENT}", fontcolor="{ACCENT}", style="dashed", arrowhead=open];'
    )

dot_lines.append('}')

OUT_DOT.parent.mkdir(parents=True, exist_ok=True)
OUT_DOT.write_text("\n".join(dot_lines), encoding="utf-8")
print(f"DOT saved to {OUT_DOT}")

subprocess.run(
    ["dot", "-Tpng", "-Gdpi=150", str(OUT_DOT), "-o", str(OUT_PNG)],
    check=True,
)
print(f"PNG saved to {OUT_PNG}")
