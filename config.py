"""
GO DESi Consumer Insights — configuration (v2).

Central schema for the whole app:
  - Google Sheet sources + mappings store
  - logical fields (form question -> analysis field), per category
  - which fields are multi-select
  - per-section tab definitions with per-tab filter specs
  - FY (Apr-Mar) quarter helpers for the response-trend graph

Downstream modules (app, charts, normalize) read from here so a renamed form
question or a new tab is a one-line change.
"""

# =====================================================================
# 1. DATA SOURCES
# =====================================================================
SOURCES = {
    "Popz": {
        "sheet_id": "18kP9C59ZmZM5Y5MshR2d-ErGRVTEU2B-hDHiRP5Qg9U",
        "worksheet": "Form Responses 1",
    },
    "Meetha": {
        "sheet_id": "1EJw-7FZubcTgoLQmwyCcgGoV8-Ux-K5CgDcGsHoGgZw",
        "worksheet": "Form Responses 1",
    },
}

MAPPINGS_STORE = {
    "sheet_id": "1dJYftR7ZEG0J-6tX4STjM15QCo3zPKmlbgMca1c6xtM",
    "worksheet": "Mappings",
}

CACHE_TTL = 300  # seconds

# =====================================================================
# 2. LOGICAL SCHEMA
# =====================================================================
# field_key -> {label, q (loose header substring), multi, cat, ts?}
#   q     : most distinctive lowercased substring of the real column header
#   multi : comma-separated multi-select answer
#   cat   : "shared" | "popz" | "meetha"

FIELDS = {
    # ---- shared spine ----
    "timestamp":     {"label": "Timestamp",         "q": "timestamp",            "multi": False, "cat": "shared"},
    "customer_name": {"label": "Customer Name",      "q": "customer name",        "multi": False, "cat": "shared"},
    "age":           {"label": "Age",               "q": "age",                  "multi": False, "cat": "shared"},
    "gender":        {"label": "Gender",            "q": "gender",               "multi": False, "cat": "shared"},
    "heard_when":    {"label": "First heard when",  "q": "when did you first hear", "multi": False, "cat": "shared"},
    "discovery":     {"label": "Discovery channel", "q": "how did you first hear", "multi": False, "cat": "shared"},
    "sku":           {"label": "SKUs bought",       "q": "what sku",             "multi": True,  "cat": "shared"},
    "comments":      {"label": "Comments",          "q": "any other comments",   "multi": False, "cat": "shared"},

    # ---- Popz ----
    "popz_frequency":   {"label": "How often eats Popz",  "q": "how often do you eat desi popz", "multi": False, "cat": "popz"},
    "popz_moment":      {"label": "When eats Popz",       "q": "when do you usually eat desi popz", "multi": True, "cat": "popz"},
    "popz_perception":  {"label": "What are Desi Popz",   "q": "what are desi popz",             "multi": True,  "cat": "popz"},
    "popz_motivation":  {"label": "Why choose Popz",      "q": "why do you choose desi popz",    "multi": True,  "cat": "popz"},
    "sweets_linkage":   {"label": "Knows we make sweets", "q": "did you know we also make",      "multi": False, "cat": "popz"},

    # ---- Meetha ----
    "sweets_frequency": {"label": "How often eats Sweets", "q": "how often do you consume sweets", "multi": False, "cat": "meetha"},
    "sweets_moment":    {"label": "When eats Sweets",      "q": "when do you usually eat sweets",  "multi": True,  "cat": "meetha"},
    "brand_awareness":  {"label": "Top-of-mind brand",     "q": "which other packaged indian sweet brand", "multi": True, "cat": "meetha"},
    "top3_recall":      {"label": "Spontaneous recall",    "q": "top 3 packaged indian sweet brands", "multi": True, "cat": "meetha"},
    "brand_preference": {"label": "Preferred brand",       "q": "which packaged sweets brand do you prefer", "multi": False, "cat": "meetha"},
    "sweet_format":     {"label": "Favourite format",      "q": "which sweet format",             "multi": True,  "cat": "meetha"},
}

