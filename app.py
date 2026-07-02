"""
GO DESi — Consumer Insights Dashboard (v2).

Run:  streamlit run app.py

Navigation lives in the sidebar:
  - three section buttons (Popz / Meetha / Combined) at the top
  - two coloured action buttons (Normalize data, Refresh data) at the bottom
Normalize opens an in-app page (not a tab) with its own Popz/Meetha/Combined
category filter for focused tagging.

Data flows live from two Google Forms -> Sheets -> here (cached). Normalization
is the 3-layer resolver in normalize.py; approvals persist to the Mappings sheet.
"""

import pandas as pd
import streamlit as st
from streamlit_echarts import st_echarts

import config
import gsheets
import normalize as nm
from normalize import UNMAPPED
import seeds
import analysis as an
import charts

st.set_page_config(page_title="GO DESi — Consumer Insights", layout="wide")

# ---------------------------------------------------------------------
# session state: routing
# ---------------------------------------------------------------------
if "page" not in st.session_state:
    st.session_state.page = "dashboard"       # "dashboard" | "normalize"
if "section" not in st.session_state:
    st.session_state.section = "Popz"          # Popz | Meetha | Combined


def render_chart(option, height="360px", key=None):
    st_echarts(options=option, height=height, key=key, theme=None)


# ---------------------------------------------------------------------
# load data (cached)
# ---------------------------------------------------------------------
try:
    learned = gsheets.load_mappings()
except Exception as e:  # noqa: BLE001
    st.error("Couldn't read the Mappings sheet. Check config sheet IDs and sharing.\n\n"
             + str(e))
    st.stop()

_lv = sum(len(v) for v in learned.values())


@st.cache_data(ttl=config.CACHE_TTL, show_spinner="Loading responses…")
def _prep(section, _v):
    raw = gsheets.load_responses(section)
    return nm.normalize_demographics(raw, learned)


data = {}
for sec in ("Popz", "Meetha"):
    try:
        data[sec] = _prep(sec, _lv)
    except Exception as e:  # noqa: BLE001
        st.warning(f"Couldn't load {sec}: {e}")
        data[sec] = pd.DataFrame()


# ---------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------
with st.sidebar:
    st.markdown("### GO DESi")
    st.caption("Consumer Insights")
    st.write("")

    for sec in ("Popz", "Meetha", "Combined"):
        is_active = (st.session_state.section == sec and st.session_state.page == "dashboard")
        if st.button(sec, use_container_width=True,
                     type=("primary" if is_active else "secondary"),
                     key=f"nav_{sec}"):
            st.session_state.section = sec
            st.session_state.page = "dashboard"
            st.rerun()

    # spacer pushes action buttons down
    st.markdown("<div style='height:40vh'></div>", unsafe_allow_html=True)

    # coloured action buttons (both primary = same accent, distinct from nav)
    if st.button("🏷  Normalize data", use_container_width=True, type="primary",
                 key="go_normalize"):
        st.session_state.page = "normalize"
        st.rerun()
    if st.button("↻  Refresh data", use_container_width=True, type="primary",
                 key="do_refresh"):
        gsheets.refresh_all()
        st.cache_data.clear()
        st.rerun()


# ---------------------------------------------------------------------
# small UI helpers
# ---------------------------------------------------------------------
def metric_card(col, label, value, base_n, note=None):
    """Uniform metric card with an 'of N answered' base line."""
    with col:
        with st.container(border=True):
            st.caption(label)
            st.markdown(f"### {value}")
            st.caption(f"of {base_n} answered" if note is None else note)


def bars_for_field(df, field, learned, keep_rows, value_is_pct=True):
    counts, base = an.field_distribution(df, field, learned, keep_rows)
    lbl = config.FIELDS[field]["label"]
    multi = config.FIELDS[field]["multi"]
    with st.container(border=True):
        st.markdown(f"**{lbl}**")
        if counts.empty:
            st.info(f"No answers for “{lbl}”.")
            return
        cap = f"Base: {base} answered"
        if multi:
            cap += " · multi-select, totals exceed 100%"
        if an.directional(base):
            cap += " · ⚠ directional (small base)"
        st.caption(cap)
        opt = charts.hbar(counts["value"], counts["pct"], value_is_pct=True)
        render_chart(opt, height=f"{max(200, 34*len(counts))}px", key=f"bar_{field}_{id(keep_rows)}")


