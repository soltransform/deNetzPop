from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BOUNDARIES = ROOT / "map-app" / "boundaries"
OUTPUT = ROOT / "data" / "official_regions.json"


def iter_positions(geometry: dict[str, Any]):
    kind = geometry.get("type")
    coords = geometry.get("coordinates", [])
    if kind == "Polygon":
      polygons = [coords]
    elif kind == "MultiPolygon":
      polygons = coords
    else:
      polygons = []
    for polygon in polygons:
        for ring in polygon:
            for lon, lat, *_ in ring:
                yield float(lon), float(lat)


def bbox_for_features(features: list[dict[str, Any]]) -> list[float]:
    xs: list[float] = []
    ys: list[float] = []
    for feature in features:
        for lon, lat in iter_positions(feature["geometry"]):
            xs.append(lon)
            ys.append(lat)
    return [min(xs), min(ys), max(xs), max(ys)] if xs else [0, 0, 0, 0]


def group_features(path: Path) -> dict[str, list[dict[str, Any]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    grouped: dict[str, list[dict[str, Any]]] = {}
    for feature in payload["features"]:
        key = str(feature["properties"]["ags"])
        grouped.setdefault(key, []).append(feature)
    return grouped


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


def main() -> None:
    state_groups = group_features(BOUNDARIES / "bkg_states.geojson")
    district_groups = group_features(BOUNDARIES / "bkg_districts.geojson")

    states = []
    for state_id, features in state_groups.items():
        props = features[0]["properties"]
        states.append({
            "id": state_id,
            "name": props["gen"],
            "label": region_label(props),
            "short": props.get("lkz", ""),
            "bbox": bbox_for_features(features),
        })

    districts = []
    for district_id, features in district_groups.items():
        props = features[0]["properties"]
        state_id = str(props["ags"])[:2]
        districts.append({
            "id": district_id,
            "name": props["gen"],
            "label": region_label(props),
            "kind": props.get("bez", ""),
            "state_id": state_id,
            "bbox": bbox_for_features(features),
        })

    states.sort(key=lambda item: item["label"])
    districts.sort(key=lambda item: (item["state_id"], item["label"]))

    OUTPUT.write_text(json.dumps({
        "source": "BKG VG250 copied from archived version 4.20 prototype",
        "license": "Datenlizenz Deutschland Namensnennung 2.0",
        "attribution": "© BKG 2025 dl-de/by-2-0",
        "states": states,
        "districts": districts,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(states)} states and {len(districts)} districts to {OUTPUT}")


if __name__ == "__main__":
    main()
