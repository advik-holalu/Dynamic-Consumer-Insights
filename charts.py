"""
ECharts chart builders for GO DESi Consumer Insights.

Everything here returns an ECharts `option` dict for streamlit_echarts.st_echarts.
House rules baked in:
  - data labels ALWAYS shown on the chart (no hover needed)
  - percentage-first labels; count fallback where % is meaningless (trend line)
  - dark-only: the app is dark everywhere, so text/axis/labels render in a light
    colour (#E5E7EB) on a transparent background — no theme switching
  - amber (#F28C28) is the GO DESi accent; grey for de-emphasis

Use render_chart() in app.py to actually draw (it wires height + key).
"""

from config import HERO, GREY, PALETTE

# Dark-mode palette (fixed — the app is always dark)
TXT = "#E5E7EB"    # axis labels, legend text, data labels
AXIS = "#4B5563"   # axis lines


def _py(seq):
    """Coerce a sequence of numpy scalars to native Python ints/floats for JSON."""
    out = []
    for v in seq:
        try:
            f = float(v)
            out.append(int(f) if f.is_integer() else round(f, 1))
        except (TypeError, ValueError):
            out.append(v)
    return out


def hbar(cats, values, pct=None, color=HERO, value_is_pct=True):
    """Horizontal bar with labels on the bars.
    cats: category names (y). values: numeric (x). pct: optional list of % for labels.
    If value_is_pct, `values` are already percentages and labelled as 'NN%'."""
    # ECharts y-axis draws bottom-up; reverse so largest sits on top
    cats = list(cats)[::-1]
    values = _py(list(values)[::-1])
    if pct is not None:
        pct = list(pct)[::-1]

    label_fmt = "{c}%" if value_is_pct else "{c}"

    series = {
        "type": "bar",
        "data": _py(values),
        "itemStyle": {"color": color, "borderRadius": [0, 4, 4, 0]},
        "label": {
            "show": True,
            "position": "right",
            "color": TXT,
            "fontSize": 12,
            "formatter": label_fmt,
        },
        "barMaxWidth": 26,
    }
    return {
        "backgroundColor": "transparent",
        "grid": {"left": 8, "right": 48, "top": 12, "bottom": 8, "containLabel": True},
        "xAxis": {"type": "value", "show": False, "max": (100 if value_is_pct else None)},
        "yAxis": {
            "type": "category",
            "data": cats,
            "axisLine": {"lineStyle": {"color": AXIS}},
            "axisLabel": {"color": TXT, "fontSize": 12},
        },
        "series": [series],
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
    }


def grouped_hbar(cats, series_map, colors=None, value_is_pct=True):
    """Grouped horizontal bars. series_map: {series_name: [values aligned to cats]}."""
    cats = list(cats)[::-1]
    names = list(series_map.keys())
    colors = colors or PALETTE
    label_fmt = "{c}%" if value_is_pct else "{c}"
    series = []
    for i, nm in enumerate(names):
        vals = _py(list(series_map[nm])[::-1])
        series.append({
            "name": nm,
            "type": "bar",
            "data": vals,
            "itemStyle": {"color": colors[i % len(colors)]},
            "label": {"show": True, "position": "right", "color": TXT,
                      "fontSize": 11, "formatter": label_fmt},
            "barMaxWidth": 16,
        })
    return {
        "backgroundColor": "transparent",
        "legend": {"data": names, "textStyle": {"color": TXT}, "top": 0},
        "grid": {"left": 8, "right": 52, "top": 34, "bottom": 8, "containLabel": True},
        "xAxis": {"type": "value", "show": False, "max": (100 if value_is_pct else None)},
        "yAxis": {"type": "category", "data": cats,
                  "axisLine": {"lineStyle": {"color": AXIS}},
                  "axisLabel": {"color": TXT, "fontSize": 12}},
        "series": series,
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
    }


def line_trend(x_labels, series_map, colors=None):
    """Multi-line trend with point labels (counts). series_map: {name: [counts]}."""
    colors = colors or [HERO] + PALETTE[1:]
    names = list(series_map.keys())
    series = []
    for i, nm in enumerate(names):
        series.append({
            "name": nm,
            "type": "line",
            "smooth": True,
            "data": _py(list(series_map[nm])),
            "itemStyle": {"color": colors[i % len(colors)]},
            "lineStyle": {"color": colors[i % len(colors)], "width": 2},
            "label": {"show": True, "position": "top", "color": TXT,
                      "fontSize": 11, "formatter": "{c}"},
            "symbolSize": 7,
        })
    return {
        "backgroundColor": "transparent",
        "legend": {"data": names, "textStyle": {"color": TXT}, "top": 0},
        "grid": {"left": 8, "right": 20, "top": 34, "bottom": 24, "containLabel": True},
        "xAxis": {"type": "category", "data": list(x_labels), "boundaryGap": False,
                  "axisLine": {"lineStyle": {"color": AXIS}},
                  "axisLabel": {"color": TXT, "fontSize": 11}},
        "yAxis": {"type": "value", "show": False},
        "series": series,
        "tooltip": {"trigger": "axis"},
    }


def donut(cats, values, colors=None):
    """Donut with percentage labels (for yes/no cross-sell etc.)."""
    colors = colors or [HERO, GREY, PALETTE[2]]
    data = [{"value": int(v), "name": c} for c, v in zip(cats, _py(values))]
    return {
        "backgroundColor": "transparent",
        "series": [{
            "type": "pie",
            "radius": ["45%", "70%"],
            "data": data,
            "label": {"show": True, "color": TXT, "fontSize": 12,
                      "formatter": "{b}: {d}%"},
            "labelLine": {"show": True},
        }],
        "color": colors,
        "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
    }