def tab_filters(df, spec, section):
    """Render the per-tab filters declared in the tab spec; return selections dict."""
    sels = {"age": "All", "gender": "All", "sku": "All",
            "discovery": "All", "preferred_brand": "All"}
    active = spec.get("filters", [])
    if not active:
        return sels
    cols = st.columns(len(active))
    for c, f in zip(cols, active):
        with c:
            if f == "age":
                opts = ["All"] + [a for a in seeds.CANONICAL["age"] if a != seeds.DROP]
                sels["age"] = st.selectbox("Age", opts, key=f"flt_age_{spec['title']}_{section}")
            elif f == "gender":
                opts = ["All"] + [g for g in seeds.CANONICAL["gender"] if g != seeds.DROP]
                sels["gender"] = st.selectbox("Gender", opts, key=f"flt_gen_{spec['title']}_{section}")
            elif f == "sku":
                opts = ["All"] + [s for s in seeds.CANONICAL["sku"] if s != seeds.DROP]
                sels["sku"] = st.selectbox("SKU family", opts, key=f"flt_sku_{spec['title']}_{section}")
            elif f == "discovery":
                opts = ["All"] + [d for d in seeds.CANONICAL["discovery"] if d != seeds.DROP]
                sels["discovery"] = st.selectbox("Discovery", opts, key=f"flt_disc_{spec['title']}_{section}")
            elif f == "preferred_brand":
                opts = ["All"] + [b for b in seeds.CANONICAL["brand_preference"] if b != seeds.DROP]
                sels["preferred_brand"] = st.selectbox("Preferred brand", opts, key=f"flt_pref_{spec['title']}_{section}")
    return sels


def rows_after_filters(df, sels, learned):
    """Row index set after age/gender + optional sku/discovery filters."""
    sub = an.apply_row_filters(df, sels["age"], sels["gender"])
    keep = set(sub.index)
    # sku / discovery narrow by membership in that field
    for fld, key in (("sku", "sku"), ("discovery", "discovery")):
        if sels.get(key) and sels[key] != "All":
            long = an.resolve_long(df, fld, learned)
            keep &= set(long[long["value"] == sels[key]]["row"])
    return keep


# ---------------------------------------------------------------------
# TAB RENDERERS
# ---------------------------------------------------------------------
def render_audience(df, keep_rows):
    c1, c2 = st.columns(2)
    for col, field, title in ((c1, "age", "Age"), (c2, "gender", "Gender")):
        with col:
            with st.container(border=True):
                counts, base = an.field_distribution(df, field, learned, keep_rows)
                st.markdown(f"**{title}**")
                st.caption(f"Base: {base} answered")
                if not counts.empty:
                    opt = charts.hbar(counts["value"], counts["pct"], value_is_pct=True)
                    render_chart(opt, height=f"{max(180, 34*len(counts))}px", key=f"aud_{field}")


def render_overview(section, df_or_frames):
    st.subheader(f"{section} — Overview")

    if section == "Combined":
        frames = df_or_frames
        total = sum(len(f) for f in frames)
        c = st.columns(3)
        metric_card(c[0], "Total responses", total, total, note="Popz + Meetha")
        metric_card(c[1], "Popz responses", len(data["Popz"]), len(data["Popz"]), note="calls logged")
        metric_card(c[2], "Meetha responses", len(data["Meetha"]), len(data["Meetha"]), note="calls logged")
    else:
        df = df_or_frames
        c = st.columns(4)
        metric_card(c[0], "Respondents", len(df), len(df), note="calls logged")
        # top age
        av, ap, ab = an.top_value(df, "age", learned)
        metric_card(c[1], "Top age group", av or "—", ab)
        if section == "Popz":
            cs = an.crosssell(df, learned)
            metric_card(c[2], "Don't know we make sweets", f"{cs['gap_pct']}%", cs["base"])
            pv, pp, pb = an.top_value(df, "popz_perception", learned)
            metric_card(c[3], "Top perception", f"{pv} ({pp}%)" if pv else "—", pb)
        else:
            bv, bp, bb = an.top_value(df, "brand_preference", learned)
            metric_card(c[2], "Top preferred brand", f"{bv} ({bp}%)" if bv else "—", bb)
            fv, fp, fb = an.top_value(df, "sweet_format", learned)
            metric_card(c[3], "Top format", f"{fv} ({fp}%)" if fv else "—", fb)

    # ---- WoW response trend with FY-quarter filter ----
    st.write("")
    st.markdown("**Weekly response trend**")
    if section == "Combined":
        all_ts = pd.concat([data["Popz"], data["Meetha"]], ignore_index=True)
    else:
        all_ts = df_or_frames if section == "Combined" else df
    quarters = an.available_quarters(all_ts if section != "Combined" else
                                     pd.concat([data["Popz"], data["Meetha"]], ignore_index=True))
    qsel = st.selectbox("Financial-year quarter (Apr–Mar)", ["All"] + quarters, key=f"q_{section}")
    ql = None if qsel == "All" else qsel

    if section == "Combined":
        xp, yp = an.response_trend(data["Popz"], ql)
        xm, ym = an.response_trend(data["Meetha"], ql)
        # align on union of weeks
        weeks = list(dict.fromkeys(xp + xm))
        pmap = dict(zip(xp, yp)); mmap = dict(zip(xm, ym))
        series = {"Popz": [pmap.get(w, 0) for w in weeks],
                  "Meetha": [mmap.get(w, 0) for w in weeks]}
        if weeks:
            with st.container(border=True):
                render_chart(charts.line_trend(weeks, series), height="300px", key="trend_comb")
        else:
            st.info("No responses in this quarter.")
    else:
        x, y = an.response_trend(df, ql)
        if x:
            with st.container(border=True):
                render_chart(charts.line_trend(x, {section: y}), height="300px", key=f"trend_{section}")
        else:
            st.info("No responses in this quarter.")


