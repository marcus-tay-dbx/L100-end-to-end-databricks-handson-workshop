#!/usr/bin/env python3
"""
Meridian Bank — Retail Banking 360 synthetic dataset generator.

Pure Python standard library only (no pandas / numpy / faker) so it runs
anywhere, including a stock Databricks driver or a laptop with no installs.

Produces five CSVs under ../ (the repo `data/` folder):
    customers.csv       ~800 rows   core entity
    accounts.csv        ~1,200 rows customer <-> product holdings
    transactions.csv    ~15,000 rows spending activity
    products.csv        12 rows     Meridian product catalog
    branches.csv        30 rows     branch / geo dimension

The dataset is 100% FICTIONAL. "Meridian Bank", all customers, accounts and
transactions are invented. It is designed so that a "Next Best Offer" (NBO)
classification model trained on engineered features finds real, explainable
signal — see build_customer_features() in the workshop notebooks.

Deterministic: a fixed RNG seed means re-running reproduces byte-identical
CSVs, so the committed data and any regenerated data always match.
"""

import csv
import os
import random
from datetime import date, timedelta

# --------------------------------------------------------------------------
# Determinism
# --------------------------------------------------------------------------
SEED = 20260715
rng = random.Random(SEED)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, ".."))  # repo data/ folder

TODAY = date(2026, 7, 15)  # fixed "today" so tenure/recency are reproducible

# --------------------------------------------------------------------------
# Reference vocabularies (Malaysian retail-banking flavour, all fictional)
# --------------------------------------------------------------------------
MALE_FIRST = [
    "Ahmad", "Muhammad", "Mohd", "Ali", "Hafiz", "Firdaus", "Zulkifli", "Amir",
    "Faizal", "Haziq", "Iqbal", "Rizal", "Syafiq", "Danial", "Aiman", "Khairul",
    "Wei Jie", "Jun Wei", "Kok Wah", "Wai Kit", "Arun", "Suresh", "Ramesh", "Kumar",
]
FEMALE_FIRST = [
    "Nurul", "Siti", "Aisyah", "Farah", "Nadia", "Aina", "Hana", "Zulaikha",
    "Balqis", "Sofia", "Alya", "Damia", "Wan", "Noraini", "Fatimah", "Liyana",
    "Mei Ling", "Xin Yi", "Hui Fen", "Li Wen", "Priya", "Kavitha", "Divya", "Anjali",
]
LAST = [
    "bin Abdullah", "bin Ismail", "bin Hassan", "bin Osman", "binti Rahman",
    "binti Yusof", "binti Ibrahim", "binti Karim", "Tan", "Lim", "Lee", "Wong",
    "a/l Muthu", "a/p Samy", "a/l Raj", "Ng", "Chong", "Goh",
]
STATES = [
    ("Selangor", "Central"), ("Kuala Lumpur", "Central"), ("Putrajaya", "Central"),
    ("Johor", "Southern"), ("Melaka", "Southern"), ("Negeri Sembilan", "Southern"),
    ("Penang", "Northern"), ("Kedah", "Northern"), ("Perak", "Northern"),
    ("Perlis", "Northern"), ("Kelantan", "East Coast"), ("Terengganu", "East Coast"),
    ("Pahang", "East Coast"), ("Sabah", "East Malaysia"), ("Sarawak", "East Malaysia"),
]
SEGMENTS = ["Mass", "Mass Affluent", "Affluent", "Youth", "Senior"]
INCOME_BANDS = ["<3K", "3K-5K", "5K-8K", "8K-12K", "12K-20K", ">20K"]
INCOME_ORDER = {b: i for i, b in enumerate(INCOME_BANDS)}

