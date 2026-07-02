"""
Analysis helpers for GO DESi Consumer Insights.

Every function here is BASE-AWARE: it returns both the numbers to chart and the
denominator (n answered) so the UI can print "of N answered" everywhere. None of
these draw anything — app.py handles rendering with charts.py.

Conventions (locked with the user):
  - percentages are % of respondents who ANSWERED that question
  - multi-selects: a respondent counts once per distinct value they gave
  - the DROP sink ("Not answered") and "Unmapped" are excluded from chart bodies
    but the base n reflects everyone who gave a usable answer
"""

import pandas as pd

import normalize as nm
from normalize import UNMAPPED
import seeds
from config import FIELDS, MIN_BASE


# ---------------------------------------------------------------------
# filtering
# ---------------------------------------------------------------------
def apply_row_filters(df, age_sel, gen_sel):
    """Return the subset of df matching age/gender selections ('All' = no filter)."""
    out = df
    if age_sel and age_sel != "All" and "age_norm" in out:
        out = out[out["age_norm"] == age_sel]
    if gen_sel and gen_sel != "All" and "gender_norm" in out:
        out = out[out["gender_norm"] == gen_sel]
    return out


def resolve_long(df, field, learned, keep_rows=None):
    """Resolve a field to long form (row, value, raw), optionally limited to keep_rows."""
    col = nm.find_column(df, field)
    if col is None:
        return pd.DataFrame(columns=["row", "value", "raw"])
    long = nm.resolve_field(df[col], field, learned)
    if keep_rows is not None:
        long = long[long["row"].isin(keep_rows)]
    return long


# ---------------------------------------------------------------------
# core: counts + base for a single field
# ---------------------------------------------------------------------
def field_distribution(df, field, learned, keep_rows=None, drop_unmapped=True):
    """
    Return (counts_df, base_n) for a field.
      counts_df: columns [value, count, pct]  (pct = % of base_n)
      base_n:    distinct respondents who gave a usable answer
    """
    long = resolve_long(df, field, learned, keep_rows)
    if long.empty:
        return pd.DataFrame(columns=["value", "count", "pct"]), 0

    usable = long[long["value"] != seeds.DROP]
    if drop_unmapped:
        usable = usable[usable["value"] != UNMAPPED]

    base_n = long[long["value"] != seeds.DROP]["row"].nunique()
    if base_n == 0:
        return pd.DataFrame(columns=["value", "count", "pct"]), 0

    counts = (usable.groupby("value")["row"].nunique()
              .reset_index(name="count").sort_values("count", ascending=False))
    counts["pct"] = (counts["count"] / base_n * 100).round(1)
    return counts.reset_index(drop=True), base_n


def top_value(df, field, learned):
    counts, base = field_distribution(df, field, learned)
    if counts.empty:
        return None, 0, base
    r = counts.iloc[0]
    return r["value"], r["pct"], base


# ---------------------------------------------------------------------
# cross-sell (Popz): "did you know we make sweets"
# ---------------------------------------------------------------------
def crosssell(df, learned, keep_rows=None):
    """Return dict with yes/no counts, gap_pct (=% No), base."""
    long = resolve_long(df, "sweets_linkage", learned, keep_rows)
    long = long[long["value"].isin(["Yes", "No"])]
    yes = long[long["value"] == "Yes"]["row"].nunique()
    no = long[long["value"] == "No"]["row"].nunique()
    base = yes + no
    gap = round(no / base * 100, 1) if base else 0
    return {"yes": yes, "no": no, "base": base, "gap_pct": gap}


# ---------------------------------------------------------------------
# competitive (Meetha): brand across awareness / recall / preference
# ---------------------------------------------------------------------
BRAND_FIELDS = [("brand_awareness", "Awareness"),
                ("top3_recall", "Recall"),
                ("brand_preference", "Preference")]


def brand_stage_table(df, learned, keep_rows=None, top_n=8, always=("GO DESi",)):
    """
    Return (stage_pct: dict{stage: {brand: pct}}, bases: dict{stage: n}, brands: list).
    Brands = top_n by awareness, plus any in `always`.
    """
    stage_counts, bases = {}, {}
    for field, stage in BRAND_FIELDS:
        counts, base = field_distribution(df, field, learned, keep_rows)
        bases[stage] = base
        stage_counts[stage] = dict(zip(counts["value"], counts["count"]))

    # rank brands by awareness count
    aware = stage_counts.get("Awareness", {})
    ranked = sorted(aware, key=aware.get, reverse=True)
    brands = ranked[:top_n]
    for b in always:
        if b not in brands and (b in aware or any(b in stage_counts[s] for _, s in BRAND_FIELDS)):
            brands.append(b)

    stage_pct = {}
    for _, stage in BRAND_FIELDS:
        base = bases[stage] or 1
        stage_pct[stage] = {b: round(stage_counts[stage].get(b, 0) / base * 100, 1)
                            for b in brands}
    return stage_pct, bases, brands