def render_crosssell(df, keep_rows):
    cs = an.crosssell(df, learned, keep_rows)
    st.subheader("Cross-sell — do Popz buyers know we make sweets?")
    c = st.columns(3)
    metric_card(c[0], "Know we make sweets", f"{100-cs['gap_pct']}%", cs["base"])
    metric_card(c[1], "Don't know", f"{cs['gap_pct']}%", cs["base"])
    metric_card(c[2], "Cross-sell opportunity", cs["no"], cs["base"], note="buyers to convert")
    if cs["base"]:
        with st.container(border=True):
            opt = charts.donut(["Know", "Don't know"], [cs["yes"], cs["no"]])
            render_chart(opt, height="320px", key="cs_donut")


def render_competitive(df, keep_rows):
    st.subheader("Competitive standing")
    st.caption("Three separate questions — read as strength at each stage, not literal drop-off.")
    stage_pct, bases, brands = an.brand_stage_table(df, learned, keep_rows)
    with st.container(border=True):
        st.caption(f"Bases — Awareness: {bases['Awareness']}, Recall: {bases['Recall']}, "
                   f"Preference: {bases['Preference']} answered")
        series = {stage: [stage_pct[stage][b] for b in brands] for stage in stage_pct}
        colors = [config.PALETTE[1], config.PALETTE[2], config.HERO]
        render_chart(charts.grouped_hbar(brands, series, colors=colors),
                     height=f"{max(260, 46*len(brands))}px", key="comp_grouped")

    # awareness paradox callout for GO DESi
    ratio, pf, aw = an.conversion_ratio(df, learned, "GO DESi", keep_rows)
    if ratio is not None:
        st.info(f"**GO DESi:** {aw}% aware → {pf}% prefer. "
                f"Conversion ratio **{ratio}×** "
                + ("(punches above its awareness)" if ratio > 1 else "(loses ground from awareness)"))


def render_headtohead(df, keep_rows):
    st.subheader("Head-to-head vs GO DESi")
    comp_opts = [b for b in seeds.CANONICAL["brand_preference"]
                 if b not in (seeds.DROP, "GO DESi", "Prefers whatever's convenient")]
    competitor = st.selectbox("Competitor", comp_opts, key="h2h_comp")
    h = an.head_to_head(df, learned, competitor, keep_rows)
    c = st.columns(3)
    metric_card(c[0], f"Aware of both", h["base"], h["base"], note="the comparable set")
    metric_card(c[1], "GO DESi win-rate", f"{h['win_rate']}%", h["base"])
    metric_card(c[2], f"{competitor} preferred", h["lose"], h["base"])
    if an.directional(h["base"]):
        st.warning(f"Base is {h['base']} — directional only, not conclusive.")
    if h["base"]:
        with st.container(border=True):
            opt = charts.hbar(["GO DESi", competitor, "Other/none"],
                              [h["win"], h["lose"], h["other"]],
                              value_is_pct=False)
            render_chart(opt, height="220px", key="h2h_bar")

    st.write("")
    st.markdown("**Share of mind** (mentions across awareness + recall)")
    som, base = an.share_of_mind(df, learned, keep_rows)
    if not som.empty:
        with st.container(border=True):
            st.caption(f"Base: {base} answered")
            render_chart(charts.hbar(som["value"], som["pct"], value_is_pct=True),
                         height=f"{max(220, 34*len(som))}px", key="som_bar")