CHANNELS = ["Mobile App", "Internet Banking", "ATM", "Branch", "Debit Card", "QR Pay"]
TXN_CATEGORIES = [
    "Groceries", "Dining", "Fuel", "Utilities", "Retail Shopping", "Healthcare",
    "Education", "Travel", "Telco", "Entertainment", "Transfer", "Cash Withdrawal",
]
MERCHANTS = {
    "Groceries": ["FreshMart", "GiantValue", "TescoLite", "Jaya Grocer Co", "MyMart"],
    "Dining": ["Nasi Kandar House", "KopiTiam Central", "BurgerLab", "Sushi Express", "Kenny's Grill"],
    "Fuel": ["PetroMax", "ShellPlus", "Petronas Station", "BHP Fuel", "Caltex Go"],
    "Utilities": ["TNB Bill", "Air Selangor", "Indah Water", "Astro", "Unifi"],
    "Retail Shopping": ["Uniqlo MY", "H&M Central", "Padini Store", "MR DIY", "Harvey Norman"],
    "Healthcare": ["Guardian Pharma", "Watsons", "Klinik Mediviron", "BP Healthcare", "Caring Pharm"],
    "Education": ["EduBooks", "SkillUp Academy", "Little Genius", "TuitionPro", "Coursera MY"],
    "Travel": ["AirAsia", "MAS Booking", "Agoda MY", "Grab Rides", "KTM Berhad"],
    "Telco": ["Maxis", "Celcom", "Digi", "U Mobile", "Yes 5G"],
    "Entertainment": ["GSC Cinemas", "Spotify MY", "Netflix MY", "Steam", "TGV Movies"],
    "Transfer": ["DuitNow Transfer", "Instant Transfer", "IBG Transfer"],
    "Cash Withdrawal": ["ATM Withdrawal"],
}

# Product catalog (product_id, name, type, profit_rate %, min_amount RM)
PRODUCTS = [
    ("P01", "Savings-i Account",            "Deposit",    0.25, 20),
    ("P02", "Term Deposit-i",               "Deposit",    3.85, 1000),
    ("P03", "Current Account-i",            "Deposit",    0.00, 500),
    ("P04", "Personal Financing-i",         "Financing",  4.50, 5000),
    ("P05", "Home Financing-i",             "Financing",  3.85, 50000),
    ("P06", "Vehicle Financing-i",          "Financing",  3.40, 20000),
    ("P07", "Education Financing-i",        "Financing",  3.75, 10000),
    ("P08", "Micro Financing-i",            "Financing",  6.00, 1000),
    ("P09", "Cash Line-i",                  "Financing",  7.50, 3000),
    ("P10", "Credit Card-i",                "Card",       0.00, 0),
    ("P11", "Investment-i Fund",            "Wealth",     0.00, 1000),
    ("P12", "Takaful Protection-i",         "Protection", 0.00, 0),
]
PRODUCT_IDS = [p[0] for p in PRODUCTS]

# The set of products a "Next Best Offer" model recommends (financing/wealth
# up-sell targets). "None" means the customer is well-served already.
NBO_CLASSES = [
    "Personal Financing-i", "Home Financing-i", "Vehicle Financing-i",
    "Education Financing-i", "Term Deposit-i", "Credit Card-i",
    "Investment-i Fund", "None",
]


def full_name():
    if rng.random() < 0.5:
        first = rng.choice(MALE_FIRST)
        gender = "M"
    else:
        first = rng.choice(FEMALE_FIRST)
        gender = "F"
    return f"{first} {rng.choice(LAST)}", gender


def rand_date(start_year, end_year):
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 28)
    delta = (end - start).days
    return start + timedelta(days=rng.randint(0, delta))


# --------------------------------------------------------------------------
# 1. Branches
# --------------------------------------------------------------------------
def gen_branches():
    # Branch names are deliberately BRAND-NEUTRAL (no bank name) so the CSV
    # data is reusable across customers. The bank name is applied only via the
    # config profile in the setup notebook and lab guide, never baked into data.
    rows = []
    bid = 1
    for state, region in STATES:
        n = rng.randint(1, 3)
        for i in range(n):
            rows.append({
                "branch_id": f"B{bid:03d}",
                "branch_name": f"{state} {'Main Branch' if i == 0 else 'Branch ' + str(i)}",
                "state": state,
                "region": region,
            })
            bid += 1
            if len(rows) >= 30:
                break
        if len(rows) >= 30:
            break
    return rows[:30]


