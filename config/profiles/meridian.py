"""
Workshop branding profile: Meridian Bank (generic, fictional).

This is the reusable default for any FSI customer. It uses the synthetic
Meridian PDS PDFs (also generated in this repo) so nothing is customer-specific
and the asset can be demoed to any prospect without rebranding data.

To reuse this repo for a new customer:
  1. Copy this file to config/profiles/<customer>.py and edit the labels.
  2. Drop the customer's PDS PDFs into data/pds_documents/<customer>/.
  3. Set ACTIVE_BANK = "<customer>" in config/workshop_config.py.
"""

PROFILE = {
    "profile_key": "meridian",
    "bank_name": "Meridian Bank",
    "bank_short": "Meridian",
    "careline": "1-300-00-0000",
    "pds_folder": "meridian",             # -> data/pds_documents/meridian/
    "currency": "MYR",
    "currency_symbol": "RM",
    "tagline": "a fictional retail & Islamic bank (demo profile)",
    "workshop_title": "End-to-End Databricks Hands-On Workshop",
}
