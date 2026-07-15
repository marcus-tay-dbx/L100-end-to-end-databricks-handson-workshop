"""
Workshop branding profile: Bank Rakyat.

Uses the REAL Bank Rakyat Product Disclosure Sheets (public PDFs) as the RAG
corpus so the Knowledge Assistant module is maximally contextual for a
Bank Rakyat audience.

The structured CSV data (customers/accounts/transactions/products/branches)
is brand-neutral and shared across all profiles — only the labels below and
the PDS folder change per customer.
"""

PROFILE = {
    "profile_key": "bank_rakyat",
    "bank_name": "Bank Rakyat",
    "bank_short": "BKRM",
    "careline": "1-300-80-5454",
    "pds_folder": "bank_rakyat",          # -> data/pds_documents/bank_rakyat/
    "currency": "MYR",
    "currency_symbol": "RM",
    # Text shown in the setup summary / lab guide intro
    "tagline": "Malaysia's cooperative Islamic bank",
    "workshop_title": "Bank Rakyat — End-to-End Databricks Hands-On Workshop",
}
