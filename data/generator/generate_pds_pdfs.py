#!/usr/bin/env python3
"""
Generate synthetic "Meridian Bank" Product Disclosure Sheet (PDS) PDFs.

Pure Python standard library only — hand-writes valid PDF 1.4 files, so it
needs no reportlab / fpdf / weasyprint and runs in any offline environment.

Output: ../pds_documents/*.pdf  (the repo data/pds_documents folder)

These are 100% FICTIONAL documents for a made-up institution ("Meridian
Bank"). They exist purely as an unstructured-text corpus for the workshop's
RAG / Knowledge Assistant module. Profit rates, fees and terms are invented
and must not be read as real financial advice.
"""

import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "pds_documents"))

# --------------------------------------------------------------------------
# Minimal PDF writer (text only, multi-page, Helvetica family)
# --------------------------------------------------------------------------
PAGE_W, PAGE_H = 595, 842          # A4 in points
MARGIN_X = 56
TOP_Y = 786
BOTTOM_Y = 56
LEADING = 15                        # line height


def esc(s):
    return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


class Line:
    __slots__ = ("text", "size", "bold", "gap")

    def __init__(self, text, size=10, bold=False, gap=0):
        self.text = text
        self.size = size
        self.bold = bold
        self.gap = gap        # extra vertical space BEFORE this line


def wrap(text, size, bold, max_w=PAGE_W - 2 * MARGIN_X):
    """Greedy word-wrap using an approximate Helvetica advance width."""
    # avg char width factor ~0.52 for Helvetica, a bit wider for bold
    cw = size * (0.55 if bold else 0.52)
    max_chars = max(8, int(max_w / cw))
    words = text.split()
    if not words:
        return [""]
    lines, cur = [], ""
    for w in words:
        trial = w if not cur else cur + " " + w
        if len(trial) <= max_chars:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def paginate(lines):
    """Split Line objects into pages of (y, size, bold, text) draw ops."""
    pages, cur, y = [], [], TOP_Y
    for ln in lines:
        wrapped = wrap(ln.text, ln.size, ln.bold) if ln.text else [""]
        first = True
        for piece in wrapped:
            gap = ln.gap if first else 0
            first = False
            if y - (LEADING + gap) < BOTTOM_Y:
                pages.append(cur)
                cur, y = [], TOP_Y
            y -= (LEADING + gap)
            cur.append((y, ln.size, ln.bold, piece))
    if cur:
        pages.append(cur)
    return pages


def build_content_stream(ops):
    parts = ["BT"]
    last_font = None
    for (y, size, bold, text) in ops:
        font = "F2" if bold else "F1"
        if font != last_font or True:
            parts.append(f"/{font} {size} Tf")
            last_font = font
        parts.append(f"1 0 0 1 {MARGIN_X} {y:.1f} Tm")
        parts.append(f"({esc(text)}) Tj")
    parts.append("ET")
    return "\n".join(parts)