# =====================================================================
# 3. TAB DEFINITIONS
# =====================================================================
# Each tab: dict(title, kind, filters=[...], + kind-specific keys)
#   filters: any of "age", "gender", "sku", "discovery", "preferred_brand"
#   kind: overview | audience | bars | perception | crosssell | headtohead |
#         competitive | format_brand | comments
# "bars" tabs render one or more fields as labelled bars; give `fields`.

POPZ_TABS = [
    {"title": "Overview",     "kind": "overview",  "filters": []},
    {"title": "Audience",     "kind": "audience",  "filters": []},
    {"title": "Acquisition",  "kind": "bars",      "filters": ["age", "gender"],
     "fields": ["discovery", "heard_when"]},
    {"title": "Behavior",     "kind": "bars",      "filters": ["age", "gender", "sku"],
     "fields": ["sku", "popz_frequency", "popz_moment"]},
    {"title": "Perception",   "kind": "bars",      "filters": ["age", "gender"],
     "fields": ["popz_perception"]},
    {"title": "Motivation",   "kind": "bars",      "filters": ["age", "gender", "sku"],
     "fields": ["popz_motivation"]},
    {"title": "Cross-sell",   "kind": "crosssell", "filters": ["age", "gender", "discovery"]},
    {"title": "Comments",     "kind": "comments",  "filters": []},
]

MEETHA_TABS = [
    {"title": "Overview",             "kind": "overview",     "filters": []},
    {"title": "Audience",             "kind": "audience",     "filters": []},
    {"title": "Acquisition",          "kind": "bars",         "filters": ["age", "gender"],
     "fields": ["discovery", "heard_when"]},
    {"title": "Behavior",             "kind": "bars",         "filters": ["age", "gender", "sku"],
     "fields": ["sku", "sweets_frequency", "sweets_moment"]},
    {"title": "Competitive standing", "kind": "competitive",  "filters": ["age", "gender"]},
    {"title": "Head-to-head",         "kind": "headtohead",   "filters": ["age", "gender"]},
    {"title": "Format & brand",       "kind": "format_brand", "filters": ["age", "gender", "preferred_brand"]},
    {"title": "Comments",             "kind": "comments",     "filters": []},
]

COMBINED_TABS = [
    {"title": "Overview",    "kind": "overview",  "filters": []},
    {"title": "Audience",    "kind": "audience",  "filters": []},
    {"title": "Acquisition", "kind": "bars",      "filters": ["age", "gender"],
     "fields": ["discovery", "heard_when"]},
    {"title": "Behavior",    "kind": "bars",      "filters": ["age", "gender"],
     "fields": ["frequency_combined", "moment_combined"]},  # resolved per-form in app
    {"title": "Comments",    "kind": "comments",  "filters": []},
]

def tabs_for(section: str):
    return {"Popz": POPZ_TABS, "Meetha": MEETHA_TABS, "Combined": COMBINED_TABS}[section]

# =====================================================================
# 4. FINANCIAL-YEAR QUARTERS (Apr-Mar)
# =====================================================================
def fy_quarter(ts):
    """Return (fy_label, quarter_label) for a timestamp. FY runs Apr-Mar.
    e.g. 2025-11 -> ('FY26', 'Q3')  (Apr25-Mar26 = FY26); 2026-05 -> ('FY27','Q1')."""
    import pandas as pd
    if pd.isna(ts):
        return (None, None)
    y, mth = ts.year, ts.month
    if mth >= 4:               # Apr-Dec -> FY = next calendar year
        fy = y + 1
        q = (mth - 4) // 3 + 1
    else:                      # Jan-Mar -> FY = this calendar year, Q4
        fy = y
        q = 4
    return (f"FY{str(fy)[2:]}", f"Q{q}")

def fy_quarter_label(ts):
    fy, q = fy_quarter(ts)
    return f"{fy} {q}" if fy else None

# Brand colours
HERO = "#F28C28"
GREY = "#9CA3AF"
PALETTE = ["#F59E0B", "#22D3EE", "#8B5CF6", "#34D399", "#F472B6", "#FB923C"]

# Minimum base below which a chart/metric is flagged directional
MIN_BASE = 30
