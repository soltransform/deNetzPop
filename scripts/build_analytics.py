"""
build_analytics.py
Builds analytics.json for the Germany EV Charger Dashboard.

Inputs:
  map-app/chargers.geojson       — 63,653 charger site features
  map-app/coverage_stats.json    — coverage buckets per state/district

Output:
  map-app/analytics.json
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).parent.parent
CHARGERS_PATH = ROOT / "map-app" / "chargers.geojson"
COVERAGE_PATH = ROOT / "map-app" / "coverage_stats.json"
OUTPUT_PATH   = ROOT / "map-app" / "analytics.json"

CLASSES = ["ac_normal", "fast_50", "hpc_150", "ultra_300"]

# ---------------------------------------------------------------------------
# State mapping: charger 'state' string → 2-digit coverage_stats key
# The coverage_stats name for state 08 is "Baden-Württemberg (Bodensee)"
# but chargers use "Baden-Württemberg"; same issue for Bayern.
# ---------------------------------------------------------------------------
STATE_NAME_TO_ID = {
    "Schleswig-Holstein":       "01",
    "Hamburg":                  "02",
    "Niedersachsen":            "03",
    "Bremen":                   "04",
    "Nordrhein-Westfalen":      "05",
    "Hessen":                   "06",
    "Rheinland-Pfalz":          "07",
    "Baden-Württemberg":        "08",
    "Bayern":                   "09",
    "Saarland":                 "10",
    "Berlin":                   "11",
    "Brandenburg":              "12",
    "Mecklenburg-Vorpommern":   "13",
    "Sachsen":                  "14",
    "Sachsen-Anhalt":           "15",
    "Thüringen":                "16",
}


def normalize_whitespace(s: str) -> str:
    """Collapse multiple spaces, normalize spaces after dots in abbreviations."""
    import re
    # Remove spaces after dots in abbreviations like "a.d. Ilm" → "a.d.Ilm"
    s = re.sub(r'(\.\s)([A-ZÜÄÖ])', lambda m: '.' + m.group(2), s)
    # Normalize multiple spaces to single
    s = re.sub(r' +', ' ', s)
    return s.strip()


def build_county_to_district_id(cov_districts: dict) -> dict:
    """
    Build a mapping from charger 'county' string → district ID.

    Coverage_stats district names look like:
      "Flensburg, Kreisfreie Stadt"   → charger uses "Kreisfreie Stadt Flensburg"
      "Dithmarschen, Kreis"           → charger uses "Kreis Dithmarschen"
      "Gifhorn, Landkreis"            → charger uses "Landkreis Gifhorn"
      "Stuttgart, Stadtkreis"         → charger uses "Stadtkreis Stuttgart"
      "Region Hannover, Landkreis"    → charger uses "Landkreis Region Hannover"

    Bavarian edge cases (abbreviation spacing):
      "Mühldorf a.Inn, Landkreis"       → charger uses "Landkreis Mühldorf a. Inn"
      "Weiden i.d.OPf., Kreisfreie Stadt" → charger "Kreisfreie Stadt Weiden i.d. OPf."

    Strategy: parse "BaseName, TypePart" → build "TypePart BaseName" as lookup key.
    Also store normalized (whitespace-collapsed) variants for abbreviation edge cases.
    """
    mapping = {}
    # Build forward map: coverage name → id
    cov_name_to_id = {v.get("name", ""): k for k, v in cov_districts.items()}

    for cov_name, dist_id in cov_name_to_id.items():
        if not cov_name:
            continue
        # Direct storage
        mapping[cov_name] = dist_id

        # Try to invert "BaseName, TypePart" → "TypePart BaseName"
        if "," in cov_name:
            parts = cov_name.split(",", 1)
            base = parts[0].strip()
            type_part = parts[1].strip()
            inverted = type_part + " " + base
            mapping[inverted] = dist_id

            # Also store just the base name (handles exact city name matches)
            mapping[base] = dist_id

            # Store normalized variant (collapse abbreviation spaces)
            norm_inverted = normalize_whitespace(inverted)
            if norm_inverted != inverted:
                mapping[norm_inverted] = dist_id

    return mapping


def normalize_county(county: str) -> str:
    """Normalize charger county name for matching (collapse spaces in abbreviations)."""
    return normalize_whitespace(county)


def round1(v) -> float:
    return round(float(v), 1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("Loading input files...")
    with open(CHARGERS_PATH, encoding="utf-8") as f:
        geo = json.load(f)
    with open(COVERAGE_PATH, encoding="utf-8") as f:
        cov = json.load(f)

    features = geo["features"]
    print(f"  Charger features: {len(features)}")
    print(f"  Coverage states:  {len(cov['states'])}")
    print(f"  Coverage districts: {len(cov['districts'])}")

    county_to_district = build_county_to_district_id(cov["districts"])

    # -----------------------------------------------------------------------
    # Pass 1: aggregate per charger feature
    # -----------------------------------------------------------------------
    # For operators
    op_sites       = defaultdict(int)
    op_cp          = defaultdict(int)
    op_power_sum   = defaultdict(float)
    op_by_class    = defaultdict(lambda: defaultdict(int))
    op_by_state    = defaultdict(lambda: defaultdict(int))

    # For growth
    year_class_new = defaultdict(lambda: defaultdict(int))  # year → class → count

    # For states
    state_sites    = defaultdict(int)
    state_cp       = defaultdict(int)
    state_by_class = defaultdict(lambda: defaultdict(int))

    # For districts
    dist_sites     = defaultdict(int)
    dist_cp        = defaultdict(int)
    dist_by_class  = defaultdict(lambda: defaultdict(int))
    district_unmapped = set()

    # For growth_by_region (cumulative sites per state/district per year)
    state_year_new = defaultdict(lambda: defaultdict(int))  # state_id → year → new sites
    dist_year_new  = defaultdict(lambda: defaultdict(int))  # dist_id → year → new sites

    # National totals
    total_sites = 0
    total_cp    = 0
    total_power = 0.0

    for feat in features:
        p = feat["properties"]
        operator    = p.get("operator") or "Unknown"
        cls         = p.get("class") or "ac_normal"
        if cls not in CLASSES:
            cls = "ac_normal"
        charge_pts  = int(p.get("charge_points") or 0)
        site_power  = float(p.get("site_power_kw") or 0.0)
        state_name  = p.get("state") or ""
        county_name = p.get("county") or ""
        start_date  = p.get("start_date") or ""

        total_sites += 1
        total_cp    += charge_pts
        total_power += site_power

        # Operator aggregation
        op_sites[operator]     += 1
        op_cp[operator]        += charge_pts
        op_power_sum[operator] += site_power
        op_by_class[operator][cls] += 1
        if state_name:
            op_by_state[operator][state_name] += 1

        # Growth (parse date)
        start_year = None
        if start_date:
            try:
                dt = datetime.strptime(start_date.strip(), "%d.%m.%Y")
                if dt.year >= 2010:
                    year_class_new[dt.year][cls] += 1
                    start_year = dt.year
            except ValueError:
                pass

        # State aggregation
        state_id = STATE_NAME_TO_ID.get(state_name)
        if state_id:
            state_sites[state_id]     += 1
            state_cp[state_id]        += charge_pts
            state_by_class[state_id][cls] += 1
            if start_year:
                state_year_new[state_id][start_year] += 1

        # District aggregation
        dist_id = county_to_district.get(county_name)
        if dist_id is None and county_name:
            # Try normalized form (handles spacing differences in abbreviations)
            dist_id = county_to_district.get(normalize_county(county_name))
        if dist_id:
            dist_sites[dist_id]     += 1
            dist_cp[dist_id]        += charge_pts
            dist_by_class[dist_id][cls] += 1
            if start_year:
                dist_year_new[dist_id][start_year] += 1
        elif county_name:
            district_unmapped.add(county_name)

    if district_unmapped:
        print(f"  WARNING: {len(district_unmapped)} unmapped county values:")
        for c in sorted(district_unmapped):
            print(f"    {repr(c)}")

    # -----------------------------------------------------------------------
    # Market summary
    # -----------------------------------------------------------------------
    market_summary = {
        "total_operators":   len(op_sites),
        "total_sites":       total_sites,
        "total_charge_points": total_cp,
        "avg_site_power_kw": round1(total_power / total_sites if total_sites else 0),
    }

    # -----------------------------------------------------------------------
    # National per_100k and pct_hpc_plus (for gap score normalization)
    # -----------------------------------------------------------------------
    germany_pop = cov["germany"]["population"]
    national_per_100k = total_sites / germany_pop * 100_000 if germany_pop else 0

    total_hpc_plus = sum(
        state_by_class[sid].get("hpc_150", 0) + state_by_class[sid].get("ultra_300", 0)
        for sid in state_sites
    )
    national_pct_hpc_plus = total_hpc_plus / total_sites * 100 if total_sites else 0

    print(f"\nNational stats:")
    print(f"  Total sites: {total_sites}, total CP: {total_cp}")
    print(f"  National per_100k: {national_per_100k:.2f}")
    print(f"  National pct_hpc_plus: {national_pct_hpc_plus:.2f}%")

    # -----------------------------------------------------------------------
    # Operators (top 50 + Other)
    # -----------------------------------------------------------------------
    all_ops_sorted = sorted(op_sites.keys(), key=lambda o: op_cp[o], reverse=True)

    def build_operator_entry(name, site_list):
        sites_n = op_sites[name]
        cp_n    = op_cp[name]
        power_n = op_power_sum[name]
        by_cls  = {c: op_by_class[name].get(c, 0) for c in CLASSES}
        hpc_n   = by_cls["hpc_150"] + by_cls["ultra_300"]
        pct_hpc = hpc_n / sites_n * 100 if sites_n else 0
        by_st   = dict(op_by_state[name])
        return {
            "name":          name,
            "sites":         sites_n,
            "charge_points": cp_n,
            "avg_kw_per_site": round1(power_n / sites_n if sites_n else 0),
            "pct_hpc_plus":  round1(pct_hpc),
            "by_class":      by_cls,
            "by_state":      by_st,
        }

    operators_out = []
    top50 = all_ops_sorted[:50]
    rest  = all_ops_sorted[50:]

    for op in top50:
        operators_out.append(build_operator_entry(op, None))

    if rest:
        rest_sites = sum(op_sites[o] for o in rest)
        rest_cp    = sum(op_cp[o]    for o in rest)
        rest_power = sum(op_power_sum[o] for o in rest)
        rest_by_class = {c: sum(op_by_class[o].get(c, 0) for o in rest) for c in CLASSES}
        rest_hpc   = rest_by_class["hpc_150"] + rest_by_class["ultra_300"]
        rest_pct   = rest_hpc / rest_sites * 100 if rest_sites else 0
        rest_by_state = defaultdict(int)
        for o in rest:
            for st, cnt in op_by_state[o].items():
                rest_by_state[st] += cnt

        operators_out.append({
            "name":          f"Other ({len(rest)} operators)",
            "sites":         rest_sites,
            "charge_points": rest_cp,
            "avg_kw_per_site": round1(rest_power / rest_sites if rest_sites else 0),
            "pct_hpc_plus":  round1(rest_pct),
            "by_class":      rest_by_class,
            "by_state":      dict(rest_by_state),
        })

    print(f"\nOperators: {len(top50)} top + {len(rest)} aggregated as 'Other'")

    # -----------------------------------------------------------------------
    # Growth
    # -----------------------------------------------------------------------
    all_years = sorted(year_class_new.keys())
    cumulative = {c: 0 for c in CLASSES}
    growth_out = []

    for year in all_years:
        new_counts = {c: year_class_new[year].get(c, 0) for c in CLASSES}
        for c in CLASSES:
            cumulative[c] += new_counts[c]
        total_new = sum(new_counts.values())
        total_cum = sum(cumulative.values())
        growth_out.append({
            "year":             year,
            "new":              dict(new_counts),
            "cumulative":       dict(cumulative),
            "total_new":        total_new,
            "total_cumulative": total_cum,
        })

    print(f"\nGrowth years: {all_years[0] if all_years else 'none'} – {all_years[-1] if all_years else 'none'}")

    # -----------------------------------------------------------------------
    # Regions – States
    # -----------------------------------------------------------------------
    def compute_gap_score(cov_region, sites_n, pop, per_100k, pct_hpc_plus_local):
        # Component 1: DC coverage underserved
        buckets_dc = cov_region.get("buckets_dc", [])
        dc_covered = buckets_dc[5] if len(buckets_dc) > 5 else 0
        cov_dc_pct = dc_covered / pop * 100 if pop > 0 else 0
        underserved = (1 - cov_dc_pct / 100) * 100

        # Component 2: density deficit
        density_deficit = max(0.0, 1 - (per_100k / national_per_100k)) * 100 if national_per_100k else 0

        # Component 3: ultra-fast gap
        ultra_gap = max(0.0, 1 - (pct_hpc_plus_local / national_pct_hpc_plus)) * 100 if national_pct_hpc_plus else 0

        return round1(0.5 * underserved + 0.3 * density_deficit + 0.2 * ultra_gap)

    states_out = []
    for state_id, state_data in sorted(cov["states"].items()):
        pop = state_data.get("population", 0)
        # Friendly name (strip Bodensee annotation)
        raw_name = state_data.get("name", state_id)
        name = raw_name.split(" (")[0].strip()

        sites_n = state_sites.get(state_id, 0)
        cp_n    = state_cp.get(state_id, 0)
        per_100k_local = sites_n / pop * 100_000 if pop > 0 else 0

        # coverage_pct_5km uses buckets_any[5]
        buckets_any = state_data.get("buckets_any", [])
        any_covered = buckets_any[5] if len(buckets_any) > 5 else 0
        cov_pct_5km = any_covered / pop * 100 if pop > 0 else 0

        by_cls = state_by_class.get(state_id, {})
        hpc_n  = by_cls.get("hpc_150", 0) + by_cls.get("ultra_300", 0)
        pct_hpc = hpc_n / sites_n * 100 if sites_n > 0 else 0

        gap = compute_gap_score(state_data, sites_n, pop, per_100k_local, pct_hpc)

        states_out.append({
            "id":               state_id,
            "name":             name,
            "population":       round1(pop),
            "sites":            sites_n,
            "charge_points":    cp_n,
            "per_100k":         round1(per_100k_local),
            "coverage_pct_5km": round1(cov_pct_5km),
            "pct_hpc_plus":     round1(pct_hpc),
            "gap_score":        gap,
        })

    # -----------------------------------------------------------------------
    # Regions – Districts
    # -----------------------------------------------------------------------
    districts_out = []
    for dist_id, dist_data in sorted(cov["districts"].items()):
        pop = dist_data.get("population", 0)
        raw_name = dist_data.get("name", dist_id)
        # Invert "BaseName, TypePart" back to a clean display name
        if "," in raw_name:
            parts = raw_name.split(",", 1)
            # Use "TypePart BaseName" format for display
            display_name = parts[1].strip() + " " + parts[0].strip()
        else:
            display_name = raw_name

        state_id = dist_id[:2]

        sites_n = dist_sites.get(dist_id, 0)
        cp_n    = dist_cp.get(dist_id, 0)
        per_100k_local = sites_n / pop * 100_000 if pop > 0 else 0

        buckets_any = dist_data.get("buckets_any", [])
        any_covered = buckets_any[5] if len(buckets_any) > 5 else 0
        cov_pct_5km = any_covered / pop * 100 if pop > 0 else 0

        by_cls = dist_by_class.get(dist_id, {})
        hpc_n  = by_cls.get("hpc_150", 0) + by_cls.get("ultra_300", 0)
        pct_hpc = hpc_n / sites_n * 100 if sites_n > 0 else 0

        gap = compute_gap_score(dist_data, sites_n, pop, per_100k_local, pct_hpc)

        districts_out.append({
            "id":               dist_id,
            "name":             display_name,
            "state_id":         state_id,
            "population":       round1(pop),
            "sites":            sites_n,
            "charge_points":    cp_n,
            "per_100k":         round1(per_100k_local),
            "coverage_pct_5km": round1(cov_pct_5km),
            "pct_hpc_plus":     round1(pct_hpc),
            "gap_score":        gap,
        })

    # -----------------------------------------------------------------------
    # Growth by region (cumulative sites per state/district per year)
    # -----------------------------------------------------------------------
    growth_by_region = {"states": {}, "districts": {}}

    for state_id in sorted(state_year_new.keys()):
        yearly = state_year_new[state_id]
        cum = 0
        state_cum = {}
        for yr in all_years:
            cum += yearly.get(yr, 0)
            state_cum[str(yr)] = cum
        growth_by_region["states"][state_id] = state_cum

    for dist_id in sorted(dist_year_new.keys()):
        yearly = dist_year_new[dist_id]
        cum = 0
        dist_cum = {}
        for yr in all_years:
            cum += yearly.get(yr, 0)
            dist_cum[str(yr)] = cum
        growth_by_region["districts"][dist_id] = dist_cum

    print(f"\nGrowth by region: {len(growth_by_region['states'])} states, {len(growth_by_region['districts'])} districts")

    # -----------------------------------------------------------------------
    # Assemble output
    # -----------------------------------------------------------------------
    analytics = {
        "market_summary": market_summary,
        "operators":      operators_out,
        "growth":         growth_out,
        "growth_by_region": growth_by_region,
        "regions": {
            "states":    states_out,
            "districts": districts_out,
        },
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(analytics, f, ensure_ascii=False, separators=(",", ":"))

    # -----------------------------------------------------------------------
    # Summary stats
    # -----------------------------------------------------------------------
    file_size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(f"\n{'='*60}")
    print(f"Output: {OUTPUT_PATH}")
    print(f"File size: {file_size_kb:.1f} KB")
    print(f"\nMarket Summary:")
    print(f"  Total operators:    {market_summary['total_operators']}")
    print(f"  Total sites:        {market_summary['total_sites']}")
    print(f"  Total charge points:{market_summary['total_charge_points']}")
    print(f"  Avg site power kW:  {market_summary['avg_site_power_kw']}")
    print(f"\nTop 5 operators by charge points:")
    for op in operators_out[:5]:
        print(f"  {op['name'][:40]}: {op['charge_points']} CP, {op['sites']} sites")
    print(f"\nGrowth data: {len(growth_out)} years")
    print(f"  First year: {growth_out[0]['year'] if growth_out else 'N/A'}, cumulative: {growth_out[0]['total_cumulative'] if growth_out else 0}")
    print(f"  Last year:  {growth_out[-1]['year'] if growth_out else 'N/A'}, cumulative: {growth_out[-1]['total_cumulative'] if growth_out else 0}")
    print(f"\nRegions:")
    print(f"  States: {len(states_out)}")
    print(f"  Districts: {len(districts_out)}")
    print(f"\nTop 5 gap states:")
    for s in sorted(states_out, key=lambda x: x["gap_score"], reverse=True)[:5]:
        print(f"  {s['name']}: gap={s['gap_score']}, per_100k={s['per_100k']}, cov={s['coverage_pct_5km']}%")
    print(f"\nDone!")


if __name__ == "__main__":
    main()
