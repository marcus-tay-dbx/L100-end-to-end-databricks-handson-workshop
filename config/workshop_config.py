"""
Workshop configuration — the ONE place to rebrand this asset per customer.

Change ACTIVE_BANK to switch the workshop's branding and RAG document set.
Available profiles live in config/profiles/:
    "bank_rakyat"  -> real Bank Rakyat PDS PDFs   (current workshop)
    "meridian"     -> synthetic generic PDFs      (reusable default)

Everything else in the repo — the CSV data, the notebooks, the lab guide
structure — is brand-neutral and does not change between customers.
"""

# ⬇️  CHANGE THIS ONE LINE TO REBRAND THE WORKSHOP FOR A NEW CUSTOMER
ACTIVE_BANK = "bank_rakyat"


def get_profile(active_bank: str = None) -> dict:
    """Return the active branding profile dict.

    Imported by the 00-setup notebook. Falls back to 'meridian' if the named
    profile module is missing, so the workshop never hard-fails on a typo.
    """
    import importlib

    name = active_bank or ACTIVE_BANK
    try:
        mod = importlib.import_module(f"profiles.{name}")
    except ModuleNotFoundError:
        try:
            # when imported as a package: config.profiles.<name>
            mod = importlib.import_module(f"config.profiles.{name}")
        except ModuleNotFoundError:
            mod = importlib.import_module("profiles.meridian")
    return mod.PROFILE


if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
    p = get_profile()
    print("Active profile:")
    for k, v in p.items():
        print(f"  {k:16s} = {v}")
