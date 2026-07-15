# 🎤 Facilitator Notes

Everything you (the facilitator) need to run the 3-hour workshop smoothly. Participants don't read this file.

---

## ⏱️ Timing at a glance (09:30 – 12:30)

| Time | Module | Format | Your job |
|------|--------|--------|----------|
| 09:30 | Welcome | Talk | Set the "you're all data practitioners today" tone |
| 09:45 | M1 Catalog & Upload | Hands-on | Get everyone to ✅ before moving; upload is the risky step |
| 10:05 | M2 Assistant Code | Hands-on | Demo one Assistant prompt on screen, then let them play |
| 10:25 | M3 Collaboration | Hands-on | Actively pair people; this is high-delight, low-risk |
| 10:40 | M4 AutoML + NBO | **You demo** | Run on YOUR environment (see below) |
| 10:55 | ☕ Break | — | Recover time if behind |
| 11:00 | M5 Dashboard | Hands-on | Circulate; the map viz can confuse — have the bar fallback |
| 11:25 | M6 Genie Space | Hands-on | Emphasise instructions = the magic |
| 11:50 | M7 Agents | Hands-on | Part A first; make Part B a demo if short on time |
| 12:20 | Wrap-up | Round-table | Capture use cases live |

---

## 🔧 Before the day — setup checklist

1. **Provision the trial workspace** (Free **Trial**, $400/14-day — *not* Free Edition; Free Edition can't do Agent Bricks / M7).
2. **Invite all 13 participants** as workspace users (Account Console → Users, or Workspace admin → add users). They're on `@bankrakyat.com.my`; you're on a different domain, so add them individually.
3. Ensure each user can **create a catalog** (metastore privilege `CREATE CATALOG`, or pre-create per-user catalogs). Test with one non-admin account.
4. **Serverless compute** enabled (SQL warehouse + serverless notebooks).
5. **Agent Bricks / Mosaic AI** available in the workspace region.
6. Set `config/workshop_config.py` → `ACTIVE_BANK = "bank_rakyat"` (already set).
7. Do a **full dry-run** yourself end-to-end with a test name (`ACTIVE_BANK` + `00-setup` + one module of each type).
8. Share the repo clone instructions (see README) on a slide.

> ⚠️ **Credit watch:** 13 users + serverless + Genie + Agent Bricks on one $400 trial. Model serving is your demo only (good — saves credit). Ask people to **stop compute** at the end. Keep an eye on usage mid-morning.

---

## 🎬 Module 4 demo script (you drive, on YOUR environment)

You're demoing **"Next Best Offer"** — predicting which product to offer each customer next. Run this in your own workspace where AutoML + serving are set up.

**Prep:** run `notebooks/build_features.py` (in this repo) against your catalog to create `customer_360_features` with the `next_best_offer` label.

**Live flow (≈12 min):**
1. **Show the feature table** (30s): open `customer_360_features`. "One row per customer: age, income, tenure, products held, spend — and a label: the product they're most likely to take next."
2. **Start AutoML** (2 min): Experiments → **Create AutoML Experiment** → Classification → dataset = `customer_360_features` → target = `next_best_offer` → Start. While it runs, talk through what it's doing (feature prep, trying many models, cross-validation).
3. **Leaderboard** (3 min): open the experiment. "Every row is a model it trained. Best on top. Each has a fully-editable notebook — no black box."
4. **Register** (2 min): register the best model to Unity Catalog. "Now it's a governed asset, versioned, permissioned."
5. **Serve** (3 min): create/enable a **Serving endpoint** from the registered model. Hit it:

```bash
curl -X POST https://<your-workspace>/serving-endpoints/<endpoint>/invocations \
  -H "Authorization: Bearer $DATABRICKS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"dataframe_records": [{"age": 34, "income_band": "8K-12K", "tenure_months": 60, "num_products_held": 2, "total_balance": 45000, "txn_count_90d": 40, "avg_txn_amount": 220, "digital_engagement_score": 0.8}]}'
```
6. **Land the message** (30s): "Data → model → live prediction on one platform. Any analyst in this room could have kicked this off."

**Fallback if serving is slow:** show a pre-created endpoint, or just show batch predictions from the AutoML notebook (`predict` on a held-out set). Don't let a cold endpoint kill momentum.

---

## ✂️ Cut-list — if you're behind at the break

Trim in this order; each keeps the story intact:
1. **M7 Part B (Supervisor Agent) → make it a 3-min demo** instead of hands-on. Part A (RAG) is the crowd-pleaser; keep it hands-on.
2. **M6 sample questions → seed only 2** instead of 5; skip the refine loop.
3. **M5 → build 2 charts** instead of 3; skip the map, keep bar + line.
4. **M2 → one Assistant prompt** together, skip the free-play.
5. Absolute worst case: **M3 → demo the share** on screen with one volunteer instead of everyone pairing.

Protect at all costs: **M1 (the upload aha)**, **M6 (Genie)**, **M7 Part A (RAG)** — these get the biggest reactions.

---

## 🗣️ Talking points per module (business value)

- **M1:** "Unity Catalog is one governance layer for *everything* — tables, files, models, dashboards, AI agents. Uploading data is drag-and-drop. No infra ticket, no ETL project."
- **M2:** "The AI Assistant works across notebooks, SQL editor, Lakeflow. You describe intent; it writes the code. Accelerates every practitioner."
- **M3:** "Real-time co-editing like Google Docs, but for data and analytics. Permissions inherit from Unity Catalog — safe by default. No more emailing CSVs."
- **M4:** "From raw table to deployed model in minutes, no ML PhD. Data → model → production endpoint, one platform, no handoff."
- **M5:** "Dashboards live *next* to the data — no export, no separate BI licence, no stale copy. Refreshes automatically."
- **M6:** "Genie is your team's data analyst on call. Democratizes access without losing governance. Instructions + examples are how you make it trustworthy."
- **M7:** "From 'we should build a chatbot someday' to a working, grounded assistant in under 30 minutes. Governed by Unity Catalog end-to-end."

---

## 🧯 Common issues & fast fixes

| Symptom | Fix |
|---------|-----|
| User can't create catalog | Grant `CREATE CATALOG` on metastore, or pre-create `name_bank` catalogs and grant `ALL PRIVILEGES` |
| `00-setup` can't find `config/` | They opened a single file, not the cloned Git folder. Re-clone via Repos |
| Upload table option missing | Use **+** at top of sidebar → Add data → Create or modify table |
| Genie gives wrong answers | Add an instruction defining the term; add a sample SQL question |
| Knowledge Assistant empty | Verify volume path + PDFs in `product_docs/`; wait for indexing to finish |
| Serving endpoint cold (M4) | Use pre-warmed endpoint or show batch predict |
| Someone way behind | Pair them with a finished neighbour; use checkpoints to resync the room |

---

## 🔁 Reusing this asset for another customer

1. Copy `config/profiles/meridian.py` → `config/profiles/<customer>.py`, edit labels.
2. Drop the customer's product PDFs into `data/pds_documents/<customer>/`.
3. Set `ACTIVE_BANK = "<customer>"` in `config/workshop_config.py`.
4. The CSV data is brand-neutral — no changes needed.
5. Optionally find/replace the bank name in `LAB-GUIDE.md` intro (or leave generic).