def conversion_ratio(df, learned, brand, keep_rows=None):
    """preference% / awareness% for a brand. Returns (ratio, pref_pct, aware_pct)."""
    aw, aw_base = field_distribution(df, "brand_awareness", learned, keep_rows)
    pf, pf_base = field_distribution(df, "brand_preference", learned, keep_rows)
    aw_pct = float(aw.loc[aw["value"] == brand, "pct"].sum())
    pf_pct = float(pf.loc[pf["value"] == brand, "pct"].sum())
    ratio = round(pf_pct / aw_pct, 2) if aw_pct else None
    return ratio, pf_pct, aw_pct


# ---------------------------------------------------------------------
# head-to-head (Meetha): GO DESi vs a competitor among people aware of both
# ---------------------------------------------------------------------
def head_to_head(df, learned, competitor, keep_rows=None, brand="GO DESi"):
    """
    Among respondents who had BOTH `brand` and `competitor` in mind (named either
    in awareness OR spontaneous recall), who do they prefer?
    Returns dict with win/lose/other counts + base (= considered-both size).
    Using awareness-OR-recall as the consideration set — unaided awareness alone
    is too sparse to yield a usable base.
    """
    aware = resolve_long(df, "brand_awareness", learned, keep_rows)
    recall = resolve_long(df, "top3_recall", learned, keep_rows)
    consid = pd.concat([aware, recall], ignore_index=True)
    pref = resolve_long(df, "brand_preference", learned, keep_rows)

    rows_brand = set(consid[consid["value"] == brand]["row"])
    rows_comp = set(consid[consid["value"] == competitor]["row"])
    both = rows_brand & rows_comp

    pref_by_row = pref[pref["row"].isin(both)].set_index("row")["value"].to_dict()
    win = sum(1 for r in both if pref_by_row.get(r) == brand)
    lose = sum(1 for r in both if pref_by_row.get(r) == competitor)
    other = len(both) - win - lose
    base = len(both)
    win_rate = round(win / base * 100, 1) if base else 0
    return {"win": win, "lose": lose, "other": other, "base": base,
            "win_rate": win_rate, "brand": brand, "competitor": competitor}


def share_of_mind(df, learned, keep_rows=None, top_n=10):
    """Combined awareness+recall mention share per brand. Returns counts_df, base."""
    aw = resolve_long(df, "brand_awareness", learned, keep_rows)
    rc = resolve_long(df, "top3_recall", learned, keep_rows)
    both = pd.concat([aw, rc], ignore_index=True)
    both = both[~both["value"].isin([seeds.DROP, UNMAPPED])]
    base = pd.concat([aw, rc])["row"].nunique()
    counts = (both.groupby("value")["row"].nunique()
              .reset_index(name="count").sort_values("count", ascending=False).head(top_n))
    counts["pct"] = (counts["count"] / base * 100).round(1) if base else 0
    return counts.reset_index(drop=True), base


# ---------------------------------------------------------------------
# format x brand (Meetha): format preference filtered by preferred brand
# ---------------------------------------------------------------------
def format_by_brand(df, learned, preferred_brand, keep_rows=None):
    """Format distribution among people who prefer `preferred_brand` ('All' = everyone)."""
    if preferred_brand and preferred_brand != "All":
        pref = resolve_long(df, "brand_preference", learned, keep_rows)
        rows = set(pref[pref["value"] == preferred_brand]["row"])
        kr = rows if keep_rows is None else (rows & set(keep_rows))
    else:
        kr = keep_rows
    return field_distribution(df, "sweet_format", learned, kr)


# ---------------------------------------------------------------------
# response trend (Overview): counts per FY-quarter week
# ---------------------------------------------------------------------
def response_trend(df, quarter_label=None):
    """
    Weekly response counts. df must have a parsed 'ts' column.
    If quarter_label given (e.g. 'FY26 Q3'), limit to that FY-quarter.
    Returns (week_labels, counts).
    """
    from config import fy_quarter_label
    d = df.dropna(subset=["ts"]).copy()
    if quarter_label:
        d = d[d["ts"].map(fy_quarter_label) == quarter_label]
    if d.empty:
        return [], []
    d["week"] = d["ts"].dt.to_period("W").apply(lambda p: p.start_time.strftime("%d %b"))
    g = d.groupby("week").size()
    # sort by actual date not string
    order = d.groupby("week")["ts"].min().sort_values().index
    g = g.reindex(order)
    return list(g.index), list(g.values.astype(int))


def available_quarters(df):
    """Sorted list of FY-quarter labels present in df['ts']."""
    from config import fy_quarter_label, fy_quarter
    d = df.dropna(subset=["ts"])
    labs = d["ts"].map(lambda t: (fy_quarter(t), fy_quarter_label(t))).tolist()
    uniq = {lbl: key for key, lbl in labs if lbl}
    # sort by (fy, q)
    return [lbl for lbl, key in sorted(uniq.items(), key=lambda kv: kv[1])]


def directional(base):
    """True if a base is below the directional threshold."""
    return 0 < base < MIN_BASE
