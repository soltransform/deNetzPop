from __future__ import annotations

import csv
import json
import re
import unicodedata
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "tesla semi" / "data" / "Ladesaeulenregister_BNetzA_2026-04-22.csv"
OUTPUT = ROOT / "map-app" / "bnetza_chargers.geojson"
BOUNDARIES = ROOT / "map-app" / "boundaries"
REGIONS = ROOT / "data" / "official_regions.json"


def parse_decimal(value: str) -> float | None:
    value = (value or "").strip().replace(",", ".")
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_int(value: str) -> int | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return int(float(value.replace(",", ".")))
    except ValueError:
        return None


def charger_class(max_kw: float | None) -> str:
    if max_kw is None:
        return "unknown"
    if max_kw >= 300:
        return "ultra_300"
    if max_kw >= 150:
        return "hpc_150"
    if max_kw > 22:
        return "fast_22"
    return "normal_22"


def max_plug_power(row: dict[str, str]) -> float | None:
    powers: list[float] = []
    for i in range(1, 7):
        value = parse_decimal(row.get(f"Nennleistung Stecker{i}", ""))
        if value is not None:
            powers.append(value)
    fallback = parse_decimal(row.get("Nennleistung Ladeeinrichtung [kW]", ""))
    if fallback is not None:
        powers.append(fallback)
    return max(powers) if powers else None


