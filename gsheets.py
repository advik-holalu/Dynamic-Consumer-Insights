"""
Google Sheets I/O for GO DESi Consumer Insights.

Reads:
  - form response sheets (one per category)
  - the Mappings sheet (learned raw->canonical), returned as a nested dict

Writes:
  - approved mappings appended to the Mappings sheet

Auth: a Google Cloud service account. Credentials live in st.secrets under
[gcp_service_account] (see .streamlit/secrets.toml.example). The two form sheets
and the Mappings sheet must each be shared with the service account's email
(client_email) as at least Viewer (forms) / Editor (mappings).

All reads are cached with a TTL so interactions don't re-hit the API on every
click; a manual refresh clears the cache.
"""

import datetime as dt
import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

from config import SOURCES, MAPPINGS_STORE, CACHE_TTL

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]


@st.cache_resource
def _client():
    """Authorized gspread client (cached for the session)."""
    info = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    return gspread.authorize(creds)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_responses(category: str) -> pd.DataFrame:
    """Load one category's form-response sheet as a DataFrame."""
    src = SOURCES[category]
    ws = _client().open_by_key(src["sheet_id"]).worksheet(src["worksheet"])
    records = ws.get_all_records()  # first row = headers
    return pd.DataFrame(records)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def load_mappings() -> dict:
    """
    Load learned mappings as {field: {raw_lower: canonical}}.
    Mappings sheet columns: field | raw_value | canonical | updated_at
    """
    store = MAPPINGS_STORE
    ws = _client().open_by_key(store["sheet_id"]).worksheet(store["worksheet"])
    rows = ws.get_all_records()
    learned = {}
    for r in rows:
        field = str(r.get("field", "")).strip()
        raw = str(r.get("raw_value", "")).strip().lower()
        canon = str(r.get("canonical", "")).strip()
        if field and raw and canon:
            learned.setdefault(field, {})[raw] = canon
    return learned


def append_mappings(entries: list[dict]):
    """
    Append approved mappings to the Mappings sheet.
    entries: [{field, raw_value, canonical}, ...]
    Clears caches so the next read reflects the change.
    """
    if not entries:
        return
    store = MAPPINGS_STORE
    ws = _client().open_by_key(store["sheet_id"]).worksheet(store["worksheet"])
    now = dt.datetime.now().isoformat(timespec="seconds")
    rows = [[e["field"], e["raw_value"], e["canonical"], now] for e in entries]
    ws.append_rows(rows, value_input_option="USER_ENTERED")
    load_mappings.clear()
    load_responses.clear()


def ensure_mappings_header():
    """Write the header row if the Mappings sheet is empty. Call once on setup."""
    store = MAPPINGS_STORE
    ws = _client().open_by_key(store["sheet_id"]).worksheet(store["worksheet"])
    if not ws.get_all_values():
        ws.append_row(["field", "raw_value", "canonical", "updated_at"])


def refresh_all():
    """Clear all cached reads (used by the Refresh button)."""
    load_responses.clear()
    load_mappings.clear()
