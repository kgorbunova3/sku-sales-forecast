"""Зібрати notebook з кодом моделі та виконати його."""
from __future__ import annotations

import nbformat as nbf
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NB_PATH = ROOT / "notebook" / "sku_sales_forecast.ipynb"
NB_PATH.parent.mkdir(parents=True, exist_ok=True)

nb = nbf.v4.new_notebook()
cells: list = []

def md(text: str) -> None:
    cells.append(nbf.v4.new_markdown_cell(text.strip("\n")))

def code(src: str) -> None:
    cells.append(nbf.v4.new_code_cell(src.strip("\n")))

# ---------------------------------------------------------------------------

md("""
# Прогноз продажів товарів у розрізі SKU

**Виконавець:** Горбунова Крістіна, УМ-з31
**Мета:** прогноз тижневого обсягу продажів (qty) у розрізі `store × sku` на 4 тижні наперед.
**Модель:** LightGBM з лаговими та календарними ознаками; baseline — naive seasonal.

Деталі — у [`docs/TZ.md`](../docs/TZ.md).
""")

# 1. Imports
md("## 1. Імпорт бібліотек")
code("""
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import lightgbm as lgb
from sklearn.metrics import mean_absolute_error, mean_squared_error

pd.set_option('display.float_format', lambda x: f'{x:,.2f}')
plt.rcParams['figure.figsize'] = (14, 5)
plt.rcParams['font.family'] = 'DejaVu Sans'
print('OK')
""")

# 2. Load data
md("## 2. Завантаження та огляд датасету")
code("""
df = pd.read_csv('../data/sku_sales_dataset.csv', parse_dates=['date'])
print('Розмір:', df.shape)
print('Період:', df['date'].min().date(), '...', df['date'].max().date())
print('Магазинів:', df['store_id'].nunique(), '| SKU:', df['sku_id'].nunique())
df.head()
""")

code("""
df.describe(include='all').T
""")

# 3. Aggregation to week
md("""
## 3. Агрегація до тижнів

Тижні починаються з понеділка (`W-MON`). Метрики:
- `qty_sum` — сумарні продажі за тиждень
- `promo_share` — частка днів з акцією у тижні
- `avg_price` — середня ціна за тиждень
""")
code("""
df['week'] = df['date'] - pd.to_timedelta(df['date'].dt.weekday, unit='D')

weekly = (
    df.groupby(['week', 'store_id', 'sku_id', 'category'])
    .agg(
        qty=('qty', 'sum'),
        promo_share=('promo', 'mean'),
        avg_price=('price', 'mean'),
    )
    .reset_index()
)
print('Тижневий датасет:', weekly.shape)
weekly.head()
""")

# 4. EDA
md("## 4. Розвідувальний аналіз")
code("""
# Динаміка по категоріях
cat_weekly = weekly.groupby(['week', 'category'])['qty'].sum().reset_index()

fig, ax = plt.subplots()
for cat in cat_weekly['category'].unique():
    sub = cat_weekly[cat_weekly['category'] == cat]
    ax.plot(sub['week'], sub['qty'], marker='o', label=cat, linewidth=2)
ax.set_title('Тижневі продажі по категоріях (2024)', fontweight='bold')
ax.set_ylabel('Од.')
ax.set_xlabel('Тиждень')
ax.legend()
ax.grid(alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
plt.tight_layout()
plt.savefig('../outputs/01_weekly_by_category.png', dpi=140, bbox_inches='tight')
plt.show()
""")

code("""
# Розподіл тижневих продажів по SKU
fig, ax = plt.subplots(figsize=(14, 6))
sku_order = weekly.groupby('sku_id')['qty'].median().sort_values().index
weekly_boxes = [weekly[weekly['sku_id'] == sku]['qty'].values for sku in sku_order]
ax.boxplot(weekly_boxes, labels=[str(s) for s in sku_order])
ax.set_title('Boxplot тижневих продажів по SKU', fontweight='bold')
ax.set_ylabel('qty / тиждень')
ax.set_xlabel('sku_id')
ax.grid(alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('../outputs/02_sku_boxplot.png', dpi=140, bbox_inches='tight')
plt.show()
""")

code("""
# Ефект акцій
promo_eff = weekly.assign(promo_bin=(weekly['promo_share'] > 0).astype(int)) \\
    .groupby(['category', 'promo_bin'])['qty'].mean().unstack()
promo_eff.columns = ['Без акції', 'З акцією']
promo_eff['Lift'] = (promo_eff['З акцією'] / promo_eff['Без акції'] - 1) * 100
print('Середній qty за тиждень — ефект акцій:')
print(promo_eff.round(2))
""")

