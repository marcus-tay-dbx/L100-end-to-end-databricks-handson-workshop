# Databricks notebook source
# MAGIC %md
# MAGIC # 🧹 99 · Reset — Delete *Your* Workshop Environment
# MAGIC
# MAGIC Run this when you want a **clean slate** — before re-running setup, or to clean up after the
# MAGIC workshop. It deletes **only your own catalog**, which cascades to everything inside it:
# MAGIC
# MAGIC | Gets deleted | Because it lives inside your catalog |
# MAGIC |---|---|
# MAGIC | Your **catalog** `your_name_bank` | ← the one thing we drop |
# MAGIC | Schema `retail_360` | inside the catalog |
# MAGIC | Volume `raw_files` + all copied CSVs/PDFs | inside the schema |
# MAGIC | Tables (customers, accounts, transactions, products, branches) | inside the schema |
# MAGIC | Functions `mask_pii`, `filter_by_region` | inside the schema |
# MAGIC | Any policies you created in Module 1 | attached to your tables |
# MAGIC
# MAGIC > 🛈 This does **not** touch shared, account-level things (the `data_builders` group, the 5
# MAGIC > regional groups, the `pii` tag). Those are managed by the facilitator and reused across cohorts.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 1 — Tell us which environment to delete
# MAGIC Type the **same `your_name`** you used in setup. To avoid accidents, you must also flip the
# MAGIC **`confirm`** widget to `yes` — nothing is deleted until you do.

# COMMAND ----------

dbutils.widgets.text("your_name", "", "1. Your name (same as setup, e.g. ali)")
dbutils.widgets.text("catalog_suffix", "bank", "2. Catalog suffix")
dbutils.widgets.dropdown("confirm", "no", ["no", "yes"], "3. Really delete? (yes to proceed)")

# COMMAND ----------

import re

your_name = dbutils.widgets.get("your_name").strip().lower()
catalog_suffix = dbutils.widgets.get("catalog_suffix").strip().lower()
confirm = dbutils.widgets.get("confirm") == "yes"

if not your_name:
    raise ValueError(
        "👆 Type your name in the 'your_name' widget (same as setup), then re-run. Example: ali"
    )
if not re.fullmatch(r"[a-z][a-z0-9_]{1,20}", your_name):
    raise ValueError(
        f"'{your_name}' is not a valid name. Use only lowercase letters, numbers and underscores."
    )

CATALOG = f"{your_name}_{catalog_suffix}"

print(f"🎯 Target catalog to delete: {CATALOG}")
if not confirm:
    print("\n🛑 SAFETY STOP — nothing deleted yet.")
    print("   Set the 'confirm' widget to 'yes' and re-run this cell to proceed.")
else:
    print("\n⚠️  confirm=yes → the next cell WILL drop this catalog and everything in it.")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 2 — Delete it
# MAGIC Runs only when `confirm=yes`. Uses `DROP CATALOG ... CASCADE`, so a single statement removes the
# MAGIC schema, volume, tables, functions and policies together.

# COMMAND ----------

if not confirm:
    print("🛑 Skipped — 'confirm' is still 'no'. Set it to 'yes' above to actually delete.")
else:
    # Does it even exist? Nicer message than a raw error.
    exists = spark.sql(
        f"SELECT count(*) AS n FROM system.information_schema.catalogs "
        f"WHERE catalog_name = '{CATALOG}'"
    ).collect()[0]["n"]

    if exists == 0:
        print(f"↩️  Catalog {CATALOG} doesn't exist — nothing to delete. You're already clean. ✅")
    else:
        spark.sql(f"DROP CATALOG IF EXISTS {CATALOG} CASCADE")
        print(f"🧹 Dropped catalog {CATALOG} (schema, volume, tables, functions, policies all gone).")
        print("✅ Clean slate. Re-run 00-setup.py whenever you're ready to build again.")

# COMMAND ----------

# MAGIC %md
# MAGIC ### 💡 Notes
# MAGIC - **Re-running is safe.** If the catalog is already gone, this just tells you so.
# MAGIC - **Fresh start instead of full delete?** You don't strictly need this notebook — `00-setup.py`
# MAGIC   has a `reset` widget that drops-and-rebuilds in one go.
# MAGIC - **Permission error on DROP?** You can only drop a catalog you **own**. If you didn't create it,
# MAGIC   ask the facilitator.
