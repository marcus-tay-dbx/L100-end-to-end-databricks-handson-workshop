# L100 — End-to-End Databricks Hands-On Workshop

A **3-hour, hands-on L100 workshop** that takes participants across the entire Databricks Data Intelligence Platform — from uploading a CSV to building AI agents — in one browser tab, one morning.

Everyone plays every role for the day: **Data Engineer → Data Scientist → BI Analyst → ML Engineer**. The lab is built to be *super straightforward, easy, and fun* — every step has a copy-paste block and a ✅ checkpoint.

> 💡 **Reusable across FSI customers.** Branding lives entirely in a config profile — the data is brand-neutral. Change one line to rebrand (see [Reuse](#-reuse-for-another-customer)).

---

## 🗺️ What participants build

| Module | Type | Outcome |
|--------|------|---------|
| 1 · Catalog, Schema & CSV Upload | Hands-on | Governed catalog + upload your own table |
| 2 · Exploring Data with the Assistant | Hands-on | AI-written SQL/Python for EDA |
| 3 · Collaborating with Your Team | Hands-on | Live co-editing on shared data |
| 4 · AutoML + Inference (**Next Best Offer**) | Facilitator demo | Table → model → serving endpoint |
| 5 · Building a Dashboard | Hands-on | Published AI/BI dashboard |
| 6 · Building Your Own Genie Space | Hands-on | Natural-language analytics on your data |
| 7 · Knowledge Assistant + Supervisor Agent | Hands-on | No-code RAG + multi-agent orchestration |

---

## 🚀 For participants — how to start

1. In your Databricks workspace, go to **Workspace → (your folder) → Create → Git folder** (Repos).
2. Clone this repo:
   ```
   https://github.com/marcus-tay-dbx/L100-end-to-end-databricks-handson-workshop.git
   ```
3. Open **`00-setup`** at the top of the repo.
4. Type **your name** in the widget (lowercase, e.g. `ali`) → **Run all**.
5. When you see the green ✅ **SETUP COMPLETE** box, open **`lab-guide/LAB-GUIDE.md`** and start Module 1.

That's it — `00-setup` builds your personal catalog, schema, volume, tables, and loads the product documents.

---

## 📁 Repo structure

```
├── 00-setup.py                 ⭐ The one notebook participants run first
├── README.md
├── config/
│   ├── workshop_config.py       ← set ACTIVE_BANK here to rebrand
│   └── profiles/
│       ├── bank_rakyat.py        (real product PDFs)
│       └── meridian.py           (generic fictional default)
├── data/
│   ├── customers.csv             (uploaded by participants in M1)
│   ├── accounts.csv
│   ├── transactions.csv
│   ├── products.csv
│   ├── branches.csv
│   ├── generator/                (scripts that produced the data + PDFs)
│   └── pds_documents/
│       ├── bank_rakyat/          (real Bank Rakyat PDS PDFs)
│       └── meridian/             (synthetic PDS PDFs)
├── notebooks/
│   └── build_features.py         (facilitator: builds NBO feature table for M4)
├── lab-guide/
│   └── LAB-GUIDE.md              ⭐ The participant handbook (7 modules)
└── facilitator/
    └── FACILITATOR-NOTES.md      timing, M4 demo script, cut-list
```

---

## 🧬 The dataset — "Retail Banking 360"

100% **synthetic** retail-banking data (Malaysian names, MYR, Islamic product terminology). Designed so the **Next Best Offer** ML target has real, learnable signal and Genie/dashboards surface genuine insights.

| Table | Rows | Grain |
|-------|------|-------|
| customers | 800 | one per customer |
| accounts | ~1,500 | one per product holding |
| transactions | ~15,000 | one per transaction |
| products | 12 | product catalog |
| branches | 24 | branch / geo |

Regenerate deterministically anytime:
```bash
python3 data/generator/generate_data.py        # the 5 CSVs
python3 data/generator/generate_pds_pdfs.py     # synthetic Meridian PDS PDFs
```

---

## 🔁 Reuse for another customer

1. Copy `config/profiles/meridian.py` → `config/profiles/<customer>.py`; edit the labels.
2. Drop the customer's product PDFs into `data/pds_documents/<customer>/`.
3. Set `ACTIVE_BANK = "<customer>"` in `config/workshop_config.py`.

The CSV data is brand-neutral, so nothing else changes.

---

## ⚙️ Environment requirements

- Databricks **Free Trial** ($400 / 14-day) — **not** Free Edition (Free Edition can't run Agent Bricks / Module 7).
- **Serverless** compute (SQL warehouse + notebooks).
- **Unity Catalog** with per-user `CREATE CATALOG` privilege.
- **Agent Bricks / Mosaic AI** available in the workspace region.

See `facilitator/FACILITATOR-NOTES.md` for the full pre-day checklist.

---

## ⚠️ Disclaimer

All customer, account, and transaction data in this repository is **fictional and synthetic**. The `meridian` product documents are fictional. The `bank_rakyat` product disclosure sheets are publicly available documents used here for educational/workshop context only. Nothing here constitutes financial advice or real product terms.
