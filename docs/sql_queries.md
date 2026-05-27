# SQL — створення таблиць та формування Датасету

> Файл супроводжує ER-діаграму [`db_schema.drawio`](db_schema.drawio).
> Тестові дані для кожної таблиці — у [`../data/db/db_sample_data.xlsx`](../data/db/db_sample_data.xlsx).

---

## 1. Створення таблиць (DDL)

```sql
-- ============================================================
-- ДОВІДНИКИ (dim)
-- ============================================================
CREATE TABLE dim_category (
  category_id   INT          PRIMARY KEY,
  category_name VARCHAR(50)  NOT NULL,
  m_path        VARCHAR(50)
);

CREATE TABLE dim_sku (
  sku_id      INT          PRIMARY KEY,
  sku_name    VARCHAR(80)  NOT NULL,
  category_id INT          NOT NULL,
  brand       VARCHAR(50),
  weight_kg   DECIMAL(6,2),
  unit_price  DECIMAL(10,2) NOT NULL,
  is_active   BOOLEAN      DEFAULT TRUE,
  FOREIGN KEY (category_id) REFERENCES dim_category(category_id)
);

CREATE TABLE dim_store (
  store_id      INT         PRIMARY KEY,
  store_name    VARCHAR(80) NOT NULL,
  city          VARCHAR(50),
  region        VARCHAR(50),
  manager_name  VARCHAR(80),
  manager_email VARCHAR(80)
);

CREATE TABLE dim_holidays (
  holiday_date    DATE         PRIMARY KEY,
  holiday_name    VARCHAR(80)  NOT NULL,
  country         CHAR(2)      DEFAULT 'UA',
  is_promo_period BOOLEAN      DEFAULT FALSE
);

CREATE TABLE dim_promo_calendar (
  promo_id     INT          PRIMARY KEY,
  sku_id       INT          NOT NULL,
  store_id     INT          NOT NULL,
  start_date   DATE         NOT NULL,
  end_date     DATE         NOT NULL,
  discount_pct INT          NOT NULL,
  reason       VARCHAR(80),
  FOREIGN KEY (sku_id)   REFERENCES dim_sku(sku_id),
  FOREIGN KEY (store_id) REFERENCES dim_store(store_id)
);

-- ============================================================
-- ФАКТИ (fact)
-- ============================================================
CREATE TABLE sales_fact (
  sales_id   BIGINT        PRIMARY KEY,
  sales_date DATE          NOT NULL,
  sku_id     INT           NOT NULL,
  store_id   INT           NOT NULL,
  qty        INT           NOT NULL,
  price      DECIMAL(10,2) NOT NULL,
  promo      BOOLEAN       DEFAULT FALSE,
  amount     DECIMAL(12,2) NOT NULL,
  FOREIGN KEY (sku_id)   REFERENCES dim_sku(sku_id),
  FOREIGN KEY (store_id) REFERENCES dim_store(store_id)
);

CREATE TABLE inventory_snapshot (
  inventory_id     BIGINT    PRIMARY KEY,
  snapshot_date    DATE      NOT NULL,
  sku_id           INT       NOT NULL,
  store_id         INT       NOT NULL,
  qty_on_hand      INT       NOT NULL,
  qty_in_transit   INT       DEFAULT 0,
  last_updated_ts  TIMESTAMP NOT NULL,
  FOREIGN KEY (sku_id)   REFERENCES dim_sku(sku_id),
  FOREIGN KEY (store_id) REFERENCES dim_store(store_id)
);
```

## 2. Заповнення даними (INSERT) — приклади

```sql
INSERT INTO dim_category (category_id, category_name, m_path) VALUES
  (80001, 'Ноутбуки',     '80000:80001'),
  (80002, 'Смартфони',    '80000:80002'),
  (80003, 'Холодильники', '80000:80003');

INSERT INTO dim_store (store_id, store_name, city, region) VALUES
  (215, 'Marketplace FC Kyiv-Brovary', 'Київ', 'Київська область'),
  (312, 'Marketplace FC Lviv-West',    'Львів', 'Львівська область');
```

> Повні дані — у [`../data/db/db_sample_data.xlsx`](../data/db/db_sample_data.xlsx) (по 100 рядків
> у fact-таблицях, реалістичні розміри у довідниках).

## 3. Формування Датасету (JOIN всіх таблиць)

```sql
CREATE OR REPLACE VIEW dataset AS
SELECT
    sf.sales_date,
    DATE_TRUNC('week', sf.sales_date)           AS week_start_date,
    sf.sku_id,
    sf.store_id,
    -- з dim_sku + dim_category
    ds.category_id,
    dc.category_name,
    ds.brand,
    ds.weight_kg,
    -- з dim_store
    st.city,
    st.region,
    -- з sales_fact
    sf.qty,
    sf.price,
    sf.amount,
    sf.promo,
    -- з dim_holidays (LEFT JOIN — якщо є дата свята)
    (dh.holiday_date IS NOT NULL)               AS is_holiday,
    COALESCE(dh.is_promo_period, FALSE)         AS is_promo_period
FROM sales_fact      AS sf
INNER JOIN dim_sku       AS ds ON sf.sku_id    = ds.sku_id
INNER JOIN dim_category  AS dc ON ds.category_id = dc.category_id
INNER JOIN dim_store     AS st ON sf.store_id   = st.store_id
LEFT  JOIN dim_holidays  AS dh ON sf.sales_date = dh.holiday_date
WHERE ds.is_active = TRUE
ORDER BY sf.sales_date, sf.store_id, sf.sku_id;
```

## 4. Розширений датасет — інтеграція з inventory

Для розрахунку формули замовлення `Q = Fct − St − GiT + SS_Fct` додаємо залишки:

```sql
WITH latest_inventory AS (
    SELECT sku_id, store_id,
           MAX(snapshot_date) AS snapshot_date
    FROM inventory_snapshot
    GROUP BY sku_id, store_id
)
SELECT
    d.*,
    i.qty_on_hand     AS current_stock,    -- St
    i.qty_in_transit  AS goods_in_transit  -- GiT
FROM dataset d
LEFT JOIN latest_inventory li
       ON d.sku_id = li.sku_id AND d.store_id = li.store_id
LEFT JOIN inventory_snapshot i
       ON i.sku_id = li.sku_id
      AND i.store_id = li.store_id
      AND i.snapshot_date = li.snapshot_date;
```

## 5. Логіка JOIN

| Join | Коли використовується | Приклад |
|---|---|---|
| **INNER JOIN** | Беремо лише ті продажі, де є SKU та магазин у довідниках | `sales_fact ⨝ dim_sku ⨝ dim_store` |
| **LEFT JOIN**  | Свято — опціональне поле (більшість днів — без свята) | `sales_fact LEFT JOIN dim_holidays` |
| **LEFT JOIN**  | Залишки — можуть бути відсутні для нових SKU | `dataset LEFT JOIN inventory_snapshot` |

Промо-таблиця (`dim_promo_calendar`) у поточній версії датасету не приєднується,
оскільки прапор акції вже денормалізовано у `sales_fact.promo`. У майбутніх версіях
датасету можна додати JOIN для деталізації знижки.