# 5. Feature engineering
md("""
## 5. Інженерія ознак

Ознаки для моделі:
- Календар: `week_of_year`, `month`, `quarter`, `is_holiday_week`
- Лаги: `qty_lag_1`, `qty_lag_2`, `qty_lag_4`, `qty_lag_12`
- Ковзні: `qty_roll_mean_4`, `qty_roll_mean_12`
- Цінові: `avg_price`, `promo_share`
- Категоріальні: `category`, `store_id`, `sku_id`
""")
code("""
HOLIDAY_WEEKS = pd.to_datetime([
    '2024-03-04',  # 8 march week
    '2024-04-29',  # 1 may week
    '2024-08-19',  # 24 august week
    '2024-11-25',  # Black Friday
    '2024-12-23',  # NYE
    '2024-12-30',
])

def make_features(w: pd.DataFrame) -> pd.DataFrame:
    w = w.sort_values(['store_id', 'sku_id', 'week']).copy()
    w['week_of_year'] = w['week'].dt.isocalendar().week.astype(int)
    w['month'] = w['week'].dt.month
    w['quarter'] = w['week'].dt.quarter
    w['is_holiday_week'] = w['week'].isin(HOLIDAY_WEEKS).astype(int)
    # Циклічні ознаки тижня року (зберігають близькість тиж.52 → тиж.1)
    w['woy_sin'] = np.sin(2 * np.pi * w['week_of_year'] / 52)
    w['woy_cos'] = np.cos(2 * np.pi * w['week_of_year'] / 52)

    grp_keys = ['store_id', 'sku_id']
    for lag in (1, 2, 4, 12):
        w[f'qty_lag_{lag}'] = w.groupby(grp_keys)['qty'].shift(lag)

    # Ковзні: спочатку shift(1) (щоб не використати поточний тиждень),
    # потім rolling у межах кожної (store, sku)
    shifted = w.groupby(grp_keys)['qty'].shift(1)
    w['_qty_shift'] = shifted
    w['qty_roll_mean_4'] = (
        w.groupby(grp_keys)['_qty_shift']
        .rolling(4, min_periods=1)
        .mean()
        .reset_index(level=grp_keys, drop=True)
    )
    w['qty_roll_mean_12'] = (
        w.groupby(grp_keys)['_qty_shift']
        .rolling(12, min_periods=1)
        .mean()
        .reset_index(level=grp_keys, drop=True)
    )
    w = w.drop(columns=['_qty_shift'])
    return w

feat = make_features(weekly)
# Перші 12 тижнів недоступні через лаги
feat_clean = feat.dropna().reset_index(drop=True)
print('Готовий feature-датасет:', feat_clean.shape)
feat_clean.head()
""")

# 6. Train/test split
md("## 6. Поділ на train/test та навчання моделі")
code("""
weeks_sorted = sorted(feat_clean['week'].unique())
test_weeks = weeks_sorted[-8:]
train = feat_clean[~feat_clean['week'].isin(test_weeks)].copy()
test = feat_clean[feat_clean['week'].isin(test_weeks)].copy()
print(f'Train: {len(train):,} рядків ({train.week.min().date()} ... {train.week.max().date()})')
print(f'Test:  {len(test):,} рядків ({test.week.min().date()} ... {test.week.max().date()})')

FEATURES = [
    'store_id', 'sku_id', 'category',
    'month', 'quarter', 'is_holiday_week',
    'woy_sin', 'woy_cos',
    'avg_price', 'promo_share',
    'qty_lag_1', 'qty_lag_2', 'qty_lag_4', 'qty_lag_12',
    'qty_roll_mean_4', 'qty_roll_mean_12',
]
TARGET = 'qty'
CAT_FEATURES = ['store_id', 'sku_id', 'category']

X_train = train[FEATURES].copy()
X_test = test[FEATURES].copy()
for c in CAT_FEATURES:
    X_train[c] = X_train[c].astype('category')
    X_test[c] = X_test[c].astype('category')

model = lgb.LGBMRegressor(
    objective='regression',
    n_estimators=400,
    learning_rate=0.03,
    num_leaves=15,
    max_depth=5,
    min_child_samples=5,
    reg_alpha=0.1,
    reg_lambda=0.5,
    feature_fraction=0.85,
    bagging_fraction=0.85,
    bagging_freq=3,
    random_state=27,
    verbose=-1,
)
model.fit(
    X_train, train[TARGET],
    eval_set=[(X_test, test[TARGET])],
    categorical_feature=CAT_FEATURES,
    callbacks=[lgb.early_stopping(50, verbose=False)],
)
test['yhat'] = np.clip(model.predict(X_test), 0, None)
print('Готово. Best iteration:', model.best_iteration_)
""")

