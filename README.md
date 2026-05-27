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
│   ├── TZ.md                  ← технічне завдання
│   └── REPORT.md              ← звіт з результатами
├── data/
│   └── sku_sales_dataset.csv  ← синтетичний датасет
├── scripts/
│   ├── generate_dataset.py    ← генерація датасету
│   └── build_notebook.py      ← збірка notebook
├── notebook/
│   └── sku_sales_forecast.ipynb
└── outputs/
    ├── metrics_results.csv
    ├── metrics_by_category.csv
    ├── forecast_results.csv
    ├── order_quantity.csv
    └── 01_…04_*.png           ← графіки
```

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