def render_format_brand(df, sels, keep_rows):
    st.subheader("Format preference")
    counts, base = an.format_by_brand(df, learned, sels.get("preferred_brand", "All"), keep_rows)
    scope = sels.get("preferred_brand", "All")
    with st.container(border=True):
        st.caption(f"Base: {base} answered"
                   + ("" if scope == "All" else f" · among {scope} preferrers")
                   + (" · ⚠ directional (small base)" if an.directional(base) else ""))
        if not counts.empty:
            render_chart(charts.hbar(counts["value"], counts["pct"], value_is_pct=True),
                         height=f"{max(220, 34*len(counts))}px", key="fmt_bar")


COMMENT_JUNK = {
    "", "na", "n/a", "n.a", "n.a.", "none", "nil", "-", "--", "---", ".",
    "nan", "no", "no comments", "no comment", "nothing", "no response",
    "not answered", "no answer",
}


def render_comments(frames_with_tag):
    st.subheader("Other comments")
    q = st.text_input("Search comments", key="cmt_search", placeholder="e.g. price, sour, packaging")
    rows = []
    for tag, df in frames_with_tag:
        col = nm.find_column(df, "comments")
        if col is None:
            continue
        s = df[col].dropna().astype(str)
        for v in s:
            val = v.strip()
            if val and val.lower() not in COMMENT_JUNK:
                rows.append({"Category": tag, "Comment": val})
    cdf = pd.DataFrame(rows, columns=["Category", "Comment"])
    if q:
        cdf = cdf[cdf["Comment"].str.contains(q, case=False, na=False)]
    st.caption(f"{len(cdf)} comments" + (f" matching “{q}”" if q else ""))
    st.dataframe(cdf, use_container_width=True, hide_index=True, height=460)


# ---------------------------------------------------------------------
# DASHBOARD PAGE
# ---------------------------------------------------------------------
def render_dashboard():
    section = st.session_state.section
    st.title("Consumer insights dashboard")
    st.caption("GO DESi — customer feedback, live from Google Forms")

    if section == "Combined":
        frames = [data["Popz"], data["Meetha"]]
        combined = pd.concat(frames, ignore_index=True)
    tabs_spec = config.tabs_for(section)
    tab_objs = st.tabs([t["title"] for t in tabs_spec])

    for tab, spec in zip(tab_objs, tabs_spec):
        with tab:
            kind = spec["kind"]

            # Overview / Comments handle their own frames
            if kind == "overview":
                if section == "Combined":
                    render_overview(section, frames)
                else:
                    render_overview(section, data[section])
                continue
            if kind == "comments":
                if section == "Combined":
                    render_comments([("Popz", data["Popz"]), ("Meetha", data["Meetha"])])
                else:
                    render_comments([(section, data[section])])
                continue

            # everything else operates on one frame (or combined for Combined section)
            if section == "Combined":
                df = combined
            else:
                df = data[section]

            sels = tab_filters(df, spec, section)
            keep = rows_after_filters(df, sels, learned)

            if kind == "audience":
                render_audience(df, keep)
            elif kind == "bars":
                if section == "Combined" and spec["title"] == "Behavior":
                    # freq + moment resolved per form then merged.
                    # Stack full-width, one bordered card per chart.
                    pairs = (("popz_frequency", "sweets_frequency", "Frequency"),
                             ("popz_moment", "sweets_moment", "Consumption moment"))
                    for i, (fld_p, fld_m, title) in enumerate(pairs):
                        with st.container(border=True):
                            st.markdown(f"**{title}**")
                            # combine both forms' equivalent field
                            cp, bp = an.field_distribution(data["Popz"], fld_p, learned,
                                                           keep & set(data["Popz"].index))
                            cm, bm = an.field_distribution(data["Meetha"], fld_m, learned,
                                                           keep & set(data["Meetha"].index))
                            merged = (pd.concat([cp, cm])
                                      .groupby("value")["count"].sum().reset_index())
                            base = bp + bm
                            merged["pct"] = (merged["count"] / base * 100).round(1) if base else 0
                            merged = merged.sort_values("count", ascending=False)
                            st.caption(f"Base: {base} answered · multi-select where applicable")
                            if not merged.empty:
                                render_chart(charts.hbar(merged["value"], merged["pct"],
                                             value_is_pct=True),
                                             height=f"{max(200,34*len(merged))}px",
                                             key=f"comb_{title}")
                        if i < len(pairs) - 1:
                            st.divider()
                else:
                    # Multiple fields stack vertically full-width — never in
                    # columns — each a bordered card, divided from the next.
                    fields = spec["fields"]
                    for i, field in enumerate(fields):
                        bars_for_field(df, field, learned, keep)
                        if i < len(fields) - 1:
                            st.divider()
            elif kind == "crosssell":
                render_crosssell(df, keep)
            elif kind == "competitive":
                render_competitive(df, keep)
            elif kind == "headtohead":
                render_headtohead(df, keep)
            elif kind == "format_brand":
                render_format_brand(df, sels, keep)


