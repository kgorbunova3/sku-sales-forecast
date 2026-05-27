"""Генерує ER-діаграму у форматі .drawio (app.diagrams.net)."""
from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "docs" / "db_schema.drawio"

# -------------------------------------------------------------------------
# Описи таблиць — порядок полів важливий
# Колонки: (name, type, key)  key ∈ {"PK", "FK", "PK,FK", ""}
# -------------------------------------------------------------------------
TABLES: dict[str, list[tuple[str, str, str]]] = {
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

# Позиції таблиць на полотні (x, y)
POSITIONS = {
    "dim_category":       (60,   60),
    "dim_sku":            (60,   320),
    "dim_store":          (60,   700),
    "dim_holidays":       (550,  60),
    "dim_promo_calendar": (550,  320),
    "sales_fact":         (1050, 320),
    "inventory_snapshot": (1050, 700),
    "dataset":            (1550, 320),
}

# Зв'язки: (from_table, from_col, to_table, to_col, label)
RELATIONS = [
    ("dim_sku", "category_id", "dim_category", "category_id", "N : 1"),
    ("dim_promo_calendar", "sku_id", "dim_sku", "sku_id", "N : 1"),
    ("dim_promo_calendar", "store_id", "dim_store", "store_id", "N : 1"),
    ("sales_fact", "sku_id", "dim_sku", "sku_id", "N : 1"),
    ("sales_fact", "store_id", "dim_store", "store_id", "N : 1"),
    ("inventory_snapshot", "sku_id", "dim_sku", "sku_id", "N : 1"),
    ("inventory_snapshot", "store_id", "dim_store", "store_id", "N : 1"),
    ("dataset", "sku_id", "sales_fact", "sku_id", "JOIN"),
    ("dataset", "category_id", "dim_category", "category_id", "JOIN"),
    ("dataset", "store_id", "dim_store", "store_id", "JOIN"),
]

# -------------------------------------------------------------------------
# Стилі (фірмові кольори)
# -------------------------------------------------------------------------
HEADER_STYLE = (
    "shape=table;startSize=30;container=1;collapsible=0;childLayout=tableLayout;"
    "fontSize=14;fillColor=#0E2D5C;strokeColor=#0E2D5C;fontColor=#FFFFFF;"
    "fontStyle=1;align=center;"
)
HEADER_STYLE_DATASET = HEADER_STYLE.replace("#0E2D5C", "#E76F51")
ROW_STYLE = (
    "shape=tableRow;horizontal=0;startSize=0;swimlaneHead=0;swimlaneBody=0;strokeColor=inherit;"
    "top=0;left=0;bottom=0;right=0;collapsible=0;dropTarget=0;fillColor=none;points=[[0,0.5],[1,0.5]];"
    "portConstraint=eastwest;fontSize=12;"
)
CELL_KEY_STYLE = (
    "shape=partialRectangle;html=1;whiteSpace=wrap;connectable=0;strokeColor=inherit;overflow=hidden;"
    "fillColor=none;top=0;left=0;bottom=0;right=0;pointerEvents=1;fontSize=12;fontStyle=4;fontColor=#E76F51;align=center;"
)
CELL_NAME_STYLE = (
    "shape=partialRectangle;html=1;whiteSpace=wrap;connectable=0;strokeColor=inherit;overflow=hidden;"
    "fillColor=none;top=0;left=0;bottom=0;right=0;pointerEvents=1;fontSize=12;align=left;spacingLeft=6;"
)
CELL_TYPE_STYLE = (
    "shape=partialRectangle;html=1;whiteSpace=wrap;connectable=0;strokeColor=inherit;overflow=hidden;"
    "fillColor=none;top=0;left=0;bottom=0;right=0;pointerEvents=1;fontSize=11;align=left;spacingLeft=6;fontColor=#666666;"
)
EDGE_STYLE = (
    "edgeStyle=entityRelationEdgeStyle;fontSize=11;html=1;endArrow=ERmany;startArrow=ERone;"
    "rounded=0;exitX=0;exitY=0.5;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;strokeColor=#0E2D5C;"
)
EDGE_STYLE_JOIN = (
    "edgeStyle=entityRelationEdgeStyle;fontSize=11;html=1;endArrow=open;startArrow=open;"
    "rounded=0;exitX=0;exitY=0.5;exitDx=0;exitDy=0;entryX=1;entryY=0.5;entryDx=0;entryDy=0;"
    "strokeColor=#E76F51;dashed=1;"
)

ROW_H = 26
HEADER_H = 30
TABLE_W = 360
COL_W_NAME = 180
COL_W_TYPE = 130
COL_W_KEY = 50

# -------------------------------------------------------------------------
# Генерація XML
# -------------------------------------------------------------------------
cells: list[str] = []
row_id_map: dict[tuple[str, str], str] = {}  # (table, col) -> id рядка


def add_cell(xml: str) -> None:
    cells.append(xml)


def make_table(name: str, cols: list[tuple[str, str, str]], x: int, y: int) -> None:
    height = HEADER_H + ROW_H * len(cols)
    table_id = f"t_{name}"
    style = HEADER_STYLE_DATASET if name == "dataset" else HEADER_STYLE
    add_cell(
        f'<mxCell id="{table_id}" value="{escape(name)}" style="{style}" '
        f'vertex="1" parent="1">'
        f'<mxGeometry x="{x}" y="{y}" width="{TABLE_W}" height="{height}" as="geometry"/>'
        f'</mxCell>'
    )
    for i, (col_name, col_type, key) in enumerate(cols):
        row_id = f"r_{name}_{col_name}"
        row_id_map[(name, col_name)] = row_id
        add_cell(
            f'<mxCell id="{row_id}" value="" style="{ROW_STYLE}" '
            f'vertex="1" parent="{table_id}">'
            f'<mxGeometry y="{HEADER_H + i*ROW_H}" width="{TABLE_W}" height="{ROW_H}" as="geometry"/>'
            f'</mxCell>'
        )
        # Key column
        add_cell(
            f'<mxCell id="{row_id}_k" value="{escape(key)}" style="{CELL_KEY_STYLE}" '
            f'vertex="1" parent="{row_id}">'
            f'<mxGeometry width="{COL_W_KEY}" height="{ROW_H}" as="geometry"/>'
            f'</mxCell>'
        )
        # Name
        add_cell(
            f'<mxCell id="{row_id}_n" value="{escape(col_name)}" style="{CELL_NAME_STYLE}" '
            f'vertex="1" parent="{row_id}">'
            f'<mxGeometry x="{COL_W_KEY}" width="{COL_W_NAME}" height="{ROW_H}" as="geometry"/>'
            f'</mxCell>'
        )
        # Type
        add_cell(
            f'<mxCell id="{row_id}_t" value="{escape(col_type)}" style="{CELL_TYPE_STYLE}" '
            f'vertex="1" parent="{row_id}">'
            f'<mxGeometry x="{COL_W_KEY + COL_W_NAME}" width="{COL_W_TYPE}" height="{ROW_H}" as="geometry"/>'
            f'</mxCell>'
        )


def make_edge(src_t: str, src_c: str, dst_t: str, dst_c: str, label: str, idx: int) -> None:
    src = row_id_map[(src_t, src_c)]
    dst = row_id_map[(dst_t, dst_c)]
    style = EDGE_STYLE_JOIN if label == "JOIN" else EDGE_STYLE
    add_cell(
        f'<mxCell id="e_{idx}" value="{escape(label)}" style="{style}" '
        f'edge="1" parent="1" source="{src}" target="{dst}">'
        f'<mxGeometry relative="1" as="geometry"/>'
        f'</mxCell>'
    )


# Будуємо таблиці
for name, cols in TABLES.items():
    x, y = POSITIONS[name]
    make_table(name, cols, x, y)

# Будуємо зв'язки
for i, rel in enumerate(RELATIONS):
    make_edge(*rel, idx=i)

# Загорнути в обгортку drawio
inner = "\n".join(cells)
xml = f'''<mxfile host="app.diagrams.net" version="24.0.0" type="device">
  <diagram name="DB Schema — SKU Sales Forecast" id="sku-db-schema">
    <mxGraphModel dx="2400" dy="1200" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="2200" pageHeight="1400" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        {inner}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
'''

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUT_PATH.write_text(xml, encoding="utf-8")
print(f"Saved {OUT_PATH} ({len(cells)} cells)")