def write_pdf(path, lines):
    pages_ops = paginate(lines)
    objects = []           # list of (obj_number, body_bytes)

    # Fixed objects: 1=Catalog, 2=Pages, 3=Helvetica, 4=Helvetica-Bold
    n_pages = len(pages_ops)
    # page objects start at 5, each page has a content stream object after all pages
    page_obj_ids = [5 + i for i in range(n_pages)]
    content_obj_ids = [5 + n_pages + i for i in range(n_pages)]

    objects.append((1, b"<< /Type /Catalog /Pages 2 0 R >>"))
    kids = " ".join(f"{pid} 0 R" for pid in page_obj_ids)
    objects.append((2, f"<< /Type /Pages /Count {n_pages} /Kids [{kids}] >>".encode()))
    objects.append((3, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"))
    objects.append((4, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>"))

    for i in range(n_pages):
        pid, cid = page_obj_ids[i], content_obj_ids[i]
        page = (f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_W} {PAGE_H}] "
                f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> "
                f"/Contents {cid} 0 R >>")
        objects.append((pid, page.encode()))

    for i in range(n_pages):
        cid = content_obj_ids[i]
        stream = build_content_stream(pages_ops[i]).encode("latin-1", "replace")
        body = b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream)
        objects.append((cid, body))

    objects.sort(key=lambda o: o[0])
    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = {}
    for (num, body) in objects:
        offsets[num] = len(out)
        out += f"{num} 0 obj\n".encode() + body + b"\nendobj\n"

    xref_pos = len(out)
    max_obj = max(offsets)
    out += f"xref\n0 {max_obj + 1}\n".encode()
    out += b"0000000000 65535 f \n"
    for num in range(1, max_obj + 1):
        out += f"{offsets[num]:010d} 00000 n \n".encode()
    out += (f"trailer\n<< /Size {max_obj + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_pos}\n%%EOF").encode()

    with open(path, "wb") as f:
        f.write(out)
    return n_pages


# --------------------------------------------------------------------------
# PDS content builder
# --------------------------------------------------------------------------
DISCLAIMER = (
    "This Product Disclosure Sheet is a FICTIONAL document created by "
    "Meridian Bank (a fictitious institution) solely for a data & AI training "
    "workshop. All rates, fees, and terms are illustrative and do not "
    "constitute financial advice or a real product offering."
)


def pds(title, tagline, sections, effective="1 January 2026", version="01/2026"):
    """sections: list of (heading, [ (label, value) or paragraph string ])"""
    L = []
    L.append(Line("MERIDIAN BANK", 16, True))
    L.append(Line("Product Disclosure Sheet", 11, False, gap=2))
    L.append(Line(title, 15, True, gap=10))
    L.append(Line(tagline, 10, False, gap=2))
    L.append(Line(f"Effective date: {effective}    |    Version: {version}", 9, False, gap=4))
    L.append(Line("-" * 92, 9, False, gap=4))

    for heading, items in sections:
        L.append(Line(heading, 12, True, gap=12))
        for it in items:
            if isinstance(it, tuple):
                label, value = it
                L.append(Line(f"{label}:  {value}", 10, False, gap=2))
            else:
                L.append(Line(it, 10, False, gap=4))

    L.append(Line("-" * 92, 9, False, gap=12))
    L.append(Line("Important Notice", 11, True, gap=8))
    L.append(Line(DISCLAIMER, 9, False, gap=2))
    L.append(Line("For enquiries, contact Meridian Bank Careline at 1-300-00-0000 "
                  "or visit any Meridian branch.", 9, False, gap=6))
    return L


# Product content -----------------------------------------------------------
DOCS = {}

DOCS["Personal_Financing-i"] = pds(
    "Personal Financing-i",
    "A Shariah-compliant personal financing facility based on the concept of Tawarruq.",
    [
        ("Product Overview", [
            "Personal Financing-i provides you with cash for personal use such as "
            "home renovation, education, medical expenses or debt consolidation, "
            "structured under the Shariah concept of Tawarruq (commodity murabahah).",
        ]),
        ("Key Product Features", [
            ("Financing amount", "RM5,000 up to RM200,000"),
            ("Profit rate", "4.50% per annum (fixed) on a flat-rate basis"),
            ("Tenure", "1 year up to 10 years"),
            ("Monthly instalment example", "RM10,000 over 5 years = approx. RM204/month"),
            ("Financing concept", "Tawarruq"),
        ]),
        ("Eligibility", [
            ("Age", "21 to 60 years old at application"),
            ("Minimum income", "RM2,000 per month"),
            ("Nationality", "Malaysian citizen"),
        ]),
        ("Fees and Charges", [
            ("Stamp duty", "0.5% of financing amount (as per Stamp Act 1949)"),
            ("Late payment charge", "1% per annum on overdue instalment"),
            ("Early settlement", "No penalty; rebate (ibra') applies on unearned profit"),
        ]),
        ("Key Risks", [
            "If you fail to meet your monthly obligations, your financing may be "
            "recalled and legal action taken. Late payments affect your credit "
            "standing with credit reference agencies.",
        ]),
    ],
)

DOCS["Home_Financing-i"] = pds(
    "Home Financing-i",
    "Islamic home financing under the concept of Musharakah Mutanaqisah (diminishing partnership).",
    [
        ("Product Overview", [
            "Home Financing-i helps you own residential property through a "
            "diminishing partnership (Musharakah Mutanaqisah) between you and "
            "Meridian Bank. Your share increases as you pay monthly, until you "
            "own the property fully.",
        ]),
        ("Key Product Features", [
            ("Financing amount", "From RM50,000, up to 90% margin of financing"),
            ("Profit rate", "3.85% per annum (variable, benchmarked to base rate)"),
            ("Tenure", "Up to 35 years or age 70, whichever is earlier"),
            ("Financing concept", "Musharakah Mutanaqisah"),
        ]),
        ("Eligibility", [
            ("Age", "21 to 65 years old"),
            ("Minimum income", "RM3,000 per month"),
            ("Property type", "Completed or under-construction residential property"),
        ]),
        ("Fees and Charges", [
            ("Stamp duty", "As per Stamp Act 1949 scale"),
            ("Valuation fee", "Based on market rate; borne by customer"),
            ("Late payment charge", "1% per annum on overdue amount"),
        ]),
        ("Key Risks", [
            "Profit rate is variable; instalments may rise if the base rate "
            "increases. Default may lead to foreclosure of the property.",
        ]),
    ],
)

DOCS["Vehicle_Financing-i"] = pds(
    "Vehicle Financing-i",
    "Shariah-compliant vehicle financing based on Al-Ijarah Thumma Al-Bai (AITAB).",
    [
        ("Product Overview", [
            "Vehicle Financing-i enables you to own a new or used vehicle under "
            "AITAB (hire-purchase then sale). Meridian Bank owns the vehicle and "
            "leases it to you; ownership transfers upon full settlement.",
        ]),
        ("Key Product Features", [
            ("Financing amount", "From RM20,000, up to 90% of vehicle price"),
            ("Profit rate", "3.40% per annum (fixed, flat rate)"),
            ("Tenure", "1 year up to 9 years"),
            ("Financing concept", "AITAB"),
        ]),
        ("Eligibility", [
            ("Age", "18 to 60 years old"),
            ("Minimum income", "RM2,000 per month"),
            ("Vehicle age", "Used vehicles: up to 10 years old at end of tenure"),
        ]),
        ("Fees and Charges", [
            ("Stamp duty", "0.5% of financing amount"),
            ("Late payment charge", "1% per annum on overdue instalment"),
            ("Early settlement", "Rebate (ibra') on unearned profit applies"),
        ]),
        ("Key Risks", [
            "The vehicle may be repossessed if instalments are not paid. "
            "Vehicles depreciate; outstanding financing may exceed resale value.",
        ]),
    ],
)

DOCS["Education_Financing-i"] = pds(
    "Education Financing-i",
    "Financing for tertiary education under the concept of Tawarruq.",
    [
        ("Product Overview", [
            "Education Financing-i funds tuition and study-related expenses for "
            "you or your children at recognised local and overseas institutions.",
        ]),
        ("Key Product Features", [
            ("Financing amount", "RM10,000 up to RM150,000"),
            ("Profit rate", "3.75% per annum (fixed)"),
            ("Tenure", "1 year up to 15 years"),
            ("Grace period", "Optional profit-only payment during study period"),
        ]),
        ("Eligibility", [
            ("Age", "18 to 60 years old (guarantor for students under 18)"),
            ("Minimum income", "RM2,000 per month (parent/guardian)"),
            ("Institution", "Must be a recognised education provider"),
        ]),
        ("Fees and Charges", [
            ("Stamp duty", "0.5% of financing amount"),
            ("Late payment charge", "1% per annum on overdue instalment"),
        ]),
        ("Key Risks", [
            "Completion of study does not guarantee employment; repayment "
            "obligations remain regardless of graduate outcomes.",
        ]),
    ],
)

DOCS["Micro_Financing-i"] = pds(
    "Micro Financing-i",
    "Small-ticket business financing for micro-entrepreneurs under Tawarruq.",
    [
        ("Product Overview", [
            "Micro Financing-i provides working capital or asset purchase "
            "financing for micro and small businesses, including sole "
            "proprietors and gig entrepreneurs.",
        ]),
        ("Key Product Features", [
            ("Financing amount", "RM1,000 up to RM50,000"),
            ("Profit rate", "6.00% per annum"),
            ("Tenure", "6 months up to 7 years"),
            ("Collateral", "No collateral required for amounts below RM20,000"),
        ]),
        ("Eligibility", [
            ("Business age", "Operating for at least 6 months"),
            ("Applicant age", "18 to 60 years old"),
            ("Registration", "Valid SSM or local authority business registration"),
        ]),
        ("Fees and Charges", [
            ("Stamp duty", "0.5% of financing amount"),
            ("Late payment charge", "1% per annum on overdue instalment"),
        ]),
        ("Key Risks", [
            "Business income may be irregular; ensure cash flow can support "
            "instalments. Default affects personal and business credit records.",
        ]),
    ],
)

DOCS["Cash_Line-i"] = pds(
    "Cash Line-i",
    "A revolving Islamic overdraft facility based on Tawarruq.",
    [
        ("Product Overview", [
            "Cash Line-i is a revolving financing facility that gives you "
            "standby access to funds. You only pay profit on the amount "
            "utilised, making it useful for short-term cash flow needs.",
        ]),
        ("Key Product Features", [
            ("Facility limit", "RM3,000 up to RM100,000"),
            ("Profit rate", "7.50% per annum on utilised amount"),
            ("Tenure", "Revolving, subject to annual review"),
            ("Repayment", "Flexible; minimum monthly profit payment"),
        ]),
        ("Eligibility", [
            ("Age", "21 to 60 years old"),
            ("Minimum income", "RM3,000 per month"),
        ]),
        ("Fees and Charges", [
            ("Annual facility fee", "RM100 per annum"),
            ("Late payment charge", "1% per annum on overdue amount"),
        ]),
        ("Key Risks", [
            "Revolving facilities can lead to persistent debt if only minimum "
            "payments are made. Profit accrues daily on utilised balances.",
        ]),
    ],
)

DOCS["Credit_Bills_Financing-i"] = pds(
    "Credit Bills Financing-i",
    "Trade financing for businesses to manage receivables and payables.",
    [
        ("Product Overview", [
            "Credit Bills Financing-i (CBF-i) helps businesses finance the "
            "purchase or sale of goods by advancing funds against trade bills, "
            "under the concept of Bai' Dayn / Murabahah.",
        ]),
        ("Key Product Features", [
            ("Financing amount", "Based on invoice value, up to 90%"),
            ("Profit rate", "5.25% per annum"),
            ("Tenure", "Up to 180 days per bill"),
            ("Financing concept", "Murabahah / Bai' Dayn"),
        ]),
        ("Eligibility", [
            ("Business type", "Registered SME or corporate entity"),
            ("Trading history", "Minimum 1 year of trading"),
        ]),
        ("Fees and Charges", [
            ("Processing fee", "0.1% of bill amount"),
            ("Late payment charge", "1% per annum on overdue amount"),
        ]),
        ("Key Risks", [
            "Non-payment by your trade counterparty does not release you from "
            "your obligation to the Bank.",
        ]),
    ],
)

DOCS["Term_Deposit-i"] = pds(
    "Term Deposit-i",
    "A fixed-term Islamic deposit based on the concept of Tawarruq.",
    [
        ("Product Overview", [
            "Term Deposit-i lets you place funds for a fixed tenure to earn a "
            "competitive, pre-agreed profit rate under Tawarruq. Your capital "
            "and expected profit are known upfront.",
        ]),
        ("Key Product Features", [
            ("Minimum placement", "RM1,000"),
            ("Profit rate", "Up to 3.85% per annum for 12-month tenure"),
            ("Tenure options", "1, 3, 6, 12, 24, 36 months"),
            ("Profit payment", "At maturity, or monthly for tenures 12 months+"),
        ]),
        ("Eligibility", [
            ("Age", "18 years and above (or via guardian)"),
            ("Account", "Requires a Meridian Savings-i or Current Account-i"),
        ]),
        ("Fees and Charges", [
            ("Account opening", "No fee"),
            ("Premature withdrawal", "Profit may not be paid if withdrawn before maturity"),
        ]),
        ("Protection", [
            "Eligible for protection by the (fictional) Deposit Insurance "
            "scheme up to the prescribed limit per depositor.",
        ]),
    ],
)

DOCS["Savings-i_Account"] = pds(
    "Savings-i Account",
    "An everyday Islamic savings account based on the concept of Qard (benevolent loan).",
    [
        ("Product Overview", [
            "The Savings-i Account is a Shariah-compliant everyday account for "
            "your daily banking, with digital access via the Meridian mobile app "
            "and internet banking.",
        ]),
        ("Key Product Features", [
            ("Minimum opening balance", "RM20"),
            ("Profit rate", "0.25% per annum on daily balance"),
            ("Access", "Debit card, mobile app, internet banking, ATM, DuitNow QR"),
            ("Financing concept", "Qard"),
        ]),
        ("Eligibility", [
            ("Age", "Open to all ages (minors via guardian)"),
        ]),
        ("Fees and Charges", [
            ("Monthly service fee", "Nil"),
            ("Replacement debit card", "RM12 per card"),
            ("Below minimum balance", "No penalty"),
        ]),
        ("Protection", [
            "Eligible for protection by the (fictional) Deposit Insurance "
            "scheme up to the prescribed limit per depositor.",
        ]),
    ],
)

DOCS["Credit_Card-i"] = pds(
    "Credit Card-i",
    "A Shariah-compliant credit card based on the concept of Ujrah (fee-based).",
    [
        ("Product Overview", [
            "Credit Card-i offers cashless convenience with profit-free "
            "transactions when you pay within the grace period, under the "
            "Ujrah (service fee) concept.",
        ]),
        ("Key Product Features", [
            ("Credit limit", "From RM3,000, subject to eligibility"),
            ("Management fee", "Up to 15% per annum on outstanding balance"),
            ("Interest-free period", "Up to 20 days"),
            ("Cashback", "Up to 1% on groceries, fuel and dining"),
        ]),
        ("Eligibility", [
            ("Age", "21 years and above (principal)"),
            ("Minimum income", "RM24,000 per annum"),
        ]),
        ("Fees and Charges", [
            ("Annual fee", "RM0 (waived for first year)"),
            ("Late payment charge", "1% of outstanding, min RM10 max RM100"),
            ("Cash withdrawal fee", "5% of amount withdrawn"),
        ]),
        ("Key Risks", [
            "Paying only the minimum extends your debt and increases total "
            "charges. Overspending can lead to financial difficulty.",
        ]),
    ],
)

DOCS["Investment-i_Fund"] = pds(
    "Investment-i Fund",
    "A Shariah-compliant unit trust investment for wealth growth.",
    [
        ("Product Overview", [
            "Investment-i Fund invests in a diversified portfolio of "
            "Shariah-compliant equities and sukuk, managed by Meridian Asset "
            "Management, suitable for medium- to long-term wealth building.",
        ]),
        ("Key Product Features", [
            ("Minimum investment", "RM1,000 initial, RM100 subsequent"),
            ("Indicative return", "Historical 5-year average ~6% per annum (not guaranteed)"),
            ("Risk level", "Moderate"),
            ("Liquidity", "Redeem units on any business day"),
        ]),
        ("Eligibility", [
            ("Age", "18 years and above"),
            ("Suitability", "Subject to a risk profiling assessment"),
        ]),
        ("Fees and Charges", [
            ("Sales charge", "Up to 3% of investment amount"),
            ("Annual management fee", "1.5% per annum of NAV"),
        ]),
        ("Key Risks", [
            "Investment value can go down as well as up. Past performance does "
            "not guarantee future returns. Capital is not guaranteed.",
        ]),
    ],
)

DOCS["Takaful_Protection-i"] = pds(
    "Takaful Protection-i",
    "A Shariah-compliant protection plan based on the concept of Tabarru' (mutual donation).",
    [
        ("Product Overview", [
            "Takaful Protection-i provides family protection and savings under "
            "the Tabarru' concept, where participants contribute to a common "
            "fund for mutual assistance.",
        ]),
        ("Key Product Features", [
            ("Coverage", "Death and total permanent disability"),
            ("Contribution", "From RM100 per month"),
            ("Maturity benefit", "Accumulated savings portion returned at maturity"),
            ("Concept", "Tabarru' and Wakalah"),
        ]),
        ("Eligibility", [
            ("Entry age", "18 to 60 years old"),
            ("Coverage term", "10 to 30 years"),
        ]),
        ("Fees and Charges", [
            ("Wakalah fee", "Deducted from contribution as disclosed"),
        ]),
        ("Key Risks", [
            "Missing contributions may lapse your certificate and reduce "
            "coverage. Surrender in early years may yield little or no value.",
        ]),
    ],
)


def main():
    os.makedirs(OUT, exist_ok=True)
    total = 0
    for key, lines in DOCS.items():
        fname = f"Meridian_PDS_{key}.pdf"
        path = os.path.join(OUT, fname)
        n = write_pdf(path, lines)
        total += 1
        print(f"  wrote {fname:44s} {n} page(s)")
    print(f"Done. {total} PDS PDFs generated in {OUT}")


if __name__ == "__main__":
    main()
