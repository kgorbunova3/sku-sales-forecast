# SKU Sales Forecast

> Прогноз продажів товарів на тиждень наперед у розрізі **SKU × магазин**.
> Навчальний проект курсу «Бізнес-прогнозування», група УМ-з31.

**Автор:** Горбунова Крістіна
**Розріз прогнозування:** Прогноз продажу товарів (SKU, weekly).

## Структура проекту

```
sku-sales-forecast/
├── README.md
├── docs/
│   ├── TZ.md                  ← технічне завдання (коротке)
│   ├── TZ_marketplace.docx    ← розгорнуте ТЗ за шаблоном (20 розділів)
│   ├── REPORT.md              ← звіт з результатами
│   ├── presentation.pptx      ← презентація для захисту (12 слайдів)
│   ├── db_schema.md           ← опис схеми БД + mermaid ER
│   ├── db_schema.drawio       ← ER-діаграма (drawio)
│   └── sql_queries.md         ← DDL + JOIN-запит для формування dataset
├── data/
│   ├── sku_sales_dataset.csv  ← основний синтетичний датасет (10 980 рядків)
│   └── db/                    ← набір таблиць БД (dim + fact)
│       ├── db_sample_data.xlsx  ← всі таблиці в одному файлі
│       ├── dim_category.csv
│       ├── dim_sku.csv
│       ├── dim_store.csv
│       ├── dim_holidays.csv
│       ├── dim_promo_calendar.csv
│       ├── sales_fact.csv
│       ├── inventory_snapshot.csv
│       └── dataset.csv         ← фінальна view-таблиця (JOIN)
├── scripts/
│   ├── generate_dataset.py    ← генерація основного датасету
│   ├── generate_db_tables.py  ← генерація таблиць БД
│   ├── build_drawio_schema.py ← збірка drawio
│   ├── build_notebook.py      ← збірка notebook
│   ├── build_marketplace_tz.py
│   └── build_presentation.py
├── notebook/
│   └── sku_sales_forecast.ipynb
└── outputs/
    ├── metrics_results.csv
    ├── metrics_by_category.csv
    ├── forecast_results.csv
    ├── order_quantity.csv
    └── 01_…04_*.png           ← графіки
```

## Схема БД

Повна ER-діаграма + опис JOIN-логіки — у [`docs/db_schema.md`](docs/db_schema.md)
(рендериться як інтерактивний mermaid прямо в GitHub).
Drawio-файл для редагування: [`docs/db_schema.drawio`](docs/db_schema.drawio).

## Швидкий старт

```bash
python -m venv .venv
source .venv/bin/activate          # macOS: ще `brew install libomp`
pip install pandas numpy matplotlib scikit-learn lightgbm jupyter nbformat nbconvert

python scripts/generate_dataset.py
python scripts/build_notebook.py
jupyter nbconvert --to notebook --execute notebook/sku_sales_forecast.ipynb --output notebook/sku_sales_forecast.ipynb
```

## Модель

- **Основна:** LightGBM з лаговими + календарними ознаками.
- **Baseline:** наївний прогноз = середнє за останні 4 тижні.
- **Горизонт:** 4 тижні наперед, рекурсивно.
- **Метрики:** WAPE 25.24% (LightGBM) проти 25.53% (Baseline). Деталі — у [`REPORT.md`](docs/REPORT.md).

## Kanban / задачі проекту

Робота розбита на 5 задач у [GitHub Project](https://github.com/users/kgorbunova3/projects/):

| # | Issue | Артефакт |
|---|---|---|
| 1 | [Написання ТЗ](../../issues/1) | [`docs/TZ.md`](docs/TZ.md) |
| 2 | [Формування Датасету](../../issues/2) | [`data/sku_sales_dataset.csv`](data/sku_sales_dataset.csv) |
| 3 | [Вибір та запуск моделі](../../issues/3) | [`notebook/sku_sales_forecast.ipynb`](notebook/sku_sales_forecast.ipynb) |
| 4 | [Вибір та оцінка метрик](../../issues/4) | [`outputs/metrics_results.csv`](outputs/metrics_results.csv) |
| 5 | [Формування звіту з результатами](../../issues/5) | [`docs/REPORT.md`](docs/REPORT.md) |
