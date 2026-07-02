"""
Offline validation for v2 — runs the whole analysis layer against the exported
xlsx files, no Google Sheets needed.

    python validate_offline.py POPZ.xlsx MEETHA.xlsx

Prints, per section: field mapping coverage, and a smoke-test of every derived
metric (crosssell, competitive, head-to-head, share-of-mind, trend, FY quarters)
so you can confirm nothing errors before wiring live sheets.
"""

import sys
import pandas as pd

import normalize as nm
from normalize import UNMAPPED
import analysis as an
import config


def coverage(df, section):
    print(f"\n--- {section}: field coverage ---")
    fields = [f for f, m in config.FIELDS.items()
              if m["cat"] in ("shared", section.lower())]
    for f in fields:
        col = nm.find_column(df, f)
        if col is None:
            print(f"  [MISS] {f}")
            continue
        long = nm.resolve_field(df[col], f, {})
        if long.empty:
            print(f"  [ok ] {f}: empty")
            continue
        um = int((long["value"] == UNMAPPED).sum())
        pct = 100 * (len(long) - um) / len(long)
        print(f"  [{'ok ' if um==0 else 'warn'}] {f}: {pct:.0f}% mapped, {um} unmapped")


def smoke(df, section):
    print(f"\n--- {section}: metric smoke test ---")
    print("  quarters:", an.available_quarters(df))
    x, y = an.response_trend(df)
    print(f"  trend weeks: {len(x)}, total: {sum(y)}")
    if section == "Popz":
        print("  crosssell:", an.crosssell(df, {}))
        print("  top perception:", an.top_value(df, "popz_perception", {}))
    else:
        sp, bases, brands = an.brand_stage_table(df, {})
        print("  competitive bases:", bases)
        print("  GO DESi stages:", {s: sp[s].get("GO DESi") for s in sp})
        print("  conversion GO DESi:", an.conversion_ratio(df, {}, "GO DESi"))
        print("  h2h vs Haldiram's:", an.head_to_head(df, {}, "Haldiram's"))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("usage: python validate_offline.py POPZ.xlsx MEETHA.xlsx")
        sys.exit(1)
    popz = nm.normalize_demographics(pd.read_excel(sys.argv[1]), {})
    meetha = nm.normalize_demographics(pd.read_excel(sys.argv[2]), {})
    coverage(popz, "Popz"); smoke(popz, "Popz")
    coverage(meetha, "Meetha"); smoke(meetha, "Meetha")
    print("\nAll metrics ran without error.")
