# 🧪 Participant Lab Guide
## End-to-End Databricks Hands-On Workshop

> ### 👋 You are all data practitioners today 💪
> For the next 3 hours, forget your job title. Whether you're a Data Engineer, Data Scientist, BI Analyst, or work in the Data Warehouse team — **today you are all of them.** You'll load data, explore it with AI, collaborate live, build a dashboard, and create your own AI assistant.
>
> **It's not as scary as you think.** Every step below has a copy-paste block and a ✅ checkpoint. If you can copy, paste, and click **Run**, you can do this. When you hit a green checkmark, give the room a 👍.

---

### 📖 How to read this guide
Each module follows the **same rhythm**, so you always know where you are:

- 🎯 **Goal** — one sentence on what you'll achieve
- 🛠️ **Steps** — numbered clicks, nothing skipped
- 📋 **Copy me** — code blocks you paste (don't type it out!)
- ✅ **Checkpoint** — what you should see when it worked
- 💡 **Stuck?** — the one or two things that trip people up

> **Naming reminder:** Everywhere you see `<your_catalog>`, replace it with your catalog from setup (e.g. `ali_bank`). Your schema is always `retail_360`.

---

## 🧰 Module 0 — Setup (5 min, do this first)

🎯 **Goal:** Create your personal catalog, schema, volume, and tables.

🛠️ **Steps**
1. In the left sidebar, make sure you're in the cloned Git folder for this workshop.
2. Open **`00-setup`** (at the top level of the repo).
3. At the top of the notebook, find the **`your_name`** widget → type your name in lowercase (e.g. `ali`).
4. Click **Run all** (▶▶ at the top).
5. Wait ~1 minute for the big green **✅ SETUP COMPLETE** box.

✅ **Checkpoint:** You see `✅ SETUP COMPLETE` and your catalog name (e.g. `ali_bank`). In the left sidebar under **Catalog**, you can find `<your_catalog>` → `retail_360` → 4 tables.

💡 **Stuck?**
- No green box? Check you typed a name in the widget and clicked **Run all**, not just one cell.
- Want a clean restart? Set the `reset` widget to `yes` and Run all again.

---

## 📥 Module 1 — Catalog, Schema & CSV Upload (20 min)

🎯 **Goal:** See how governed data lives in Unity Catalog, and upload your first table by hand.

🛠️ **Steps**
1. In the left sidebar, click **Catalog** 🗂️.
2. Expand `<your_catalog>` → `retail_360`. Notice the 4 tables setup created for you (accounts, transactions, products, branches).
3. Click the **`transactions`** table. Explore the tabs: **Columns**, **Sample Data**, **Details**. Notice the description we added — this is your governance layer.
4. Now **upload `customers.csv` yourself.** First, download it from your volume:
   - Go to `<your_catalog>` → `retail_360` → **Volumes** → `raw_files`.
   - Click **`customers.csv`** → **⋮** (or the download icon) → **Download**. Save it to your laptop.
5. Click **+ (Add / Create)** at the top of the sidebar → **Add data** → **Create or modify table**.
6. **Drag `customers.csv`** into the upload box (or browse to it).
7. Set the destination: **Catalog** = `<your_catalog>`, **Schema** = `retail_360`, **Table name** = `customers`.
8. Preview looks good? Click **Create table**.

📋 **Copy me** — after upload, run this in a **SQL editor** (or a notebook cell with `%sql`) to confirm and add a tag:
```sql
-- Confirm your table loaded
SELECT segment, COUNT(*) AS customers, ROUND(AVG(age), 1) AS avg_age
FROM `<your_catalog>`.retail_360.customers
GROUP BY segment
ORDER BY customers DESC;
```
```sql
-- Add a table description (documentation in one line)
COMMENT ON TABLE `<your_catalog>`.retail_360.customers IS
  'Retail banking customers: demographics, segment, income band, home branch.';
```
```sql
-- Tag the region COLUMN as PII. This is the attribute a policy will match on.
ALTER TABLE `<your_catalog>`.retail_360.customers
  ALTER COLUMN region SET TAGS ('pii' = 'true');
```

✅ **Checkpoint:** `customers` now appears as a 5th table under `retail_360`, the query returns ~800 customers across segments, and on the **Details / Columns** tab the `region` column shows the `pii` tag.

🙌 **Your Turn — govern by attribute (7 min)**
You've tagged `region` as PII. Now create a **policy** that automatically masks *any* column carrying that tag — using the `mask_pii` function that setup pre-built for you. This is **ABAC**: govern by attribute (the tag), not column-by-column.

1. **See the raw value first.** Note the real region values before masking:
   ```sql
   SELECT customer_id, region, segment
   FROM `<your_catalog>`.retail_360.customers
   LIMIT 5;
   ```
2. **Create your own column-mask policy** that matches the `pii` tag and applies the pre-built function:
   ```sql
   CREATE OR REPLACE POLICY mask_pii_columns
   ON SCHEMA `<your_catalog>`.retail_360
   COMMENT 'Mask any column tagged pii using the mask_pii function'
   COLUMN MASK `<your_catalog>`.retail_360.mask_pii
   TO `account users`
   FOR TABLES
   MATCH COLUMNS has_tag_value('pii', 'true') AS pii_col
   ON COLUMN pii_col;
   ```
3. **Query again and watch it mask.** Re-run the query from step 1 — `region` now shows `***REDACTED***`, while `segment` (untagged) is untouched:
   ```sql
   SELECT customer_id, region, segment
   FROM `<your_catalog>`.retail_360.customers
   LIMIT 5;
   ```
4. **The attribute-based payoff.** Tag a *second* column and see the **same policy** mask it automatically — no policy change needed:
   ```sql
   ALTER TABLE `<your_catalog>`.retail_360.customers
     ALTER COLUMN name SET TAGS ('pii' = 'true');
   -- now query name + region; both are masked by the one policy you wrote
   SELECT customer_id, name, region, segment
   FROM `<your_catalog>`.retail_360.customers
   LIMIT 5;
   ```

> 💡 That's the power of ABAC: you wrote **one** policy against a *tag*, and every current and future column with that tag is governed automatically.

💡 **Stuck?**
- Can't find **Create or modify table**? Use the **+** button at the very top of the left sidebar → **Add data**.
- Backtick reminder: wrap the catalog name in backticks `` ` `` if your name has anything unusual.

---

## 🤖 Module 2 — Exploring Data with Genie / Assistant Code (20 min)

🎯 **Goal:** Use the AI Assistant to write and understand SQL & Python — no need to remember syntax.

🛠️ **Steps**
1. Create a new notebook: **+ → Notebook**. Rename it `my-exploration`.
2. Attach it to **Serverless** compute (top-right dropdown).
3. Set your working context by running this first cell:

📋 **Copy me**
```python
catalog = "<your_catalog>"   # e.g. ali_bank
spark.sql(f"USE CATALOG {catalog}")
spark.sql("USE SCHEMA retail_360")
print("Working in", catalog, "retail_360")
```

4. Open the **Assistant** panel (✨ icon on the right, or `Cmd/Ctrl + I` in a cell).
5. Try asking it — in **plain English** — to write code for you. Type these prompts into the Assistant:
   - *"Write SQL to show total transaction amount by category for this schema, highest first."*
   - *"Now write PySpark to find the top 10 customers by total spend, joining customers and transactions."*
   - *"Explain what this query does"* (highlight any query first).
6. Run the code it generates. Tweak a prompt and re-ask.

📋 **Copy me** — a starter query if you'd rather run something now:
```sql
%sql
SELECT c.segment,
       ROUND(SUM(t.amount_myr), 2) AS total_spend,
       COUNT(DISTINCT c.customer_id) AS customers
FROM customers c
JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY c.segment
ORDER BY total_spend DESC;
```

✅ **Checkpoint:** You've generated at least one query with the Assistant and seen a result table. You understand you can ask for SQL *or* Python and it adapts.

🙌 **Your Turn — try these (5 min)**
1. **Ask for a new angle.** Prompt the Assistant: *"Write SQL for the average transaction amount by channel, most-used channel first."* Run it.
2. **Translate languages.** Highlight any SQL query and ask the Assistant: *"Convert this to PySpark."* Notice it keeps the logic, changes the syntax.
3. **Make it explain itself.** Highlight a query → ask *"Add an inline comment to each line explaining what it does."*

💡 **Stuck?**
- Assistant not showing? Click the ✨ sparkle icon on the far right edge of the screen.
- "Table not found"? Make sure you ran the `USE CATALOG` cell first (Step 3).

---

## 🤝 Module 3 — Collaborating with Your Team (15 min)

🎯 **Goal:** Experience real-time collaboration — two people, same data, no email attachments.

> 👥 **Pair up with the person next to you.** Decide who is **Person A** and who is **Person B**.

🛠️ **Steps**

**Person A — share your notebook:**
1. Open your `my-exploration` notebook.
2. Click **Share** (top-right).
3. Enter **Person B's** email → give **Can Edit** → **Add**. Done.

**Person B — join and add data:**
4. Open the notebook A shared with you (check **Recents** or **Shared with me**).
5. You'll both see each other's cursors — like Google Docs. 👀
6. Add a new cell and run a join across A's tables with the products table:

📋 **Copy me** (Person B runs this — note: use **Person A's** catalog):
```sql
%sql
SELECT p.product_name,
       p.product_type,
       COUNT(a.account_id) AS num_accounts,
       ROUND(AVG(a.balance_myr), 2) AS avg_balance
FROM `<personA_catalog>`.retail_360.accounts a
JOIN `<personA_catalog>`.retail_360.products p
  ON a.product_id = p.product_id
GROUP BY p.product_name, p.product_type
ORDER BY num_accounts DESC;
```
7. **Person A**, watch the result appear on your screen in real time. Add a `%md` cell together describing what you found.

✅ **Checkpoint:** Both partners see the same joined result and each other's edits live. You joined two tables owned by one person, accessed by another — governed automatically by Unity Catalog.

🙌 **Your Turn — try these (5 min)**
1. **Co-write a finding.** Together, add a `%md` cell that names the **top product by number of accounts** from the query above.
2. **Swap roles.** Now **Person B** shares *their* `my-exploration` notebook back to **Person A** with **Can Edit**.
3. **Leave a comment.** Highlight a cell → **Comment** → `@mention` your partner with a question. Watch it appear on their screen.

💡 **Stuck?**
- B can't see the notebook? A should double-check the email and that permission is **Can Edit**.
- Permission error on the query? The catalog owner (A) may need to grant `SELECT`. Ask the facilitator to show a quick `GRANT`.

---

## 🧠 Module 4 — AutoML + Inference *(watch the facilitator)* (15 min)

🎯 **Goal:** See how the platform goes from a table to a deployed ML model — **"Next Best Offer"** — in minutes.

> 🎬 **This module is a demo.** Sit back and watch the facilitator. No hands-on needed — just follow the story.

**What you'll see the facilitator do:**
1. Point **AutoML** at a `customer_360_features` table where the target column is **`next_best_offer`** (which product to recommend each customer next).
2. Start a **Classification** experiment — AutoML tries dozens of models automatically.
3. Review the **leaderboard** — best model on top, with a generated notebook for each.
4. **Register** the winning model to Unity Catalog.
5. Deploy it to a **real-time serving endpoint** and hit it with a REST call to get a live prediction.

💬 **Why it matters:** Data → model → production endpoint on **one platform**. No handoff to a separate ML team, no separate MLOps toolchain. The same governed tables you explored become the fuel for ML.

🙌 **Your Turn — think about it (discussion)**
No hands-on here — just get your brain going for the round-table later:
1. **Spot a feature.** Looking at the columns the facilitator used, name **one more feature** you'd add to improve "Next Best Offer" (e.g. months since last product opened).
2. **Name the action.** If the model says a customer's next best offer is *Home Financing-i*, **what should the bank actually do** with that prediction?

✅ **Checkpoint (mental):** You understand that "Next Best Offer" turns your customer + transaction data into a prediction the business can act on — and that any analyst here could kick off AutoML.

---

## ☕ Break (5 min)

Stretch, grab a drink. When you're back, we build dashboards. Everyone with a ✅ so far, thumbs up!

---

## 📊 Module 5 — Building a Dashboard (25 min)

🎯 **Goal:** Turn your data into a shareable AI/BI dashboard for stakeholders.

🛠️ **Steps**
1. Left sidebar → **Dashboards** → **Create dashboard**. Name it `<your_name> Retail 360`.
2. Go to the **Data** tab → **+ Add data** → pick your `<your_catalog>.retail_360` tables. Add **transactions**, **customers**, and **products**.
3. Go to the **Canvas** tab. Click **Add a visualization** (chart icon).
4. Build three charts by describing them or dragging fields:

📋 **Copy me** — if you'd rather define a dataset with SQL, use the **Data** tab → **Create from SQL**:
```sql
SELECT c.state,
       c.segment,
       t.category,
       t.channel,
       t.amount_myr,
       t.txn_date
FROM `<your_catalog>`.retail_360.customers c
JOIN `<your_catalog>`.retail_360.transactions t
  ON c.customer_id = t.customer_id;
```

5. **Chart 1 — Bar:** Total `amount_myr` by `category`.
6. **Chart 2 — Map or Bar:** Customers (or spend) by `state`.
7. **Chart 3 — Line:** `amount_myr` over `txn_date` (by month).
8. Add a **Filter** widget on `segment` (so viewers can slice by customer segment).
9. Click **Publish** (top-right) → then **Share** → add your neighbour as a viewer.

✅ **Checkpoint:** A published dashboard with 3 charts + a working segment filter. Toggle the filter and watch every chart update. Your neighbour can open your link.

🙌 **Your Turn — try these (5 min)**
1. **Add a big number.** Add a **Counter** visualization showing **total customers** (or total spend in MYR).
2. **Slice it differently.** Add a second **Filter** widget on `state` and watch the charts react.
3. **Let AI build one.** Use the dashboard's **Assistant** — type *"chart of average transaction amount by channel"* and add the result to your canvas.

💡 **Stuck?**
- No data in a chart? Confirm you added the tables/dataset in the **Data** tab first.
- Chart looks empty? Check the field you dropped on the axis matches the dataset (e.g. `amount_myr` is numeric).

---

## 💬 Module 6 — Building Your Own Genie Space (25 min)

🎯 **Goal:** Package your data + business context so anyone can ask it questions in plain English.

🛠️ **Steps**
1. Left sidebar → **Genie** → **New** (or **+ Genie space**).
2. Name it `<your_name> Retail Genie`.
3. **Add tables:** choose from `<your_catalog>.retail_360` → add **customers**, **transactions**, **products**, **accounts**.
4. **Add instructions** (this is what makes Genie smart). Paste these:

📋 **Copy me** — general instructions:
```
This Genie space answers questions about a retail bank's customers, their
accounts, transactions and products.
- "spend" or "spending" means SUM(transactions.amount_myr).
- "product holdings" means rows in the accounts table joined to products.
- income_band values are: <3K, 3K-5K, 5K-8K, 8K-12K, 12K-20K, >20K.
- Always show amounts in MYR (RM) and round to 2 decimals.
- A customer's "segment" is one of: Mass, Mass Affluent, Affluent, Youth, Senior.
```

5. **Add sample questions** (SQL example queries teach Genie your patterns). Add these as sample/trusted questions:

📋 **Copy me** — sample questions to seed:
```
1. What is the total transaction amount by product category?
2. Which customer segment has the highest average spend?
3. Show the number of accounts per product type.
4. Which states have the most customers?
5. List the top 10 customers by total transaction amount.
```

6. Click into the chat and **test it** — ask: *"Which segment spends the most on Dining?"* and *"How many customers are in Selangor?"*
7. Refine one instruction if an answer looks off, then re-ask.
8. **Share** the Genie space with your neighbour.

✅ **Checkpoint:** Genie answers at least two of your questions correctly with a table/chart, and your neighbour can open the space.

🙌 **Your Turn — try these (5 min)**
1. **Teach Genie a new term.** Add one instruction, e.g. *"A 'digital customer' is one whose transactions are mostly on Mobile App or Internet Banking."* Then ask *"How many digital customers do we have?"*
2. **Add your own trusted question.** Create one sample question that matters to you (e.g. *"Average balance by product type"*) and save it.
3. **Push it harder.** Ask a comparison: *"Compare total spend between Youth and Senior segments."* Refine an instruction if the answer looks off.

💡 **Stuck?**
- Wrong answer? Add or sharpen an **instruction** (e.g. define the term it got wrong), then ask again.
- Genie can't find a column? Make sure the relevant table is added to the space.

---

## 🦾 Module 7 — Knowledge Assistant + Supervisor Agent (30 min)

🎯 **Goal:** Build a no-code AI assistant — one that answers from your **documents** (RAG), and one that **orchestrates across your Genie spaces**.

### Part A — Knowledge Assistant (RAG on product PDFs) — 15 min

🛠️ **Steps**
1. Left sidebar → **Agents** (Agent Bricks) → **Knowledge Assistant** → **Create**.
2. Name it `<your_name> Product Helper`.
3. **Add a knowledge source** → point it at your product docs in the volume:
   - Path: `/Volumes/<your_catalog>/retail_360/raw_files/product_docs/`
   - This folder holds the bank's **Product Disclosure Sheet** PDFs.
4. Give it a short description: *"Answers customer questions about our financing and deposit products using the official product disclosure sheets."*
5. Let it build (it chunks + indexes the PDFs automatically). Then **test in the chat**:

📋 **Copy me** — questions to ask your Knowledge Assistant:
```
1. What is the profit rate for Personal Financing-i?
2. What is the minimum deposit for the Term Deposit account?
3. What are the eligibility requirements for Vehicle Financing-i?
4. Which Shariah concept does Home Financing-i use?
```

✅ **Checkpoint (Part A):** The assistant answers a product question and **cites the PDF** it pulled the answer from.

🙌 **Your Turn — try these (5 min)**
1. **Cross-document question.** Ask: *"Compare the profit rate of Personal Financing-i and Home Financing-i."* — it should pull from **two** PDFs.
2. **Dig into fees.** Ask about the **fees or late payment charges** for any one product and check the citation.

### Part B — Supervisor Agent (orchestrates your Genies) — 15 min

🛠️ **Steps**
6. Left sidebar → **Agents** → **Multi-Agent Supervisor** → **Create**. Name it `<your_name> Bank Assistant`.
7. **Add agents** for it to orchestrate:
   - Your **`<your_name> Retail Genie`** (from Module 6) — for structured data questions.
   - Your **`<your_name> Product Helper`** (from Part A) — for product document questions.
8. Give the supervisor a description: *"Routes banking questions to the right specialist: data questions to the Retail Genie, product questions to the Product Helper."*
9. **Test the routing** in chat — ask a mix and watch which specialist it calls:

📋 **Copy me** — questions that test orchestration:
```
1. How many customers do we have in Johor?          (→ Retail Genie)
2. What is the profit rate on Personal Financing-i?  (→ Product Helper)
3. Which segment spends most, and what financing product could we offer them?
                                                     (→ uses both!)
```

✅ **Checkpoint (Part B):** The Supervisor routes each question to the right agent, and the combined question touches both. You just built a working assistant in under 30 minutes — grounded on your data and documents, governed by Unity Catalog.

🙌 **Your Turn — try these (5 min)**
1. **Force a hand-off.** Ask a data question then a product question back-to-back, and watch which specialist each one routes to.
2. **One question, both agents.** Ask: *"Which segment holds the fewest financing products, and what are the eligibility requirements for Personal Financing-i?"*

💡 **Stuck?**
- Knowledge Assistant returns nothing? Confirm the volume path is exact and the PDFs are in `product_docs/` (setup put them there).
- Supervisor doesn't route well? Improve each sub-agent's **description** — the supervisor uses descriptions to decide who answers.

---

## 🏁 Wrap-up & Next Steps (10 min)

🎉 **Look what you built this morning — as one person, in one browser tab:**

| Module | You built |
|--------|-----------|
| 1 | A governed catalog + uploaded your own table |
| 2 | AI-assisted data exploration |
| 3 | Live collaboration on shared data |
| 4 | (Saw) an ML model for Next Best Offer |
| 5 | A published, shareable dashboard |
| 6 | Your own natural-language Genie space |
| 7 | A RAG knowledge assistant + a supervisor agent |

**Round-table:** think of **one use case** from your real work at the bank you'd bring back to this platform. We'll go around the room.

> One platform, one morning — you built what usually takes multiple teams and weeks. **What's your first project?**

---

### 📎 Appendix — Quick reference

**Your objects**
- Catalog: `<your_catalog>` (e.g. `ali_bank`)
- Schema: `retail_360`
- Volume: `/Volumes/<your_catalog>/retail_360/raw_files/`
- Product docs: `/Volumes/<your_catalog>/retail_360/raw_files/product_docs/`

**Tables**
| Table | What's in it |
|-------|--------------|
| `customers` | demographics, segment, income_band, home branch (you upload in M1) |
| `accounts` | product holdings per customer + balances |
| `transactions` | ~15k transactions: amount, channel, category, merchant |
| `products` | product catalog with profit rates |
| `branches` | branch + state + region |
