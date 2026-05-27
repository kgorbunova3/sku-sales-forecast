"""
Генерація синтетичного датасету продажів SKU.

Структура:
- 2 магазини (store_id: 215, 312)
- 3 категорії × 5 SKU = 15 SKU
- Період: 2024-01-01 ... 2024-12-31 (366 днів)
- Колонки: date, store_id, sku_id, category, qty, price, promo
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path

RNG = np.random.default_rng(seed=27)

STORES = [215, 312]
CATEGORIES = {
    "Ноутбуки":      {"sku_count": 5, "base_qty": (3, 8),   "base_price": (18000, 42000), "promo_lift": 1.6, "season": "q4"},
    "Смартфони":     {"sku_count": 5, "base_qty": (8, 20),  "base_price": (9000,  35000), "promo_lift": 1.8, "season": "q4"},
    "Холодильники":  {"sku_count": 5, "base_qty": (2, 5),   "base_price": (15000, 38000), "promo_lift": 1.4, "season": "summer"},
}

START = pd.Timestamp("2024-01-01")
END = pd.Timestamp("2024-12-31")
DAYS = pd.date_range(START, END, freq="D")

HOLIDAYS = {
    pd.Timestamp("2024-03-08"),
    pd.Timestamp("2024-05-01"),
    pd.Timestamp("2024-08-24"),
    pd.Timestamp("2024-11-29"),  # Black Friday
    pd.Timestamp("2024-12-24"),
    pd.Timestamp("2024-12-31"),
}


def seasonal_multiplier(date: pd.Timestamp, season_type: str) -> float:
    month = date.month
    if season_type == "q4":
        # Зростання до листопаду-грудню
        return 1.0 + 0.35 * np.sin((month - 3) / 12 * 2 * np.pi)
    if season_type == "summer":
        # Пік влітку
        return 1.0 + 0.25 * np.sin((month - 1) / 12 * 2 * np.pi)
    return 1.0


def weekday_multiplier(date: pd.Timestamp) -> float:
    # Уівх — вс: 1.0, 1.0, 1.0, 1.05, 1.15, 1.35, 1.20
    weights = [1.0, 1.0, 1.0, 1.05, 1.15, 1.35, 1.20]
    return weights[date.weekday()]


def holiday_lift(date: pd.Timestamp) -> float:
    if date in HOLIDAYS:
        return 1.8
    if any((date - h).days in (-2, -1, 1, 2) for h in HOLIDAYS):
        return 1.25
    return 1.0


def build_rows() -> list[dict]:
    rows: list[dict] = []
    sku_meta: dict[str, dict] = {}

    # SKU метадані
    sku_counter = 64500
    for category, cfg in CATEGORIES.items():
        for i in range(cfg["sku_count"]):
            sku_id = sku_counter
            sku_counter += 1
            base_qty = RNG.integers(cfg["base_qty"][0], cfg["base_qty"][1] + 1)
            base_price = float(RNG.integers(cfg["base_price"][0], cfg["base_price"][1] + 1))
            sku_meta[sku_id] = {
                "category": category,
                "base_qty": base_qty,
                "base_price": base_price,
                "promo_lift": cfg["promo_lift"],
                "season": cfg["season"],
            }

    for date in DAYS:
        for store in STORES:
            # Магазин 312 трохи менший за обсягом
            store_mult = 1.0 if store == 215 else 0.72
            for sku_id, meta in sku_meta.items():
                # Шанс акції ~7%
                promo = int(RNG.random() < 0.07)
                lambda_qty = (
                    meta["base_qty"]
                    * store_mult
                    * seasonal_multiplier(date, meta["season"])
                    * weekday_multiplier(date)
                    * holiday_lift(date)
                    * (meta["promo_lift"] if promo else 1.0)
                )
                qty = int(RNG.poisson(lambda_qty))
                # Ціна: -10% під час акції, ±3% шум
                price = meta["base_price"] * (0.9 if promo else 1.0)
                price *= float(RNG.normal(1.0, 0.03))
                price = round(price, 2)

                rows.append(
                    {
                        "date": date.date().isoformat(),
                        "store_id": store,
                        "sku_id": sku_id,
                        "category": meta["category"],
                        "qty": qty,
                        "price": price,
                        "promo": promo,
                    }
                )
    return rows


def main() -> None:
    out_dir = Path(__file__).resolve().parents[1] / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = build_rows()
    df = pd.DataFrame(rows)
    out_path = out_dir / "sku_sales_dataset.csv"
    df.to_csv(out_path, index=False)

    print(f"Записано {len(df):,} рядків у {out_path}")
    print(f"Період: {df['date'].min()} ... {df['date'].max()}")
    print(f"SKU: {df['sku_id'].nunique()}, магазинів: {df['store_id'].nunique()}")
    print(df.head())


if __name__ == "__main__":
    main()