# --------------------------------------------------------------------------
# 2. Customers  (with hidden propensity attributes used to shape NBO later)
# --------------------------------------------------------------------------
def gen_customers(n, branches):
    rows = []
    for i in range(1, n + 1):
        name, gender = full_name()
        age = rng.choices(
            population=[rng.randint(18, 25), rng.randint(26, 35),
                        rng.randint(36, 45), rng.randint(46, 60),
                        rng.randint(61, 78)],
            weights=[18, 30, 25, 18, 9],
        )[0]
        state, region = rng.choice(STATES)

        # income correlates loosely with age
        if age < 26:
            income = rng.choices(INCOME_BANDS, weights=[40, 35, 15, 7, 2, 1])[0]
        elif age < 36:
            income = rng.choices(INCOME_BANDS, weights=[15, 30, 30, 15, 8, 2])[0]
        elif age < 46:
            income = rng.choices(INCOME_BANDS, weights=[8, 20, 28, 24, 15, 5])[0]
        elif age < 61:
            income = rng.choices(INCOME_BANDS, weights=[10, 22, 26, 22, 14, 6])[0]
        else:
            income = rng.choices(INCOME_BANDS, weights=[25, 30, 22, 13, 7, 3])[0]

        # SEGMENTS = ["Mass", "Mass Affluent", "Affluent", "Youth", "Senior"]
        # Youth only for <26, Senior only for >=61 -> no mismatched age/segment.
        if age < 26:
            segment = rng.choices(["Mass", "Mass Affluent", "Youth"], weights=[30, 12, 58])[0]
        elif age >= 61:
            segment = rng.choices(["Mass", "Mass Affluent", "Affluent", "Senior"],
                                  weights=[30, 18, 8, 44])[0]
        else:
            hi = INCOME_ORDER[income]
            if hi >= 4:
                segment = rng.choices(["Mass", "Mass Affluent", "Affluent"], weights=[12, 38, 50])[0]
            elif hi >= 2:
                segment = rng.choices(["Mass", "Mass Affluent", "Affluent"], weights=[50, 38, 12])[0]
            else:
                segment = rng.choices(["Mass", "Mass Affluent", "Affluent"], weights=[78, 18, 4])[0]

        join = rand_date(2012, 2026)
        rows.append({
            "customer_id": f"C{i:05d}",
            "name": name,
            "gender": gender,
            "age": age,
            "state": state,
            "region": region,
            "segment": segment,
            "income_band": income,
            "home_branch_id": rng.choice(branches)["branch_id"],
            "join_date": join.isoformat(),
        })
    return rows


# --------------------------------------------------------------------------
# 3. Accounts  (product holdings per customer)
# --------------------------------------------------------------------------
def gen_accounts(customers):
    rows = []
    aid = 1
    holdings = {}  # customer_id -> set(product_id)
    for c in customers:
        cid = c["customer_id"]
        held = set()

        # Almost everyone has a Savings-i
        if rng.random() < 0.95:
            held.add("P01")
        # Some have current account
        if rng.random() < 0.25:
            held.add("P03")

        hi = INCOME_ORDER[c["income_band"]]
        age = c["age"]

        # Term deposit: older + higher income + idle cash
        if rng.random() < (0.05 + 0.04 * hi + (0.15 if age >= 55 else 0)):
            held.add("P02")
        # Home financing: 30-50, mid-high income
        if 30 <= age <= 52 and rng.random() < (0.05 + 0.05 * hi):
            held.add("P05")
        # Vehicle financing
        if 25 <= age <= 55 and rng.random() < 0.18:
            held.add("P06")
        # Personal financing
        if rng.random() < 0.15:
            held.add("P04")
        # Credit card: mid+ income
        if hi >= 2 and rng.random() < 0.30:
            held.add("P10")
        # Investment: affluent
        if hi >= 4 and rng.random() < 0.35:
            held.add("P11")

        pmeta = {p[0]: p for p in PRODUCTS}
        for pid in held:
            meta = pmeta[pid]
            ptype = meta[2]
            if ptype == "Deposit":
                if pid == "P02":
                    bal = round(rng.uniform(5000, 120000) * (1 + 0.3 * hi), 2)
                else:
                    bal = round(rng.uniform(200, 40000) * (1 + 0.2 * hi), 2)
            elif ptype == "Financing":
                bal = -round(rng.uniform(meta[4], meta[4] * 6), 2)  # outstanding
            elif ptype == "Card":
                bal = -round(rng.uniform(0, 15000), 2)
            elif ptype == "Wealth":
                bal = round(rng.uniform(1000, 80000), 2)
            else:
                bal = 0.0
            open_d = rand_date(max(2012, int(c["join_date"][:4])), 2026)
            rows.append({
                "account_id": f"A{aid:06d}",
                "customer_id": cid,
                "product_id": pid,
                "balance_myr": bal,
                "open_date": open_d.isoformat(),
                "status": rng.choices(["Active", "Dormant", "Closed"], weights=[88, 9, 3])[0],
            })
            aid += 1
        holdings[cid] = held
    return rows, holdings