def normalize_label(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.lower().replace("ß", "ss")
    return re.sub(r"[^a-z0-9]+", "", value)


def iter_rings(geometry: dict[str, Any]):
    kind = geometry.get("type")
    coords = geometry.get("coordinates", [])
    if kind == "Polygon":
        for polygon in [coords]:
            yield polygon
    elif kind == "MultiPolygon":
        for polygon in coords:
            yield polygon


def bbox_for_geometry(geometry: dict[str, Any]) -> tuple[float, float, float, float]:
    xs: list[float] = []
    ys: list[float] = []
    for polygon in iter_rings(geometry):
        for ring in polygon:
            for lon, lat, *_ in ring:
                xs.append(float(lon))
                ys.append(float(lat))
    return min(xs), min(ys), max(xs), max(ys)


def point_in_bbox(lon: float, lat: float, bbox: tuple[float, float, float, float]) -> bool:
    min_lon, min_lat, max_lon, max_lat = bbox
    return min_lon <= lon <= max_lon and min_lat <= lat <= max_lat


def point_in_ring(lon: float, lat: float, ring: list[list[float]]) -> bool:
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = float(ring[i][0]), float(ring[i][1])
        xj, yj = float(ring[j][0]), float(ring[j][1])
        intersects = ((yi > lat) != (yj > lat)) and (
            lon < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-30) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def point_in_polygon(lon: float, lat: float, polygon: list[list[list[float]]]) -> bool:
    if not polygon or not point_in_ring(lon, lat, polygon[0]):
        return False
    for hole in polygon[1:]:
        if point_in_ring(lon, lat, hole):
            return False
    return True


def point_in_geometry(lon: float, lat: float, geometry: dict[str, Any]) -> bool:
    return any(point_in_polygon(lon, lat, polygon) for polygon in iter_rings(geometry))


def region_label(props: dict[str, Any]) -> str:
    name = props.get("gen", "")
    kind = props.get("bez", "")
    if kind in {"Land", ""}:
        return name
    if kind == "Kreis":
        return f"Kreis {name}"
    if kind == "Landkreis":
        return f"Landkreis {name}"
    if kind == "Kreisfreie Stadt":
        return f"Kreisfreie Stadt {name}"
    if kind == "Stadtkreis":
        return f"Stadtkreis {name}"
    return f"{kind} {name}".strip()


def load_regions(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    regions = []
    for feature in payload["features"]:
        props = feature["properties"]
        regions.append({
            "id": str(props["ags"]),
            "label": region_label(props),
            "bbox": bbox_for_geometry(feature["geometry"]),
            "geometry": feature["geometry"],
        })
    return regions


def build_bbox_index(regions: list[dict[str, Any]], cell_size: float = 0.25) -> dict[tuple[int, int], list[dict[str, Any]]]:
    index: dict[tuple[int, int], list[dict[str, Any]]] = {}
    for region in regions:
        min_lon, min_lat, max_lon, max_lat = region["bbox"]
        x0 = int(min_lon / cell_size)
        x1 = int(max_lon / cell_size)
        y0 = int(min_lat / cell_size)
        y1 = int(max_lat / cell_size)
        for x in range(x0, x1 + 1):
            for y in range(y0, y1 + 1):
                index.setdefault((x, y), []).append(region)
    return index


def locate_region(
    lon: float,
    lat: float,
    index: dict[tuple[int, int], list[dict[str, Any]]],
    cell_size: float = 0.25,
) -> dict[str, Any] | None:
    candidates = index.get((int(lon / cell_size), int(lat / cell_size)), [])
    for region in candidates:
        if point_in_bbox(lon, lat, region["bbox"]) and point_in_geometry(lon, lat, region["geometry"]):
            return region
    return None


def load_region_lookups() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    payload = json.loads(REGIONS.read_text(encoding="utf-8"))
    state_lookup: dict[str, dict[str, Any]] = {}
    district_lookup: dict[str, dict[str, Any]] = {}

    for state in payload["states"]:
        for value in {state["name"], state["label"]}:
            state_lookup[normalize_label(value)] = state

    for district in payload["districts"]:
        variants = {
            district["name"],
            district["label"],
            f'{district["kind"]} {district["name"]}',
            f'{district["name"]} {district["kind"]}',
        }
        if district["kind"] == "Landkreis":
            variants.add(f'Kreis {district["name"]}')
        for value in variants:
            district_lookup[normalize_label(value)] = district

    return state_lookup, district_lookup


def main() -> None:
    state_lookup, district_lookup = load_region_lookups()
    features = []
    skipped = 0
    unmatched = 0

    with SOURCE.open("r", encoding="cp1252", newline="") as handle:
        for _ in range(10):
            next(handle)
        reader = csv.DictReader(handle, delimiter=";")
        for row in reader:
            lat = parse_decimal(row.get("Breitengrad", ""))
            lon = parse_decimal(row.get("Längengrad", ""))
            if lat is None or lon is None:
                skipped += 1
                continue
            if not (47 <= lat <= 56 and 5 <= lon <= 16):
                skipped += 1
                continue

            max_kw = max_plug_power(row)
            state = state_lookup.get(normalize_label(row.get("Bundesland", "")))
            district = district_lookup.get(normalize_label(row.get("Kreis/kreisfreie Stadt", "")))
            if district is None or state is None:
                unmatched += 1

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [round(lon, 6), round(lat, 6)],
                },
                "properties": {
                    "id": row.get("Ladeeinrichtungs-ID", ""),
                    "operator": row.get("Betreiber", ""),
                    "name": row.get("Anzeigename (Karte)", ""),
                    "status": row.get("Status", ""),
                    "kind": row.get("Art der Ladeeinrichtung", ""),
                    "points": parse_int(row.get("Anzahl Ladepunkte", "")),
                    "max_kw": max_kw,
                    "class": charger_class(max_kw),
                    "opened": row.get("Inbetriebnahmedatum", ""),
                    "city": row.get("Ort", ""),
                    "kreis": row.get("Kreis/kreisfreie Stadt", ""),
                    "bundesland": row.get("Bundesland", ""),
                    "state_id": state["id"] if state else "",
                    "state_label": state["label"] if state else "",
                    "district_id": district["id"] if district else "",
                    "district_label": district["label"] if district else "",
                },
            })

    payload = {
        "type": "FeatureCollection",
        "metadata": {
            "source": str(SOURCE),
            "generated_from": "BNetzA Ladesaeulenregister 2026-04-22",
            "feature_count": len(features),
            "skipped_rows": skipped,
            "unmatched_official_region_rows": unmatched,
        },
        "features": features,
    }

    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {len(features):,} chargers to {OUTPUT}")
    if skipped:
        print(f"Skipped {skipped:,} rows without usable Germany coordinates")
    if unmatched:
        print(f"{unmatched:,} rows were not matched to both BKG state and district polygons")


if __name__ == "__main__":
    main()
