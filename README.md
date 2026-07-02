# GO DESi — Consumer Insights Dashboard (v2)

Live, auto-updating Streamlit dashboard for customer feedback from two Google
Forms (Popz + Meetha). Responses flow Forms → Google Sheets → dashboard; no
manual Excel step. Messy free-text answers are normalized by a self-learning
resolver with an in-app review page.

## Navigation

Sidebar-driven:
- **Popz / Meetha / Combined** — three section buttons at the top.
- **Normalize data** — opens an in-app page (not a tab) to tag unrecognised
  answers, with its own Popz/Meetha/Combined category filter for focused review.
- **Refresh data** — clears the cache and re-pulls the sheets.

## Sections & tabs

**Popz (8):** Overview (+ weekly trend, FY-quarter filter) · Audience ·
Acquisition · Behavior · Perception · Motivation · Cross-sell · Comments.

**Meetha (8):** Overview · Audience · Acquisition · Behavior ·
Competitive standing (incl. the awareness→preference conversion) ·
Head-to-head (GO DESi vs a chosen competitor + share-of-mind) ·
Format & brand · Comments.

**Combined (5):** Overview (both trend lines) · Audience · Acquisition ·
Behavior (frequency + moment only) · Comments.

## House rules (baked in)

- Every card and chart shows its own base — "of N answered".
- Percentages are % of respondents who answered that question.
- Multi-select charts note "totals exceed 100%".
- Any base under 30 is flagged "directional only".
- Financial year = Apr–Mar (data currently spans FY26 Q3 → FY27 Q1).
- Filters are per-tab, not global.
- Charts: ECharts, labels always on (percentage-first, count where % is moot),
  and they follow Streamlit's native light/dark toggle.

## Files

| File | Purpose |
|------|---------|
| `app.py` | Sidebar nav, routing, all sections/tabs, Normalize page |
| `config.py` | Sheet IDs, field schema, per-section tabs + per-tab filters, FY logic |
| `analysis.py` | Base-aware metrics (distributions, crosssell, competitive, h2h, trend) |
| `charts.py` | ECharts option builders (labelled bars, grouped bars, line, donut) |
| `normalize.py` | 3-layer resolver + multi-select splitting (unchanged engine) |
| `seeds.py` | Canonical vocab + seed aliases |
| `gsheets.py` | Google Sheets read/write via service account |
| `validate_offline.py` | Smoke-test the whole analysis layer against xlsx, no Google |

## Setup

Sheet IDs are already filled in `config.py`. You still need the service-account
credentials locally:

1. Copy `.streamlit/secrets.toml.example` → `.streamlit/secrets.toml` and paste
   the values from your service-account JSON into `[gcp_service_account]`.
   (If you set up v1, just copy its `.streamlit/secrets.toml` into this folder.)
2. Confirm the three sheets are shared with the service-account email
   (`godesi-insights@customer-insights-501113.iam.gserviceaccount.com`):
   Popz + Meetha as Viewer, Mappings as Editor.
3. Install & run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Test without Google

```bash
python validate_offline.py POPZ.xlsx MEETHA.xlsx
```

Runs every metric against the exported files and prints coverage — the fast loop
after editing `seeds.py`.

## Notes on the data (what the numbers already show)

- **Popz:** ~42% of buyers don't know GO DESi makes sweets — a sized cross-sell
  gap. Dominant perception is "Tamarind Pop"; dominant reason is "Better
  ingredients".
- **Meetha:** GO DESi shows an inverted funnel — ~8% unaided awareness but ~60%
  preference (a ~7.8× conversion ratio). Classic challenger signature: wins on
  trial/taste, loses on top-of-mind salience. Head-to-head vs Haldiram's runs on
  a small base (~20 who considered both), so it's flagged directional.
- The Meetha **preference** question is ~62% filled, so preference-based numbers
  run on a smaller base — shown explicitly on every relevant chart.

## Extending

- New form question → add to `FIELDS` in `config.py`, add a tab entry to the
  relevant `*_TABS`, and add canonical + seed aliases in `seeds.py`.
- Renamed question → update that field's `q` substring (loose matching).
- New answer variants → handled at runtime via the Normalize page, no code edit.
