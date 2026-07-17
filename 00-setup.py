# Databricks notebook source
# MAGIC %md
# MAGIC # 🚀 00 · Workshop Setup — Build *Your* Personal Environment
# MAGIC
# MAGIC **Welcome!** Today you are a Data Engineer, Data Scientist, BI Analyst *and* ML Engineer — all at once. Don't worry, it's not as scary as it sounds. 😊
# MAGIC
# MAGIC > 🛈 **Before you start:** your facilitator has already run the one-time `00-setup-ADMIN` notebook, which added you to the `data_builders` group (so you can create your own catalog) and set up the shared groups and tags. If **Step 3 fails with a permission error**, tell your facilitator — you may not be in `data_builders` yet.
# MAGIC
# MAGIC This one notebook creates your **own private sandbox** so you never step on anyone else's work:
# MAGIC
# MAGIC | What gets created | Example (if your name is `ali`) |
# MAGIC |---|---|
# MAGIC | A **catalog** | `ali_bank` |
# MAGIC | A **schema** inside it | `ali_bank.retail_360` |
# MAGIC | A **volume** for files | `ali_bank.retail_360.raw_files` |
# MAGIC | **4 Delta tables** | accounts, transactions, products, branches |
# MAGIC | **1 CSV in the volume** | `customers.csv` — you'll upload this yourself in Module 1! |
# MAGIC | **Product PDF documents** | for the Module 7 AI assistant |
# MAGIC
# MAGIC ### 👉 What you need to do
# MAGIC 1. In the widgets at the **top of this notebook**, type **`your_name`** (lowercase, no spaces — e.g. `ali`).
# MAGIC 2. Click **Run all** (or press the ▶▶ button).
# MAGIC 3. Wait for the green ✅ summary at the bottom. That's it!

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 1 — Tell us your name (creates your widgets)
# MAGIC Run the cell below **once**. Two boxes appear at the top of the notebook. Fill in `your_name`, then continue.

# COMMAND ----------

dbutils.widgets.text("your_name", "", "1. Your name (lowercase, e.g. ali)")
dbutils.widgets.text("catalog_suffix", "bank", "2. Catalog suffix")
dbutils.widgets.dropdown("reset", "no", ["no", "yes"], "3. Reset my catalog first?")

# COMMAND ----------

your_name = dbutils.widgets.get("your_name").strip().lower()
catalog_suffix = dbutils.widgets.get("catalog_suffix").strip().lower()
reset = dbutils.widgets.get("reset") == "yes"

# --- basic validation so nobody gets a cryptic SQL error later ---
import re

if not your_name:
    raise ValueError(
        "👆 Please type your name in the 'your_name' widget at the top, "
        "then re-run this cell. Example: ali"
    )
if not re.fullmatch(r"[a-z][a-z0-9_]{1,20}", your_name):
    raise ValueError(
        f"'{your_name}' is not a valid name. Use only lowercase letters, "
        "numbers and underscores, starting with a letter (e.g. ali, siti_a)."
    )

CATALOG = f"{your_name}_{catalog_suffix}"
SCHEMA = "retail_360"
VOLUME = "raw_files"