# ---------------------------------------------------------------------
# NORMALIZE PAGE
# ---------------------------------------------------------------------
def render_normalize():
    top = st.columns([3, 1])
    with top[0]:
        st.title("Normalize responses")
        st.caption("Tag unrecognised answers. Approving writes to the Mappings sheet — "
                   "it resolves automatically from the next refresh on.")
    with top[1]:
        if st.button("← Back to dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()

    cat = st.radio("Category", ["Popz", "Meetha", "Combined"], horizontal=True, key="norm_cat")
    if cat == "Combined":
        frames = [("Popz", data["Popz"]), ("Meetha", data["Meetha"])]
    else:
        frames = [(cat, data[cat])]

    # gather unmapped per field across the chosen frames
    # only normalizable fields have a seeds.CANONICAL vocabulary — timestamp,
    # customer_name and comments don't, so skip them (they'd KeyError on select
    # and inflate the unmapped total).
    all_fields = [f for f in config.FIELDS if f in seeds.CANONICAL]
    reports = {}   # field -> {raw: {"count":n, "cats":set}}
    for tag, df in frames:
        if df.empty:
            continue
        for f in all_fields:
            rep = nm.unmapped_report(df, f, learned)
            for _, r in rep.iterrows():
                d = reports.setdefault(f, {})
                e = d.setdefault(r["raw"], {"count": 0, "cats": set()})
                e["count"] += int(r["count"]); e["cats"].add(tag)

    total_unmapped = sum(v["count"] for d in reports.values() for v in d.values())
    st.metric("Unmapped values in view", total_unmapped)

    if not reports:
        st.success("Nothing to normalize in this category — everything resolves cleanly.")
        return

    field_choice = st.selectbox(
        "Question", options=list(reports.keys()),
        format_func=lambda f: config.FIELDS[f]["label"])

    merged = dict(sorted(reports[field_choice].items(), key=lambda kv: -kv[1]["count"]))
    options = seeds.CANONICAL[field_choice] + ["— Ignore (drop) —"]

    with st.form(f"norm_{field_choice}"):
        assignments = {}
        for raw, meta in merged.items():
            cols = st.columns([3, 1, 3])
            tags = ",".join(sorted(meta["cats"]))
            cols[0].markdown(f"`{raw}`  \n<small>{tags}</small>", unsafe_allow_html=True)
            cols[1].markdown(f"×{meta['count']}")
            assignments[raw] = cols[2].selectbox(
                "map", ["— choose —"] + options, key=f"norm_{field_choice}_{raw}",
                label_visibility="collapsed")
        submitted = st.form_submit_button("Approve assigned", type="primary")

    if submitted:
        entries = []
        for raw, choice in assignments.items():
            if choice == "— choose —":
                continue
            canon = seeds.DROP if choice == "— Ignore (drop) —" else choice
            entries.append({"field": field_choice, "raw_value": raw, "canonical": canon})
        if entries:
            try:
                gsheets.append_mappings(entries)
                st.cache_data.clear()
                st.success(f"Saved {len(entries)} mapping(s). Refreshing…")
                st.rerun()
            except Exception as e:  # noqa: BLE001
                st.error(f"Couldn't write to Mappings sheet: {e}")
        else:
            st.info("Nothing assigned yet.")


# ---------------------------------------------------------------------
# ROUTER
# ---------------------------------------------------------------------
if st.session_state.page == "normalize":
    render_normalize()
else:
    render_dashboard()

st.caption("Data cached for 5 minutes · use Refresh data to force a re-pull.")
