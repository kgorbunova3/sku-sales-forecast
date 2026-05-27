# Прогноз продажу товарів у розрізі SKU

> Навчальний проект курсу «Бізнес-прогнозування», група УМ-з31.
> **Виконавець:** Горбунова Крістіна.

**Розріз прогнозування:** продажу товарів — тижневий горизонт, гранулярність SKU × магазин.

## Файли проекту

| Що | Файл |
|---|---|
| Технічне завдання | [`docs/TZ_marketplace.docx`](docs/TZ_marketplace.docx) |
| Фінальний реферат (підсумок робіт) | [`docs/Referat.docx`](docs/Referat.docx) |
| Презентація для захисту | [`docs/presentation.pptx`](docs/presentation.pptx) |
| Схема БД (ER-діаграма) | [`docs/db_schema.png`](docs/db_schema.png) |
| SQL DDL + JOIN-запит | [`docs/sql_queries.md`](docs/sql_queries.md) |
| Тестові дані для БД | [`data/db/db_sample_data.xlsx`](data/db/db_sample_data.xlsx) |
| Основний датасет | [`data/sku_sales_dataset.csv`](data/sku_sales_dataset.csv) |
| Notebook з моделлю | [`notebook/sku_sales_forecast.ipynb`](notebook/sku_sales_forecast.ipynb) |
| Метрики моделі | [`outputs/metrics_results.csv`](outputs/metrics_results.csv) |
| Прогноз на 4 тижні | [`outputs/forecast_results.csv`](outputs/forecast_results.csv) |
| План замовлення (Q) | [`outputs/order_quantity.csv`](outputs/order_quantity.csv) |
| Графіки | [`outputs/`](outputs/) |

## Модель

LightGBM з лаговими та календарними ознаками. Baseline — наївний прогноз (середнє за 4 тижні).
WAPE 25,24% (LightGBM) vs 25,53% (Baseline). Деталі — в реферат.

## Kanban

Задачі проекту — у [GitHub Project](https://github.com/users/kgorbunova3/projects/1):
[#1 ТЗ](../../issues/1) · [#2 Датасет](../../issues/2) · [#3 Модель](../../issues/3) · [#4 Метрики](../../issues/4) · [#5 Звіт](../../issues/5)