# --------------------------------------------------------------------------
# 4. Transactions
# --------------------------------------------------------------------------
def gen_transactions(customers, target_rows=15000):
    rows = []
    tid = 1
    # digital engagement varies by age -> drives channel + volume
    per_cust = {}
    for c in customers:
        base = 30 - (c["age"] // 4)
        n = max(4, int(rng.gauss(base, 6)))
        per_cust[c["customer_id"]] = (n, c)

    total = sum(v[0] for v in per_cust.values())
    scale = target_rows / total if total else 1
    for cid, (n, c) in per_cust.items():
        n = max(3, int(round(n * scale)))
        digital = c["age"] < 40
        for _ in range(n):
            cat = rng.choice(TXN_CATEGORIES)
            merch = rng.choice(MERCHANTS[cat])
            if digital:
                channel = rng.choices(CHANNELS, weights=[40, 15, 8, 5, 20, 12])[0]
            else:
                channel = rng.choices(CHANNELS, weights=[12, 12, 30, 25, 15, 6])[0]
            amt_ranges = {
                "Groceries": (15, 350), "Dining": (10, 200), "Fuel": (30, 250),
                "Utilities": (40, 500), "Retail Shopping": (20, 1200),
                "Healthcare": (15, 800), "Education": (100, 3000),
                "Travel": (50, 5000), "Telco": (30, 300),
                "Entertainment": (10, 250), "Transfer": (50, 8000),
                "Cash Withdrawal": (50, 2000),
            }
            lo, hi = amt_ranges[cat]
            amt = round(rng.uniform(lo, hi), 2)
            txn_d = rand_date(2025, 2026)
            if txn_d > TODAY:
                txn_d = TODAY
            rows.append({
                "txn_id": f"T{tid:07d}",
                "customer_id": cid,
                "txn_date": txn_d.isoformat(),
                "amount_myr": amt,
                "channel": channel,
                "category": cat,
                "merchant": merch,
            })
            tid += 1
    rng.shuffle(rows)
    return rows


# --------------------------------------------------------------------------
# Writers
# --------------------------------------------------------------------------
def write_csv(name, rows, fieldnames):
    path = os.path.join(OUT, name)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {name:22s} {len(rows):>6,} rows")


def write_products():
    rows = [{
        "product_id": p[0], "product_name": p[1], "product_type": p[2],
        "profit_rate_pct": p[3], "min_amount_myr": p[4],
    } for p in PRODUCTS]
    write_csv("products.csv", rows,
              ["product_id", "product_name", "product_type", "profit_rate_pct", "min_amount_myr"])


def main():
    print(f"Meridian Bank data generator (seed={SEED}) -> {OUT}")
    branches = gen_branches()
    write_csv("branches.csv", branches, ["branch_id", "branch_name", "state", "region"])

    customers = gen_customers(800, branches)
    write_csv("customers.csv", customers,
              ["customer_id", "name", "gender", "age", "state", "region",
               "segment", "income_band", "home_branch_id", "join_date"])

    accounts, holdings = gen_accounts(customers)
    write_csv("accounts.csv", accounts,
              ["account_id", "customer_id", "product_id", "balance_myr", "open_date", "status"])

    txns = gen_transactions(customers, target_rows=15000)
    write_csv("transactions.csv", txns,
              ["txn_id", "customer_id", "txn_date", "amount_myr", "channel", "category", "merchant"])

    write_products()
    print("Done. 5 CSVs generated.")


if __name__ == "__main__":
    main()
