# Databricks notebook source
# MAGIC %md
# MAGIC # 🧱 Build `customer_360_features` — for the Module 4 AutoML demo
# MAGIC
# MAGIC **Facilitator notebook** (not part of the participant hands-on).
# MAGIC
# MAGIC Builds a one-row-per-customer feature table with a **`next_best_offer`** label,
# MAGIC so you can point AutoML (Classification) at it and demo "Next Best Offer".
# MAGIC
# MAGIC Run this in *your* environment after `00-setup` has created the base tables.
# MAGIC Set the `catalog` widget to your catalog (e.g. `marcus_bank`).

# COMMAND ----------

dbutils.widgets.text("catalog", "", "Your catalog (e.g. marcus_bank)")
CATALOG = dbutils.widgets.get("catalog").strip().lower()
assert CATALOG, "Set the 'catalog' widget to your catalog name first."
SCHEMA = "retail_360"
spark.sql(f"USE CATALOG {CATALOG}")
spark.sql(f"USE SCHEMA {SCHEMA}")
print("Building features in", CATALOG, SCHEMA)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Feature engineering
# MAGIC Aggregate transactions + accounts up to the customer grain, then derive a
# MAGIC `next_best_offer` label from simple, explainable rules so AutoML finds real signal.

# COMMAND ----------

features_sql = f"""
CREATE OR REPLACE TABLE {CATALOG}.{SCHEMA}.customer_360_features AS
WITH txn AS (
  SELECT customer_id,
         COUNT(*)                                   AS txn_count_90d,
         ROUND(AVG(amount_myr), 2)                  AS avg_txn_amount,
         ROUND(SUM(amount_myr), 2)                  AS total_spend,
         COUNT(DISTINCT category)                   AS category_variety,
         SUM(CASE WHEN channel IN ('Mobile App','Internet Banking','QR Pay')
                  THEN 1 ELSE 0 END)                AS digital_txns
  FROM {CATALOG}.{SCHEMA}.transactions
  GROUP BY customer_id
),
acct AS (
  SELECT customer_id,
         COUNT(*)                                            AS num_products_held,
         ROUND(SUM(CASE WHEN balance_myr > 0 THEN balance_myr ELSE 0 END), 2) AS total_balance,
         MAX(CASE WHEN product_id = 'P05' THEN 1 ELSE 0 END) AS has_home,
         MAX(CASE WHEN product_id = 'P06' THEN 1 ELSE 0 END) AS has_vehicle,
         MAX(CASE WHEN product_id = 'P04' THEN 1 ELSE 0 END) AS has_personal,
         MAX(CASE WHEN product_id = 'P02' THEN 1 ELSE 0 END) AS has_term_deposit,
         MAX(CASE WHEN product_id = 'P10' THEN 1 ELSE 0 END) AS has_card,
         MAX(CASE WHEN product_id = 'P11' THEN 1 ELSE 0 END) AS has_investment
  FROM {CATALOG}.{SCHEMA}.accounts
  GROUP BY customer_id
),
base AS (
  SELECT c.customer_id,
         c.age,
         c.gender,
         c.state,
         c.region,
         c.segment,
         c.income_band,
         CAST(months_between(current_date(), to_date(c.join_date)) AS INT) AS tenure_months,
         COALESCE(a.num_products_held, 0)   AS num_products_held,
         COALESCE(a.total_balance, 0)       AS total_balance,
         COALESCE(a.has_home, 0)            AS has_home,
         COALESCE(a.has_vehicle, 0)         AS has_vehicle,
         COALESCE(a.has_personal, 0)        AS has_personal,
         COALESCE(a.has_term_deposit, 0)    AS has_term_deposit,
         COALESCE(a.has_card, 0)            AS has_card,
         COALESCE(a.has_investment, 0)      AS has_investment,
         COALESCE(t.txn_count_90d, 0)       AS txn_count_90d,
         COALESCE(t.avg_txn_amount, 0)      AS avg_txn_amount,
         COALESCE(t.total_spend, 0)         AS total_spend,
         COALESCE(t.category_variety, 0)    AS category_variety,
         ROUND(COALESCE(t.digital_txns, 0) / NULLIF(t.txn_count_90d, 0), 2) AS digital_engagement_score
  FROM {CATALOG}.{SCHEMA}.customers c
  LEFT JOIN acct a ON c.customer_id = a.customer_id
  LEFT JOIN txn  t ON c.customer_id = t.customer_id
),
income_rank AS (
  SELECT *,
    CASE income_band
      WHEN '<3K' THEN 0 WHEN '3K-5K' THEN 1 WHEN '5K-8K' THEN 2
      WHEN '8K-12K' THEN 3 WHEN '12K-20K' THEN 4 WHEN '>20K' THEN 5 ELSE 0 END AS income_rank
  FROM base
)
SELECT *,
  /* Next Best Offer label — explainable rules, priority order top-to-bottom.
     Signal is intentionally learnable by AutoML while staying realistic. */
  CASE
    WHEN has_home = 0 AND age BETWEEN 30 AND 50 AND income_rank >= 3
         THEN 'Home Financing-i'
    WHEN has_investment = 0 AND income_rank >= 4 AND total_balance > 50000
         THEN 'Investment-i Fund'
    WHEN has_term_deposit = 0 AND age >= 50 AND total_balance > 30000
         THEN 'Term Deposit-i'
    WHEN has_vehicle = 0 AND age BETWEEN 25 AND 45 AND income_rank BETWEEN 2 AND 4
         THEN 'Vehicle Financing-i'
    WHEN has_personal = 0 AND age BETWEEN 21 AND 40 AND income_rank <= 2
         THEN 'Personal Financing-i'
    WHEN has_card = 0 AND income_rank >= 2 AND digital_engagement_score >= 0.5
         THEN 'Credit Card-i'
    WHEN age BETWEEN 22 AND 35 AND category_variety >= 5
         THEN 'Education Financing-i'
    ELSE 'None'
  END AS next_best_offer
FROM income_rank
"""
spark.sql(features_sql)
print("✅ Created", f"{CATALOG}.{SCHEMA}.customer_360_features")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Sanity check — label distribution should be varied (good for AutoML)

# COMMAND ----------

display(spark.sql(f"""
  SELECT next_best_offer, COUNT(*) AS customers
  FROM {CATALOG}.{SCHEMA}.customer_360_features
  GROUP BY next_best_offer
  ORDER BY customers DESC
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC Now go to **Experiments → Create AutoML Experiment → Classification**,
# MAGIC dataset = `customer_360_features`, target = `next_best_offer`. 🎯