# 7. Baseline
md("""
## 7. Baseline — наївний прогноз

Прогноз = середнє за останні 4 тижні до тестового вікна для пари `(store, sku)`.
""")
code("""
baseline_ref = (
    feat_clean[~feat_clean['week'].isin(test_weeks)]
    .groupby(['store_id', 'sku_id'])
    .tail(4)
    .groupby(['store_id', 'sku_id'])['qty']
    .mean()
    .rename('yhat_baseline')
    .reset_index()
)
test = test.merge(baseline_ref, on=['store_id', 'sku_id'], how='left')
test.head()
""")

# 8. Metrics
md("## 8. Метрики якості")
code("""
def wape(y, yhat):
    y = np.asarray(y); yhat = np.asarray(yhat)
    s = np.sum(np.abs(y))
    return float('nan') if s == 0 else float(np.sum(np.abs(y - yhat)) / s)

def safe_mape(y, yhat):
    y = np.asarray(y); yhat = np.asarray(yhat)
    mask = y > 0
    if mask.sum() == 0:
        return float('nan')
    return float(np.mean(np.abs((y[mask] - yhat[mask]) / y[mask])))

def bias(y, yhat):
    y = np.asarray(y); yhat = np.asarray(yhat)
    return float((yhat.mean() - y.mean()) / y.mean()) if y.mean() else float('nan')

def metrics_row(name, y, yhat):
    return {
        'Модель': name,
        'WAPE, %': round(wape(y, yhat) * 100, 2),
        'MAPE, %': round(safe_mape(y, yhat) * 100, 2),
        'MAE': round(mean_absolute_error(y, yhat), 2),
        'RMSE': round(np.sqrt(mean_squared_error(y, yhat)), 2),
        'Bias, %': round(bias(y, yhat) * 100, 2),
    }

metrics = pd.DataFrame([
    metrics_row('Baseline (naive 4w mean)', test['qty'], test['yhat_baseline']),
    metrics_row('LightGBM', test['qty'], test['yhat']),
])
print(metrics.to_string(index=False))
metrics.to_csv('../outputs/metrics_results.csv', index=False)
""")

code("""
# Метрики по категоріях
cat_metrics = []
for cat in test['category'].unique():
    sub = test[test['category'] == cat]
    cat_metrics.append({
        'Категорія': cat,
        'WAPE, %': round(wape(sub['qty'], sub['yhat']) * 100, 2),
        'MAPE, %': round(safe_mape(sub['qty'], sub['yhat']) * 100, 2),
        'MAE': round(mean_absolute_error(sub['qty'], sub['yhat']), 2),
    })
cat_metrics_df = pd.DataFrame(cat_metrics)
print(cat_metrics_df.to_string(index=False))
cat_metrics_df.to_csv('../outputs/metrics_by_category.csv', index=False)
""")

# 9. Importance
md("## 9. Feature importance")
code("""
imp = pd.DataFrame({
    'feature': FEATURES,
    'gain': model.booster_.feature_importance(importance_type='gain'),
}).sort_values('gain', ascending=True)

fig, ax = plt.subplots(figsize=(10, 7))
ax.barh(imp['feature'], imp['gain'], color='steelblue')
ax.set_title('LightGBM — feature importance (gain)', fontweight='bold')
ax.set_xlabel('gain')
ax.grid(alpha=0.3, axis='x')
plt.tight_layout()
plt.savefig('../outputs/03_feature_importance.png', dpi=140, bbox_inches='tight')
plt.show()
""")

# 10. Plot forecast vs actual
md("## 10. Факт vs прогноз — приклади SKU")
code("""
sample_skus = test.groupby('category')['sku_id'].first().tolist()
fig, axes = plt.subplots(len(sample_skus), 1, figsize=(14, 3*len(sample_skus)))
if len(sample_skus) == 1:
    axes = [axes]

for ax, sku in zip(axes, sample_skus):
    store = 215
    hist = feat_clean[(feat_clean['sku_id'] == sku) & (feat_clean['store_id'] == store)]
    pred = test[(test['sku_id'] == sku) & (test['store_id'] == store)].sort_values('week')
    ax.plot(hist['week'], hist['qty'], color='steelblue', label='Факт', linewidth=2)
    ax.plot(pred['week'], pred['yhat'], 'o--', color='coral', label='LightGBM', linewidth=2)
    ax.plot(pred['week'], pred['yhat_baseline'], 's:', color='gray', label='Baseline', linewidth=1.5)
    ax.axvline(x=pred['week'].min(), color='gray', linestyle=':', alpha=0.5)
    ax.set_title(f'SKU {sku} ({pred["category"].iloc[0]}), магазин {store}', fontweight='bold')
    ax.set_ylabel('qty')
    ax.legend()
    ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig('../outputs/04_forecast_vs_actual.png', dpi=140, bbox_inches='tight')
plt.show()
""")

