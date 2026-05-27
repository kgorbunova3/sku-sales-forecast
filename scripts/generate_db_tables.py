"""
Генерує сім таблиць для входу в модель прогнозування SKU.

Зберігає у:
  - data/db/db_sample_data.xlsx (всі таблиці в окремих листах)
  - data/db/<table>.csv         (кожна таблиця окремо)
"""
from __future__ import annotations

import random
from pathlib import Path
from datetime import date, timedelta

import numpy as np
import pandas as pd

RNG = np.random.default_rng(seed=27)
random.seed(27)

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "db"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# =========================================================================
# 1. dim_category
# =========================================================================
dim_category = pd.DataFrame([
    {"category_id": 80001, "category_name": "Ноутбуки",     "m_path": "80000:80001"},
    {"category_id": 80002, "category_name": "Смартфони",    "m_path": "80000:80002"},
    {"category_id": 80003, "category_name": "Холодильники", "m_path": "80000:80003"},
])

# =========================================================================
# 2. dim_sku
# =========================================================================
SKU_RANGE = list(range(64500, 64515))  # 15 SKU
BRANDS = {
    80001: ["Lenovo", "ASUS", "Acer", "HP", "Apple"],
    80002: ["Samsung", "Xiaomi", "Apple", "Google", "OnePlus"],
    80003: ["Samsung", "LG", "Bosch", "Whirlpool", "Beko"],
}
PRICE_RANGE = {
    80001: (18000, 42000),
    80002: (9000, 35000),
    80003: (15000, 38000),
}
WEIGHT_RANGE = {
    80001: (1.4, 2.8),
    80002: (0.15, 0.25),
    80003: (45.0, 95.0),
}

