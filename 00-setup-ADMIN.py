# Databricks notebook source
# MAGIC %md
# MAGIC # 🛠️ 00 · ADMIN Setup — Run ONCE for the whole workshop
# MAGIC
# MAGIC **Facilitator only.** This notebook prepares the *shared, account-level* resources that every
# MAGIC participant depends on. Participants do **not** run this — they run `00-setup.py`.
# MAGIC
# MAGIC > 👥 **Everyone in this workshop is an account/workspace admin.** That means the usual
# MAGIC > "let participants create catalogs and assign tags" grants are unnecessary — admins already
# MAGIC > have those privileges. So this notebook only creates the two things admin status does **not**
# MAGIC > give you automatically: the **region groups** and the **governed tags**.
# MAGIC
# MAGIC | What this creates | Scope | Why |
# MAGIC |---|---|---|
# MAGIC | **5 regional groups** | Account | Row-level-security demo in Module 1 (one team per region). Every participant joins exactly one. |
# MAGIC | Governed tags **`pii`** and **`region_filter`** (values `true` / `false`) | Account | Module 1's ABAC policies match on these tags. **ABAC only works on _governed_ tags** — a plain tag fails with `Unknown tag policy key`. Admin status does **not** create these for you. |
# MAGIC
# MAGIC ### 👉 What you need to do
# MAGIC 1. Make sure you are an **account admin** (or workspace admin with account privileges).
# MAGIC 2. Click **Run all**.
# MAGIC 3. Do the **⚠️ MANUAL STEP** printed at the bottom (group membership — the only thing SQL can't do).

# COMMAND ----------

# MAGIC %md
# MAGIC ### Step 1 — Create the 5 regional groups (for Module 1 row-level security)
# MAGIC These back the row filter on the `branches.region` column: a user in `team_central` sees only
# MAGIC Central branches, etc. Groups are **account-level** resources with no `CREATE GROUP` SQL, so we use
# MAGIC the SDK. Idempotent — re-running never fails if a group already exists.

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
# MAGIC ### Step 2 — Create the governed tags for Module 1 (`pii`, `region_filter`)
# MAGIC Module 1's ABAC policies match columns with `has_tag_value('pii', 'true')` and
# MAGIC `has_tag_value('region_filter', 'true')`. **ABAC only recognizes _governed_ tags** — a plain tag
# MAGIC fails at policy-compile time with `Unknown tag policy key`. So we create both as governed tags
# MAGIC with a fixed `true` / `false` value set. (Admins can already *assign* governed tags, so no extra
# MAGIC grant is needed once the tags exist.)
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
# MAGIC ## ⚠️ MANUAL STEP — do this in the Account Console before participants start
# MAGIC Group **membership** is the one thing SQL can't set. Do it now in the UI:

# COMMAND ----------

manual = """
╔══════════════════════════════════════════════════════════════════════╗
   ⚠️  MANUAL STEP (group membership — the only thing SQL can't set)
╠══════════════════════════════════════════════════════════════════════╣

  ASSIGN EVERY PARTICIPANT TO EXACTLY ONE REGION GROUP
     Account Console → User management → Groups → team_central /
     team_east_coast / team_east_malaysia / team_northern / team_southern
     Put EACH participant into ONE region group. In Module 1's row-level
     security demo, they'll then see ONLY that region's branches — live,
     on their own screen (there is no admin bypass in filter_by_region).

  ⚠️  A participant in NO region group will see an EMPTY branches table
      after applying the row-filter policy. Make sure everyone is in one.

╠══════════════════════════════════════════════════════════════════════╣
   After this step, participants can open 00-setup.py and Run all.
╚══════════════════════════════════════════════════════════════════════╝
"""
print(manual)

# COMMAND ----------

# MAGIC %md
# MAGIC ### 💡 Notes for the facilitator
# MAGIC - **Everyone is an admin**, so participants can create their own catalog and assign the governed
# MAGIC   tags with no extra grants. This notebook only sets up the region groups and governed tags.
# MAGIC - **Re-running is safe.** The groups and the governed tags are all idempotent here.
# MAGIC - **Why governed tags?** ABAC policies (`has_tag_value(...)`) only recognize **governed** tags. A
# MAGIC   plain tag makes Module 1 fail with `Unknown tag policy key 'pii'`. Both `pii` and
# MAGIC   `region_filter` must be governed tags — creating them is enough (admins can already assign them).
# MAGIC - **No admin bypass in RLS.** `filter_by_region` (created in `00-setup.py`) matches only on region
# MAGIC   group membership, so the filter applies to everyone — that's what makes the demo visible. Every
# MAGIC   participant must be in exactly one `team_<region>` group.
# MAGIC - **Governed tags need DBR 18.1+.** Free-trial serverless SQL is fine. If Step 2 fails with a
# MAGIC   syntax error, your warehouse is on an older runtime.
# MAGIC - **Removing everything after the workshop:** drop participant catalogs individually; the
# MAGIC   account groups and governed tags can be reused for the next cohort.
