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
# MAGIC | Governed tags **`pii`** and **`region_filter`** (values `true` / `false`) | Account | Module 1's ABAC policies match on these tags. **ABAC only works on _governed_ tags** — a plain tag fails with `Unknown tag policy key`. |
# MAGIC | `GRANT ASSIGN ON GOVERNED TAG` → `data_builders` | Account | So participants can apply those governed tags to their own columns. |
# MAGIC
# MAGIC ### 👉 What you need to do
# MAGIC 1. Make sure you are an **account admin** (or workspace admin with account privileges).
# MAGIC 2. Click **Run all**.
# MAGIC 3. Do the **⚠️ MANUAL STEPS** printed at the bottom (group membership — the only thing SQL can't do).

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
# MAGIC ### Step 4 — Create the governed tags for Module 1 (`pii`, `region_filter`)
# MAGIC Module 1's ABAC policies match columns with `has_tag_value('pii', 'true')` and
# MAGIC `has_tag_value('region_filter', 'true')`. **ABAC only recognizes _governed_ tags** — a plain tag
# MAGIC fails at policy-compile time with `Unknown tag policy key`. So we create both as governed tags
# MAGIC with a fixed `true` / `false` value set.
# MAGIC
# MAGIC > 🛈 `CREATE GOVERNED TAG` has no `IF NOT EXISTS`; it errors `ALREADY_EXISTS` on re-run. We catch
# MAGIC > that so this notebook stays safe to re-run. Requires **DBR 18.1+ / serverless SQL** and account
# MAGIC > `CREATE` privilege (account/workspace admins have it by default).

# COMMAND ----------

GOVERNED_TAGS = {
    "pii": "Marks a column as personally identifiable information (Module 1 column-mask policy).",
    "region_filter": "Marks the branch region column used by the Module 1 row-filter policy.",
}

for tag_key, desc in GOVERNED_TAGS.items():
    try:
        spark.sql(f"CREATE GOVERNED TAG {tag_key} DESCRIPTION '{desc}' VALUES ('true', 'false')")
        print(f"✅ Created governed tag `{tag_key}` (values: true, false)")
    except Exception as e:
        msg = f"{type(e).__name__}: {e}"
        if "ALREADY_EXISTS" in msg or "already exists" in msg.lower():
            print(f"↩️  Governed tag `{tag_key}` already exists — skipped.")
            print(f"    (To reset its values: ALTER GOVERNED TAG {tag_key} SET VALUES ('true', 'false'))")
        else:
            print(f"⚠️  Could not create governed tag `{tag_key}`.")
            print(f"    Reason: {msg}")
            print("    Check you are an ACCOUNT admin and the SQL warehouse is DBR 18.1+ / serverless.")

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 5 — Let `data_builders` assign those governed tags
# MAGIC To run `ALTER TABLE ... SET TAGS ('pii' = 'true')`, a participant needs **`ASSIGN`** on the
# MAGIC governed tag (plus `APPLY TAG` on the object — which they get automatically as **owner of their
# MAGIC own catalog**). This grant is what makes participant tagging work in Module 1.

# COMMAND ----------

for tag_key in GOVERNED_TAGS:
    try:
        spark.sql(f"GRANT ASSIGN ON GOVERNED TAG {tag_key} TO `data_builders`")
        print(f"✅ Granted ASSIGN on governed tag `{tag_key}` to `data_builders`")
    except Exception as e:
        print(f"⚠️  Could not grant ASSIGN on `{tag_key}`: {type(e).__name__}: {e}")
        print("    The tag must exist first (Step 4) and you must be able to MANAGE it.")

# COMMAND ----------

# MAGIC %md
# MAGIC ## ⚠️ MANUAL STEP — do this in the Account Console before participants start
# MAGIC Group **membership** is the one thing SQL can't set. Do it now in the UI:

# COMMAND ----------

manual = """
╔══════════════════════════════════════════════════════════════════════╗
   ⚠️  MANUAL STEPS (group membership — the only thing SQL can't set)
╠══════════════════════════════════════════════════════════════════════╣

  1. ADD PARTICIPANTS TO  data_builders
     Account Console → User management → Groups → data_builders → Members
     Add every workshop participant. This is what lets their 00-setup.py
     create their own catalog AND assign the pii / region_filter tags.

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
# MAGIC - **Re-running is safe.** Groups, the metastore grant, the governed tags, and the ASSIGN grants
# MAGIC   are all idempotent here.
# MAGIC - **Why governed tags?** ABAC policies (`has_tag_value(...)`) only recognize **governed** tags. A
# MAGIC   plain tag makes Module 1 fail with `Unknown tag policy key 'pii'`. Both `pii` and
# MAGIC   `region_filter` must be governed and `ASSIGN`-granted to `data_builders`.
# MAGIC - **Governed tags need DBR 18.1+.** Free-trial serverless SQL is fine. If Step 4 fails with a
# MAGIC   syntax error, your warehouse is on an older runtime.
# MAGIC - **Removing everything after the workshop:** drop participant catalogs individually; the
# MAGIC   account groups and governed tags can be reused for the next cohort.