print(f"👤 Name           : {your_name}")
print(f"📦 Your catalog   : {CATALOG}")
print(f"🗂️  Your schema    : {CATALOG}.{SCHEMA}")
print(f"📁 Your volume    : {CATALOG}.{SCHEMA}.{VOLUME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 2 — Load the workshop branding profile
# MAGIC This reads `config/workshop_config.py`. The facilitator has set the active bank for today.

# COMMAND ----------

import os
import sys

# Locate the repo root (this notebook lives at the repo root when cloned via Repos/Git folders)
def find_repo_root():
    # Databricks Repos path is available via the notebook context
    try:
        nb_path = (
            dbutils.notebook.entry_point.getDbutils().notebook().getContext()
            .notebookPath().get()
        )
    except Exception:
        nb_path = None
    # Candidate filesystem roots to search for config/
    candidates = []
    if nb_path:
        candidates.append("/Workspace" + os.path.dirname(nb_path))
    candidates += [os.getcwd(), os.path.dirname(os.getcwd())]
    for c in candidates:
        if c and os.path.exists(os.path.join(c, "config", "workshop_config.py")):
            return c
    return candidates[0] if candidates else os.getcwd()

REPO_ROOT = find_repo_root()
CONFIG_DIR = os.path.join(REPO_ROOT, "config")
sys.path.insert(0, CONFIG_DIR)

from workshop_config import get_profile  # noqa: E402

PROFILE = get_profile()
BANK_NAME = PROFILE["bank_name"]
PDS_FOLDER = PROFILE["pds_folder"]

print(f"🏦 Workshop branding : {BANK_NAME}  ({PROFILE['tagline']})")
print(f"📄 Product documents : data/pds_documents/{PDS_FOLDER}/")
print(f"📂 Repo root         : {REPO_ROOT}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 3 — Create your catalog, schema and volume
# MAGIC Unity Catalog governs everything. Creating storage is just three SQL statements — no infra tickets.

# COMMAND ----------

if reset:
    print(f"♻️  reset=yes → dropping catalog {CATALOG} (if it exists) ...")
    spark.sql(f"DROP CATALOG IF EXISTS {CATALOG} CASCADE")

spark.sql(f"CREATE CATALOG IF NOT EXISTS {CATALOG}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {CATALOG}.{SCHEMA}.{VOLUME}")

spark.sql(f"USE CATALOG {CATALOG}")
spark.sql(f"USE SCHEMA {SCHEMA}")

print(f"✅ Catalog  {CATALOG}")
print(f"✅ Schema   {CATALOG}.{SCHEMA}")
print(f"✅ Volume   {CATALOG}.{SCHEMA}.{VOLUME}")

VOLUME_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}"

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 4 — Copy the raw files into your volume
# MAGIC We copy the CSVs and the product PDFs from the cloned repo into *your* volume, so everything you need lives in your own governed storage.

# COMMAND ----------

import shutil

DATA_DIR = os.path.join(REPO_ROOT, "data")
PDS_SRC = os.path.join(DATA_DIR, "pds_documents", PDS_FOLDER)

# 4a. Copy CSVs into the volume
csv_files = ["customers.csv", "accounts.csv", "transactions.csv", "products.csv", "branches.csv"]
for f in csv_files:
    src = os.path.join(DATA_DIR, f)
    dst = os.path.join(VOLUME_PATH, f)
    shutil.copyfile(src, dst)
print(f"📄 Copied {len(csv_files)} CSV files into {VOLUME_PATH}")

# 4b. Copy product PDFs into a docs/ subfolder in the volume (for Module 7 RAG)
docs_dst = os.path.join(VOLUME_PATH, "product_docs")
os.makedirs(docs_dst, exist_ok=True)
pdf_count = 0
for f in sorted(os.listdir(PDS_SRC)):
    if f.lower().endswith(".pdf"):
        shutil.copyfile(os.path.join(PDS_SRC, f), os.path.join(docs_dst, f))
        pdf_count += 1
print(f"📁 Copied {pdf_count} {BANK_NAME} product PDF documents into {docs_dst}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 5 — Load 4 tables as Delta
# MAGIC We load **accounts, transactions, products, branches** for you.
# MAGIC
# MAGIC > 🙌 We deliberately **do _not_ load `customers`** — that's *your* hands-on moment in **Module 1**, where you'll upload `customers.csv` yourself. It's already waiting in your volume.

# COMMAND ----------

def load_csv_to_table(csv_name, table_name):
    path = f"{VOLUME_PATH}/{csv_name}"
    df = (
        spark.read.option("header", True)
        .option("inferSchema", True)
        .csv(path)
    )
    (df.write.mode("overwrite").option("overwriteSchema", "true")
        .saveAsTable(f"{CATALOG}.{SCHEMA}.{table_name}"))
    return df.count()

tables = {
    "accounts": "accounts.csv",
    "transactions": "transactions.csv",
    "products": "products.csv",
    "branches": "branches.csv",
}
for tbl, csv_name in tables.items():
    n = load_csv_to_table(csv_name, tbl)
    print(f"✅ {CATALOG}.{SCHEMA}.{tbl:14s} — {n:>6,} rows")

print("\n⏭️  customers.csv is in your volume, ready for you to upload in Module 1.")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 6 — Add a helpful table comment (nice touch for Genie later)

# COMMAND ----------

spark.sql(f"""
  COMMENT ON TABLE {CATALOG}.{SCHEMA}.transactions IS
  'Customer card & account transactions: amount_myr, channel, category, merchant. One row per transaction.'
""")
spark.sql(f"""
  COMMENT ON TABLE {CATALOG}.{SCHEMA}.products IS
  'Product catalog: product_name, product_type (Deposit/Financing/Card/Wealth/Protection), profit_rate_pct.'
""")
print("✅ Added table descriptions (Genie and Catalog Explorer will show these).")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 7 — Create the PII masking function (used in Module 1)
# MAGIC This is the **pre-built function** you'll reference in Module 1 when you create your own
# MAGIC ABAC policy. It masks any string value, so a policy can hide columns tagged as PII from
# MAGIC other users. We create it for you — you'll write the *policy* that uses it.

# COMMAND ----------

spark.sql(f"""
  CREATE OR REPLACE FUNCTION {CATALOG}.{SCHEMA}.mask_pii(input_value STRING)
  RETURNS STRING
  COMMENT 'Masks a value for users who should not see PII. Used by ABAC column-mask policies.'
  RETURN '***REDACTED***'
""")
print(f"✅ Created masking function {CATALOG}.{SCHEMA}.mask_pii(STRING)")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 8 — Create the Row-Level Security function (used in Module 1)
# MAGIC This **pre-built function** returns TRUE only when the querying user is an admin, **or** is a
# MAGIC member of the group matching a row's `region`. In Module 1 you'll attach it to your `branches`
# MAGIC table as a **row filter**, so each region team sees only their own branches.
# MAGIC
# MAGIC The mapping is automatic: `Central → team_central`, `East Coast → team_east_coast`, etc.

# COMMAND ----------

spark.sql(f"""
  CREATE OR REPLACE FUNCTION {CATALOG}.{SCHEMA}.filter_by_region(region STRING)
  RETURNS BOOLEAN
  COMMENT 'Row filter: user sees a branch row only if admin, or member of the row''s region group.'
  RETURN is_member('admins')
      OR is_member(concat('team_', lower(replace(region, ' ', '_'))))
""")
print(f"✅ Created row-filter function {CATALOG}.{SCHEMA}.filter_by_region(STRING)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 🎉 You're all set!

# COMMAND ----------

summary = f"""
╔══════════════════════════════════════════════════════════════╗
   ✅ SETUP COMPLETE — {BANK_NAME} Workshop
╠══════════════════════════════════════════════════════════════╣
   Your catalog : {CATALOG}
   Your schema  : {CATALOG}.{SCHEMA}
   Your volume  : {VOLUME_PATH}

   Tables loaded for you:
     • accounts, transactions, products, branches

   Waiting for YOU in Module 1:
     • customers.csv  (in your volume — upload it as a table)

   Product docs for Module 7 (RAG):
     • {VOLUME_PATH}/product_docs/  ({pdf_count} PDFs)

   Pre-built for you (Module 1 governance):
     • {SCHEMA}.mask_pii()          (column mask function)
     • {SCHEMA}.filter_by_region()  (row-level security function)

   Shared, set up by facilitator (used in Module 1):
     • governed tags `pii` + `region_filter` (values: true / false)
     • 5 regional groups: team_central / _east_coast /
       _east_malaysia / _northern / _southern
╠══════════════════════════════════════════════════════════════╣
   ▶️  NEXT: open lab-guide/LAB-GUIDE.ipynb and start Module 1.
╚══════════════════════════════════════════════════════════════╝
"""
print(summary)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 💡 Stuck?
# MAGIC - **"your_name is not valid"** → use only lowercase letters/numbers (e.g. `ali`, `siti2`). Re-run Step 1.
# MAGIC - **"catalog already exists" / want a clean start** → set the **`reset`** widget to `yes` and Run all again.
# MAGIC - **"config not found" / import error** → make sure you opened this from the **cloned Git folder** (Repos), not a single uploaded file.
# MAGIC - **Permission denied creating a catalog** → tell the facilitator; your trial user may need the *Create Catalog* privilege.