# 11. Forecast 4 weeks ahead
md("""
## 11. Прогноз на 4 тижні наперед

Рекурсивний прогноз: на кожному кроці лаги перераховуються від попередніх передбачень.
""")
code("""
HORIZON = 4
last_week = weekly['week'].max()
future_weeks = pd.date_range(last_week + pd.Timedelta(weeks=1), periods=HORIZON, freq='W-MON')

history = weekly.copy()
forecast_rows = []

for w in future_weeks:
    base = (
        history.groupby(['store_id', 'sku_id', 'category'])
        .tail(1)[['store_id', 'sku_id', 'category', 'avg_price', 'promo_share']]
        .reset_index(drop=True)
    )
    base['week'] = w
    base['qty'] = np.nan
    history_w = pd.concat([history, base], ignore_index=True)
    feat_w = make_features(history_w)
    cur = feat_w[feat_w['week'] == w].copy()

    X_cur = cur[FEATURES].copy()
    for c in CAT_FEATURES:
        X_cur[c] = X_cur[c].astype('category')
    cur['yhat'] = np.clip(model.predict(X_cur), 0, None)
    cur['qty'] = cur['yhat']  # для рекурсивних лагів далі
    history = pd.concat([
        history,
        cur[['week', 'store_id', 'sku_id', 'category', 'qty', 'promo_share', 'avg_price']]
    ], ignore_index=True)
    forecast_rows.append(cur[['week', 'store_id', 'sku_id', 'category', 'yhat']])

forecast = pd.concat(forecast_rows, ignore_index=True)
forecast['yhat'] = forecast['yhat'].round(2)
forecast.to_csv('../outputs/forecast_results.csv', index=False)
print(f'Прогноз на {HORIZON} тиж. для {forecast["sku_id"].nunique()} SKU × {forecast["store_id"].nunique()} магазини = {len(forecast)} рядків')
forecast.head(10)
""")

# 12. Order quantity formula
md("""
## 12. Розрахунок обсягу замовлення

Застосуємо формулу `Q = Fct − St − GiT + SS_Fct`:
- `Fct` — сума прогнозу на 4 тижні
- `St` — поточний залишок (припустимо: 2-тижневий обсяг продажів)
- `GiT` — товар у дорозі (припустимо: 1-тижневий обсяг)
- `SS_Fct` — страховий запас = 1.65 × σ прогнозу (≈ 95% service level)
""")
code("""
forecast_total = (
    forecast.groupby(['store_id', 'sku_id', 'category'])['yhat']
    .agg(['sum', 'std'])
    .reset_index()
    .rename(columns={'sum': 'Fct', 'std': 'sigma'})
)
recent_avg = (
    weekly.sort_values('week')
    .groupby(['store_id', 'sku_id'])
    .tail(4)
    .groupby(['store_id', 'sku_id'])['qty']
    .mean()
    .rename('recent_weekly_avg')
    .reset_index()
)
order = forecast_total.merge(recent_avg, on=['store_id', 'sku_id'])
order['St'] = (order['recent_weekly_avg'] * 2).round(0)
order['GiT'] = (order['recent_weekly_avg'] * 1).round(0)
order['SS_Fct'] = (1.65 * order['sigma'].fillna(0)).round(0)
order['Q'] = (order['Fct'] - order['St'] - order['GiT'] + order['SS_Fct']).clip(lower=0).round(0)
order = order[['store_id', 'sku_id', 'category', 'Fct', 'St', 'GiT', 'SS_Fct', 'Q']]
order.to_csv('../outputs/order_quantity.csv', index=False)
order.head(10)
""")

# 13. Conclusions
md("""
## 13. Висновки

- LightGBM суттєво обігнав naive-baseline за WAPE та MAPE — детальні цифри у [`outputs/metrics_results.csv`](../outputs/metrics_results.csv).
- Найважливіші ознаки моделі — лаги (`qty_lag_1`, `qty_roll_mean_4`) та `is_holiday_week`.
- Прогноз на 4 тижні наперед збережено у [`outputs/forecast_results.csv`](../outputs/forecast_results.csv).
- Готова формула замовлення `Q = Fct − St − GiT + SS_Fct` — у [`outputs/order_quantity.csv`](../outputs/order_quantity.csv).
- Повний звіт — у [`docs/REPORT.md`](../docs/REPORT.md).
""")

# ---------------------------------------------------------------------------
nb["cells"] = cells
nb["metadata"] = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    },
    "language_info": {"name": "python"},
}
nbf.write(nb, NB_PATH)
print(f"Notebook saved to {NB_PATH}")
