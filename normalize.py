"""
Normalization engine for GO DESi Consumer Insights.

Three-layer resolver applied per field, in order:
  1. canonical  — value is already a clean label -> keep as-is
  2. alias      — seeded + learned {raw: canonical} lookup
  3. unmapped   — anything left over is tagged UNMAPPED (never silently dropped)

Multi-select answers ("A, B") are split into tokens and each token resolved
independently, so one respondent can contribute to several categories.

`learned` is the live dict pulled from the Mappings Google Sheet, layered ON TOP
of the seed aliases at call time. That's what makes approvals in the Review tab
take effect without code changes.
"""

import re
import pandas as pd

import seeds
from config import FIELDS

UNMAPPED = "\u26a0 Unmapped"   # ⚠ Unmapped


def _clean(x):
    if pd.isna(x):
        return ""
    return re.sub(r"\s+", " ", str(x)).strip()


def _resolve_token(field, raw, learned):
    """Resolve a single already-split token to a canonical label or UNMAPPED."""
    low = _clean(raw).lower()
    if low == "" or low == "nan":
        return None  # empty -> contributes nothing

    canon = seeds.CANONICAL.get(field, [])
    canon_low = {c.lower(): c for c in canon}

    # Layer 1: already canonical
    if low in canon_low:
        return canon_low[low]

    # Layer 2a: learned aliases (from Mappings sheet) — highest priority alias
    learned_field = learned.get(field, {})
    if low in learned_field:
        return learned_field[low]

    # Layer 2b: seed aliases
    seed_field = seeds.ALIASES.get(field, {})
    if low in seed_field:
        return seed_field[low]

    # Field-specific keyword fallbacks
    if field == "sku":
        for kw, fam in seeds.SKU_KEYWORDS:
            if kw in low:
                return fam
    if field in ("brand_awareness", "top3_recall", "brand_preference"):
        for kw in seeds.LOCAL_BRAND_KEYWORDS:
            if kw in low:
                return "Local / unbranded"

    # Layer 3: unmapped
    return UNMAPPED


def _split_multi(cleaned):
    """Split a multi-select answer on commas, but NOT commas inside parentheses.
    e.g. 'While watching content(Netflix, tv), After meals' -> 2 tokens, not 4."""
    tokens, depth, buf = [], 0, []
    for ch in cleaned:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            tokens.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    tokens.append("".join(buf))
    return [t.strip() for t in tokens if t.strip()]


def resolve_field(series, field, learned):
    """
    Resolve a raw column into a long-form DataFrame of (index, value) where
    multi-selects are exploded. Returns a Series aligned to exploded index.
    """
    multi = FIELDS[field]["multi"]
    out_idx, out_val, out_raw = [], [], []

    for idx, cell in series.items():
        cleaned = _clean(cell)
        if cleaned == "":
            continue
        tokens = _split_multi(cleaned) if multi else [cleaned]
        for tok in tokens:
            if tok == "":
                continue
            resolved = _resolve_token(field, tok, learned)
            if resolved is None:
                continue
            out_idx.append(idx)
            out_val.append(resolved)
            out_raw.append(tok)

    return pd.DataFrame({"row": out_idx, "value": out_val, "raw": out_raw})


def find_column(df, field):
    """Loosely match the sheet header for a logical field (lowercased substring)."""
    q = FIELDS[field]["q"].lower()
    for c in df.columns:
        if q in str(c).strip().lower():
            return c
    return None


def unmapped_report(df, field, learned):
    """Return a DataFrame of raw values that resolve to UNMAPPED, with counts."""
    col = find_column(df, field)
    if col is None:
        return pd.DataFrame(columns=["raw", "count"])
    long = resolve_field(df[col], field, learned)
    um = long[long["value"] == UNMAPPED]
    if um.empty:
        return pd.DataFrame(columns=["raw", "count"])
    return (
        um.groupby("raw").size().reset_index(name="count")
        .sort_values("count", ascending=False).reset_index(drop=True)
    )


def normalize_demographics(df, learned):
    """Age + gender resolved onto the raw frame, plus a parsed 'ts' timestamp."""
    out = df.copy()
    for f in ("age", "gender"):
        col = find_column(df, f)
        if col is None:
            out[f + "_norm"] = seeds.DROP
            continue
        out[f + "_norm"] = df[col].map(
            lambda v: (_resolve_token(f, v, learned) or seeds.DROP)
        )
    ts_col = find_column(df, "timestamp")
    out["ts"] = pd.to_datetime(df[ts_col], errors="coerce") if ts_col else pd.NaT
    return out