dim_sku_rows = []
for i, sku_id in enumerate(SKU_RANGE):
    cat_id = [80001, 80002, 80003][i // 5]
    brand = BRANDS[cat_id][i % 5]
    price_lo, price_hi = PRICE_RANGE[cat_id]
    w_lo, w_hi = WEIGHT_RANGE[cat_id]
    dim_sku_rows.append({
        "sku_id": sku_id,
        "sku_name": f"{brand} model {sku_id % 1000:03d}",
        "category_id": cat_id,
        "brand": brand,
        "weight_kg": round(float(RNG.uniform(w_lo, w_hi)), 2),
        "unit_price": float(RNG.integers(price_lo, price_hi + 1)),
        "is_active": True,
    })
dim_sku = pd.DataFrame(dim_sku_rows)

# =========================================================================
# 3. dim_store
# =========================================================================
dim_store = pd.DataFrame([
    {"store_id": 215, "store_name": "Marketplace FC Kyiv-Brovary",
     "city": "Київ", "region": "Київська область",
     "manager_name": "Олексій Іванов",
     "manager_email": "kyiv-fc@marketplace.ua"},
    {"store_id": 312, "store_name": "Marketplace FC Lviv-West",
     "city": "Львів", "region": "Львівська область",
     "manager_name": "Марія Шевченко",
     "manager_email": "lviv-fc@marketplace.ua"},
])

# =========================================================================
# 4. dim_holidays
# =========================================================================
dim_holidays = pd.DataFrame([
    {"holiday_date": date(2024, 1, 1),  "holiday_name": "Новий рік",         "country": "UA", "is_promo_period": True},
    {"holiday_date": date(2024, 1, 7),  "holiday_name": "Різдво",            "country": "UA", "is_promo_period": False},
    {"holiday_date": date(2024, 3, 8),  "holiday_name": "Міжнародний жіночий день", "country": "UA", "is_promo_period": True},
    {"holiday_date": date(2024, 5, 1),  "holiday_name": "День праці",        "country": "UA", "is_promo_period": True},
    {"holiday_date": date(2024, 5, 9),  "holiday_name": "День перемоги",     "country": "UA", "is_promo_period": False},
    {"holiday_date": date(2024, 6, 28), "holiday_name": "День Конституції",  "country": "UA", "is_promo_period": False},
    {"holiday_date": date(2024, 8, 24), "holiday_name": "День Незалежності", "country": "UA", "is_promo_period": True},
    {"holiday_date": date(2024, 11, 29),"holiday_name": "Black Friday",      "country": "UA", "is_promo_period": True},
    {"holiday_date": date(2024, 12, 2), "holiday_name": "Cyber Monday",      "country": "UA", "is_promo_period": True},
    {"holiday_date": date(2024, 12, 24),"holiday_name": "Святий вечір",      "country": "UA", "is_promo_period": True},
    {"holiday_date": date(2024, 12, 31),"holiday_name": "Переддень Нового року", "country": "UA", "is_promo_period": True},
])

# =========================================================================
# 5. dim_promo_calendar
# =========================================================================
PROMO_REASONS = ["Знижка тижня", "Чорна п'ятниця", "Сезонна акція", "Liquidation",
                 "Партнерська знижка", "Cyber Monday", "Святковий розпродаж"]

# 100 промо за рік
promo_rows = []
promo_id = 5000
days = pd.date_range("2024-01-01", "2024-12-31").to_list()
for _ in range(100):
    sku_id = int(RNG.choice(SKU_RANGE))
    store_id = int(RNG.choice([215, 312]))
    start = random.choice(days)
    duration = int(RNG.integers(1, 8))
    end = start + pd.Timedelta(days=duration)
    discount = int(RNG.choice([5, 10, 15, 20, 25, 30]))
    promo_rows.append({
        "promo_id": promo_id,
        "sku_id": sku_id,
        "store_id": store_id,
        "start_date": start.date(),
        "end_date": end.date(),
        "discount_pct": discount,
        "reason": random.choice(PROMO_REASONS),
    })
    promo_id += 1
dim_promo_calendar = pd.DataFrame(promo_rows).sort_values("start_date").reset_index(drop=True)

# =========================================================================
# 6. sales_fact (100 строк sample)
# =========================================================================
sales_rows = []
sales_id = 100000
for _ in range(100):
    d = random.choice(days)
    sku_id = int(RNG.choice(SKU_RANGE))
    store_id = int(RNG.choice([215, 312]))
    cat_id = dim_sku.loc[dim_sku.sku_id == sku_id, "category_id"].iloc[0]
    base_qty = {80001: 4, 80002: 12, 80003: 3}[cat_id]
    qty = int(RNG.poisson(base_qty))
    base_price = float(dim_sku.loc[dim_sku.sku_id == sku_id, "unit_price"].iloc[0])
    promo = int(RNG.random() < 0.1)
    price = round(base_price * (0.9 if promo else 1.0) * float(RNG.normal(1.0, 0.02)), 2)
    sales_rows.append({
        "sales_id": sales_id,
        "sales_date": d.date(),
        "sku_id": sku_id,
        "store_id": store_id,
        "qty": qty,
        "price": price,
        "promo": bool(promo),
        "amount": round(qty * price, 2),
    })
    sales_id += 1
sales_fact = pd.DataFrame(sales_rows).sort_values(["sales_date", "store_id", "sku_id"]).reset_index(drop=True)

# =========================================================================
# 7. inventory_snapshot (100 строк sample)
# =========================================================================
inv_rows = []
inv_id = 200000
for _ in range(100):
    d = random.choice(days)
    sku_id = int(RNG.choice(SKU_RANGE))
    store_id = int(RNG.choice([215, 312]))
    qty_on_hand = int(RNG.integers(0, 80))
    qty_in_transit = int(RNG.integers(0, 40))
    inv_rows.append({
        "inventory_id": inv_id,
        "snapshot_date": d.date(),
        "sku_id": sku_id,
        "store_id": store_id,
        "qty_on_hand": qty_on_hand,
        "qty_in_transit": qty_in_transit,
        "last_updated_ts": pd.Timestamp(d) + pd.Timedelta(hours=int(RNG.integers(0, 24))),
    })
    inv_id += 1
inventory_snapshot = pd.DataFrame(inv_rows).sort_values(
    ["snapshot_date", "store_id", "sku_id"]
).reset_index(drop=True)

# =========================================================================
# 8. dataset (фінальний — приклад 100 рядків через JOIN)
# =========================================================================
def build_dataset_sample() -> pd.DataFrame:
    s = sales_fact.copy()
    s = s.merge(dim_sku[["sku_id", "category_id", "brand", "weight_kg"]], on="sku_id", how="left")
    s = s.merge(dim_category[["category_id", "category_name"]], on="category_id", how="left")
    s = s.merge(dim_store[["store_id", "city", "region"]], on="store_id", how="left")
    # Прапор свята
    holiday_dates = set(dim_holidays["holiday_date"])
    s["is_holiday"] = s["sales_date"].isin(holiday_dates)
    # Тиждень (понеділок)
    s["week_start_date"] = pd.to_datetime(s["sales_date"]) - pd.to_timedelta(
        pd.to_datetime(s["sales_date"]).dt.weekday, unit="D"
    )
    s["week_start_date"] = s["week_start_date"].dt.date
    cols = [
        "sales_date", "week_start_date", "sku_id", "store_id",
        "category_id", "category_name", "brand", "weight_kg",
        "city", "region",
        "qty", "price", "amount", "promo", "is_holiday",
    ]
    return s[cols]


dataset = build_dataset_sample()

# =========================================================================
# Збереження
# =========================================================================
TABLES = {
    "dim_category":       dim_category,
    "dim_sku":            dim_sku,
    "dim_store":          dim_store,
    "dim_holidays":       dim_holidays,
    "dim_promo_calendar": dim_promo_calendar,
    "sales_fact":         sales_fact,
    "inventory_snapshot": inventory_snapshot,
    "dataset":            dataset,
}

# CSV-файли
for name, df in TABLES.items():
    df.to_csv(OUT_DIR / f"{name}.csv", index=False)

# Один XLSX з листами
xlsx_path = OUT_DIR / "db_sample_data.xlsx"
with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
    for name, df in TABLES.items():
        df.to_excel(writer, sheet_name=name[:31], index=False)

print(f"Saved {len(TABLES)} tables to {OUT_DIR}")
for name, df in TABLES.items():
    print(f"  {name:22s} {len(df):4d} rows × {len(df.columns):2d} cols")
