# Databricks notebook source
# MAGIC %md
# MAGIC # 🛠️ 00 · ADMIN Setup — Run ONCE for the whole workshop
# MAGIC
# MAGIC **Facilitator only.** This notebook prepares the *shared, account-level* resources that every
# MAGIC participant depends on. Participants do **not** run this — they run `00-setup.py`.
# MAGIC
# MAGIC | What this creates | Scope | Why |
# MAGIC |---|---|---|
# MAGIC | Group **`data_builders`** | Account | Participants join this; it grants them the right to create their own catalog. |
# MAGIC | `GRANT CREATE CATALOG ON METASTORE` → `data_builders` | Metastore | So each participant's `00-setup.py` can build their own catalog. |
# MAGIC | **5 regional groups** | Account | Row-level-security demo in Module 1 (one team per region). |
# MAGIC
# MAGIC ### 👉 What you need to do
# MAGIC 1. Make sure you are an **account admin** (or workspace admin with account privileges).
# MAGIC 2. Click **Run all**.
# MAGIC 3. Read the **⚠️ MANUAL STEPS** printed at the bottom — a few grants can only be done in the
# MAGIC    Account Console UI, not in SQL. Do those before participants start.

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 1 — Create the `data_builders` group (participants join this)
# MAGIC Groups are **account-level** resources with no `CREATE GROUP` SQL, so we use the SDK. This is
# MAGIC idempotent — re-running never fails if the group already exists.

# COMMAND ----------

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()


def ensure_group(display_name):
    """Create an account group if it doesn't already exist. Returns 'created' or 'existing'."""
    found = list(w.groups.list(filter=f'displayName eq "{display_name}"'))
    if found:
        return "existing"
    w.groups.create(display_name=display_name)
    return "created"


status = ensure_group("data_builders")
print(f"{'✅ Created' if status == 'created' else '↩️  Already existed'} group: data_builders")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 2 — Let `data_builders` create their own catalogs
# MAGIC This is the privilege that makes the participant setup work: each person's `00-setup.py` runs
# MAGIC `CREATE CATALOG <name>_bank`. Without this grant, only admins could do that.

# COMMAND ----------

spark.sql("GRANT CREATE CATALOG ON METASTORE TO `data_builders`")
print("✅ Granted CREATE CATALOG ON METASTORE to `data_builders`")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 3 — Create the 5 regional groups (for Module 1 row-level security)
# MAGIC These back the row filter on the `branches.region` column: a user in `team_central` sees only
# MAGIC Central branches, etc. Created once, shared by everyone. Idempotent.

# COMMAND ----------

REGION_GROUPS = [
    "team_central",
    "team_east_coast",
    "team_east_malaysia",
    "team_northern",
    "team_southern",
]

created, existing = [], []
for g in REGION_GROUPS:
    if ensure_group(g) == "created":
        created.append(g)
    else:
        existing.append(g)

if created:
    print(f"✅ Created groups: {', '.join(created)}")
if existing:
    print(f"↩️  Already existed (skipped): {', '.join(existing)}")

# COMMAND ----------

# MAGIC %md
# MAGIC ### ℹ️ About the `pii` tag (nothing to create here)
# MAGIC Module 1 uses a **plain tag**, not a governed one. Plain tags need no setup: the moment a
# MAGIC participant runs `ALTER TABLE ... SET TAGS ('pii' = 'true')` on their own table, the tag exists.
# MAGIC As **owner of their own catalog**, each participant already has `APPLY TAG`, so no grant is
# MAGIC needed. This keeps Module 1 friction-free.

# COMMAND ----------

# MAGIC %md
# MAGIC ## ⚠️ MANUAL STEPS — do these in the Account Console before participants start
# MAGIC A few things **cannot** be done in SQL. Do them now in the UI:

# COMMAND ----------

manual = """
╔══════════════════════════════════════════════════════════════════════╗
   ⚠️  MANUAL STEPS (Account Console UI — no SQL equivalent)
╠══════════════════════════════════════════════════════════════════════╣

  1. ADD PARTICIPANTS TO  data_builders
     Account Console → User management → Groups → data_builders → Members
     Add every workshop participant. This is what lets their 00-setup.py
     create their own catalog.

  2. (For the Module 1 RLS demo) ASSIGN REGION-GROUP MEMBERSHIP
     Account Console → Groups → team_central / team_east_coast /
     team_east_malaysia / team_northern / team_southern
     Put yourself (and any demo user) in ONE region group so you can
     show "this user only sees their region's branches".

╠══════════════════════════════════════════════════════════════════════╣
   After steps 1–2, participants can open 00-setup.py and Run all.
╚══════════════════════════════════════════════════════════════════════╝
"""
print(manual)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 💡 Notes for the facilitator
# MAGIC - **Re-running is safe.** The group creation and the metastore grant are both idempotent here.
# MAGIC - **No tag setup needed.** Module 1 uses a plain `pii` tag that participants create on their own
# MAGIC   tables — nothing to pre-create or grant.
# MAGIC - **Removing everything after the workshop:** drop participant catalogs individually; the
# MAGIC   account groups can be reused for the next cohort.
