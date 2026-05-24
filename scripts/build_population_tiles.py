"""
Build Germany population + charger distance RGBA tiles → PMTiles + coverage_stats.json.

Encoding per pixel:
  R = population (log2 scale: round(log2(pop+1)*255/16))
  G = distance to nearest AC charger (0-50 km → 0-255)
  B = distance to nearest DC fast charger (fast_50 + hpc_150)
  A = distance to nearest ultra charger (ultra_300)

Run:
  & "C:\\Users\\KitCat\\Desktop\\tesla semi\\.venv\\Scripts\\python.exe" scripts\\build_population_tiles.py
"""

import json, io, os, time
from pathlib import Path
import numpy as np
from PIL import Image
from pyproj import Transformer
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
TIF_PATH = Path(r"C:\Users\KitCat\Desktop\tesla semi\data\GHS_POP_E2030_GLOBE_R2023A_54009_100_V1_0.tif")
CHARGER_PATH = ROOT / "map-app" / "chargers.geojson"
STATES_PATH = ROOT / "map-app" / "boundaries" / "bkg_states.geojson"
DISTRICTS_PATH = ROOT / "map-app" / "boundaries" / "bkg_districts.geojson"
OUT_PMTILES = ROOT / "map-app" / "germany_pop.pmtiles"
OUT_STATS = ROOT / "map-app" / "coverage_stats.json"
CACHE_DIR = ROOT / "data" / "tile_cache"
PIXELS_CACHE = CACHE_DIR / "germany_pixels.npz"

TILE = 256
MAX_Z = 12
MIN_Z = 5
MAX_DIST = 50.0
HALF_CELL = 50.0
MIN_POP = 0.1

MOLL2WGS = Transformer.from_crs("ESRI:54009", "EPSG:4326", always_xy=True)
WGS2MOLL = Transformer.from_crs("EPSG:4326", "ESRI:54009", always_xy=True)


# ═══════════════════════════ Phase 1: extract pixels ═════════════════════════

def extract_pixels():
    if PIXELS_CACHE.exists():
        print(f"  cached: {PIXELS_CACHE.name}")
        d = np.load(str(PIXELS_CACHE))
        return d["x_moll"], d["y_moll"], d["lons"], d["lats"], d["pop"]

    import rasterio
    from rasterio.windows import Window

    cx = [5.5, 15.5, 5.5, 15.5, 10.5, 5.5, 15.5]
    cy = [47.0, 47.0, 55.5, 55.5, 55.5, 51.0, 51.0]
    mx, my = WGS2MOLL.transform(cx, cy)
    mxn, mxx = min(mx) - 500, max(mx) + 500
    myn, myx = min(my) - 500, max(my) + 500

    with rasterio.open(str(TIF_PATH)) as ds:
        tf = ds.transform
        nd = ds.nodata
        cmin = max(0, int((mxn - tf.c) / tf.a))
        cmax = min(ds.width, int((mxx - tf.c) / tf.a) + 1)
        rmin = max(0, int((myx - tf.f) / tf.e))
        rmax = min(ds.height, int((myn - tf.f) / tf.e) + 1)
        print(f"  TIFF window: rows {rmin}-{rmax}, cols {cmin}-{cmax}")

        out = {k: [] for k in ("xm", "ym", "lo", "la", "po")}
        total = 0
        STRIP = 4096
        for ro in range(rmin, rmax, STRIP):
            h = min(STRIP, rmax - ro)
            w = cmax - cmin
            data = ds.read(1, window=Window(cmin, ro, w, h)).astype(np.float32)
            mask = (data != nd) & (data >= MIN_POP)
            if not mask.any():
                continue
            rows, cols = np.where(mask)
            xm = tf.c + (cols + cmin + 0.5) * tf.a
            ym = tf.f + (rows + ro + 0.5) * tf.e
            lo, la = MOLL2WGS.transform(xm.astype(np.float64), ym.astype(np.float64))
            keep = (lo >= 5.5) & (lo <= 15.5) & (la >= 47.0) & (la <= 55.5)
            out["xm"].append(xm[keep].astype(np.float32))
            out["ym"].append(ym[keep].astype(np.float32))
            out["lo"].append(np.float32(lo[keep]))
            out["la"].append(np.float32(la[keep]))
            out["po"].append(data[mask][keep])
            total += int(keep.sum())
            if total % 500_000 < int(keep.sum()):
                print(f"    {total:,} cells so far")

    r = {k: np.concatenate(v) for k, v in out.items()}
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(str(PIXELS_CACHE),
                        x_moll=r["xm"], y_moll=r["ym"],
                        lons=r["lo"], lats=r["la"], pop=r["po"])
    print(f"  {len(r['po']):,} cells → {PIXELS_CACHE.name}")
    return r["xm"], r["ym"], r["lo"], r["la"], r["po"]


# ═══════════════════════════ Phase 2: distances ══════════════════════════════

def compute_distances(lons, lats):
    with open(CHARGER_PATH, encoding="utf-8") as f:
        gj = json.load(f)

    tiers = {"ac": [], "dc": [], "ultra": []}
    for feat in gj["features"]:
        lon, lat = feat["geometry"]["coordinates"]
        cls = feat["properties"].get("class", "ac_normal")
        if cls == "ac_normal":
            tiers["ac"].append((lon, lat))
        elif cls in ("fast_50", "hpc_150"):
            tiers["dc"].append((lon, lat))
        elif cls == "ultra_300":
            tiers["ultra"].append((lon, lat))

    cos_lat = np.cos(np.radians(float(np.mean(lats))))
    sx, sy = cos_lat * 111_320.0, 111_320.0
    cell_xy = np.column_stack([lons * sx, lats * sy])

    result = {}
    for name, coords in tiers.items():
        if not coords:
            result[name] = np.full(len(lons), 999.0, dtype=np.float32)
            print(f"    {name}: 0 chargers")
            continue
        arr = np.array(coords)
        tree = cKDTree(np.column_stack([arr[:, 0] * sx, arr[:, 1] * sy]))
        t0 = time.time()
        dist_m, _ = tree.query(cell_xy)
        result[name] = (dist_m / 1000.0).astype(np.float32)
        print(f"    {name}: {len(coords):,} chargers, {time.time()-t0:.1f}s")

    return result["ac"], result["dc"], result["ultra"]


# ═══════════════════════════ Phase 3: coverage stats ═════════════════════════

def compute_coverage_stats(lons, lats, pop, d_ac, d_dc, d_ultra):
    from shapely.geometry import shape
    from shapely import STRtree, points as shp_points

    d_any = np.minimum(np.minimum(d_ac, d_dc), d_ultra)

    def stats_for(mask):
        p = pop[mask]
        total = float(p.sum())
        if total == 0:
            return None
        da, dd, du, dn = d_ac[mask], d_dc[mask], d_ultra[mask], d_any[mask]
        b_any = [float(p[dn <= km].sum()) for km in range(51)]
        b_dc = [float(p[dd <= km].sum()) for km in range(51)]
        b_ultra = [float(p[du <= km].sum()) for km in range(51)]
        mi = int(np.argmax(dn))
        lo_m, la_m = lons[mask], lats[mask]
        return {
            "population": total,
            "buckets_any": b_any, "buckets_dc": b_dc, "buckets_ultra": b_ultra,
            "max_distance_any": round(float(dn[mi]), 2),
            "max_distance_location": [round(float(lo_m[mi]), 4), round(float(la_m[mi]), 4)],
        }

    result = {}
    print(f"  total cells in bbox: {len(pop):,} ({pop.sum()/1e6:.1f}M pop)")

    with open(STATES_PATH, encoding="utf-8") as f:
        states_gj = json.load(f)
    with open(DISTRICTS_PATH, encoding="utf-8") as f:
        districts_gj = json.load(f)

    d_geoms, d_meta = [], []
    for feat in districts_gj["features"]:
        geom = shape(feat["geometry"])
        if not geom.is_valid:
            geom = geom.buffer(0)
        d_geoms.append(geom)
        p = feat["properties"]
        d_meta.append({"ags": p.get("ags", ""), "name": p.get("gen", ""), "bez": p.get("bez", "")})

    pts = shp_points(lons, lats)
    print(f"  STRtree query for {len(pts):,} cells...")
    t0 = time.time()
    tree = STRtree(d_geoms)
    pt_idx, geom_idx = tree.query(pts, predicate="intersects")
    print(f"  {len(pt_idx):,} hits in {time.time()-t0:.1f}s")

    cell_dist = np.full(len(pop), -1, dtype=np.int32)
    order = np.argsort(pt_idx)
    pt_sorted = pt_idx[order]
    geom_sorted = geom_idx[order]
    _, first = np.unique(pt_sorted, return_index=True)
    cell_dist[pt_sorted[first]] = geom_sorted[first]
    n_assigned = int((cell_dist >= 0).sum())
    print(f"  assigned: {n_assigned:,}/{len(pop):,}")

    s_map = {}
    for feat in states_gj["features"]:
        s_map[feat["properties"].get("ags", "")] = feat["properties"].get("gen", "")

    # Germany total from assigned cells only
    assigned = cell_dist >= 0
    result["germany"] = stats_for(assigned)
    print(f"  Germany (assigned): {result['germany']['population']/1e6:.1f}M pop")

    # vectorized state assignment
    dist_to_state = np.array([m["ags"][:2] for m in d_meta])
    cell_state = np.full(len(pop), "", dtype="U2")
    cell_state[assigned] = dist_to_state[cell_dist[assigned]]

    result["states"] = {}
    for s_ags, s_name in s_map.items():
        mask = cell_state == s_ags
        s = stats_for(mask)
        if s:
            s["name"] = s_name
            result["states"][s_ags] = s

    result["districts"] = {}
    for di, meta in enumerate(d_meta):
        mask = cell_dist == di
        s = stats_for(mask)
        if s:
            label = meta["name"]
            if meta["bez"]:
                label = f"{meta['name']}, {meta['bez']}"
            s["name"] = label
            result["districts"][meta["ags"]] = s

    with open(OUT_STATS, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)
    sz = OUT_STATS.stat().st_size / 1024
    print(f"  → {OUT_STATS.name} ({sz:.0f} KB), {len(result['states'])} states, {len(result['districts'])} districts")
    return result


# ═══════════════════════════ Phase 4: tile pyramid ═══════════════════════════

def _gpx(lons, z):
    return (lons + 180.0) / 360.0 * (1 << z) * TILE

def _gpy(lats, z):
    lats = np.clip(lats, -85.05112878, 85.05112878)
    s = np.sin(np.radians(lats))
    return (0.5 - np.log((1 + s) / (1 - s)) / (4 * np.pi)) * (1 << z) * TILE


def build_footprints(xm, ym):
    n = len(xm)
    print(f"  footprints for {n:,} cells at z{MAX_Z}...")
    t0 = time.time()
    x0 = np.empty(n, np.int32); x1 = np.empty(n, np.int32)
    y0 = np.empty(n, np.int32); y1 = np.empty(n, np.int32)
    B = 1_000_000
    world = (1 << MAX_Z) * TILE
    for s in range(0, n, B):
        e = min(s + B, n)
        xl = xm[s:e].astype(np.float64) - HALF_CELL
        xr = xm[s:e].astype(np.float64) + HALF_CELL
        yt = ym[s:e].astype(np.float64) + HALF_CELL
        yb = ym[s:e].astype(np.float64) - HALF_CELL
        cx = np.concatenate([xl, xr, xr, xl])
        cy = np.concatenate([yt, yt, yb, yb])
        clon, clat = MOLL2WGS.transform(cx, cy)
        m = e - s
        px = _gpx(np.asarray(clon), MAX_Z).reshape(4, m)
        py = _gpy(np.asarray(clat), MAX_Z).reshape(4, m)
        ok = np.isfinite(px).all(0) & np.isfinite(py).all(0)
        px = np.where(np.isfinite(px), px, 0.0)
        py = np.where(np.isfinite(py), py, 0.0)
        rx0 = np.clip(np.floor(px.min(0)).astype(np.int32), 0, world - 1)
        rx1 = np.clip(np.floor(px.max(0)).astype(np.int32), 0, world - 1)
        ry0 = np.clip(np.floor(py.min(0)).astype(np.int32), 0, world - 1)
        ry1 = np.clip(np.floor(py.max(0)).astype(np.int32), 0, world - 1)
        x0[s:e] = np.where(ok, rx0, 1)
        x1[s:e] = np.where(ok, rx1, 0)
        y0[s:e] = np.where(ok, ry0, 1)
        y1[s:e] = np.where(ok, ry1, 0)
    print(f"  done in {time.time()-t0:.1f}s")
    return x0, x1, y0, y1


def render_row(tile_y, cell_idx, fp_x0, fp_x1, fp_y0, fp_y1,
               pop, d_ac, d_dc, d_ultra):
    """Render all z=MAX_Z tiles in this tile row. Returns dict (tx,ty)->4 grids."""
    row_top = tile_y * TILE
    row_bot = row_top + TILE - 1
    if len(cell_idx) == 0:
        return {}

    cx0 = fp_x0[cell_idx]
    cx1 = fp_x1[cell_idx]
    cy0 = np.clip(fp_y0[cell_idx], row_top, row_bot)
    cy1 = np.clip(fp_y1[cell_idx], row_top, row_bot)
    ok = (cx1 >= cx0) & (cy1 >= cy0)
    if not ok.any():
        return {}

    cx0, cx1, cy0, cy1 = cx0[ok], cx1[ok], cy0[ok], cy1[ok]
    cp = pop[cell_idx[ok]]
    ca = d_ac[cell_idx[ok]]
    cd = d_dc[cell_idx[ok]]
    cu = d_ultra[cell_idx[ok]]

    widths = (cx1 - cx0 + 1).astype(np.int64)
    heights = (cy1 - cy0 + 1).astype(np.int64)
    counts = widths * heights
    total = int(counts.sum())
    if total == 0:
        return {}

    # expand footprints to individual pixel contributions
    CHUNK = 2_000_000
    tiles = {}
    start = 0
    while start < len(cx0):
        end = start
        emitted = 0
        while end < len(cx0) and emitted + int(counts[end]) <= CHUNK:
            emitted += int(counts[end])
            end += 1
        if end == start:
            emitted = int(counts[start])
            end = start + 1

        c_counts = counts[start:end]
        c_widths = widths[start:end]
        c_x0 = cx0[start:end].astype(np.int64)
        c_y0 = cy0[start:end].astype(np.int64)

        local = np.arange(emitted, dtype=np.int64) - np.repeat(
            np.cumsum(c_counts) - c_counts, c_counts)
        rw = np.repeat(c_widths, c_counts)
        rx0 = np.repeat(c_x0, c_counts)
        ry0 = np.repeat(c_y0, c_counts)

        gx = rx0 + (local % rw)
        gy = ry0 + (local // rw)
        tx = (gx // TILE).astype(np.int32)
        lpx = (gx - tx.astype(np.int64) * TILE).astype(np.int32)
        lpy = (gy - row_top).astype(np.int32)

        rp = np.repeat(cp[start:end], c_counts)
        ra = np.repeat(ca[start:end], c_counts)
        rd = np.repeat(cd[start:end], c_counts)
        ru = np.repeat(cu[start:end], c_counts)

        # group by tile_x
        order = np.argsort(tx, kind="stable")
        tx_s = tx[order]
        utx, upos = np.unique(tx_s, return_index=True)
        uend = np.append(upos[1:], len(tx_s))

        for ui, sp, ep in zip(utx, upos, uend):
            sel = order[sp:ep]
            key = (int(ui), tile_y)
            if key not in tiles:
                tiles[key] = (
                    np.zeros((TILE, TILE), dtype=np.float32),
                    np.full((TILE, TILE), np.inf, dtype=np.float32),
                    np.full((TILE, TILE), np.inf, dtype=np.float32),
                    np.full((TILE, TILE), np.inf, dtype=np.float32),
                )
            gp, ga, gd, gu = tiles[key]
            spy, spx = lpy[sel], lpx[sel]
            np.add.at(gp, (spy, spx), rp[sel])
            np.minimum.at(ga, (spy, spx), ra[sel])
            np.minimum.at(gd, (spy, spx), rd[sel])
            np.minimum.at(gu, (spy, spx), ru[sel])

        start = end

    return tiles


def encode_png(pop_g, ac_g, dc_g, ultra_g):
    has = pop_g > 0
    if not has.any():
        return None
    rgba = np.zeros((TILE, TILE, 4), dtype=np.uint8)
    lp = np.where(has, np.round(np.log2(pop_g + 1) * 255.0 / 16.0), 0)
    rgba[..., 0] = np.clip(lp, 1, 255).astype(np.uint8) * has
    rgba[..., 1] = np.where(has, np.clip(np.round(ac_g / MAX_DIST * 255), 0, 255), 0).astype(np.uint8)
    rgba[..., 2] = np.where(has, np.clip(np.round(dc_g / MAX_DIST * 255), 0, 255), 0).astype(np.uint8)
    rgba[..., 3] = np.where(has, np.clip(np.round(ultra_g / MAX_DIST * 255), 0, 255), 0).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(rgba, "RGBA").save(buf, "PNG", optimize=False, compress_level=1)
    return buf.getvalue()


def propagate_up(z, x, y, grids, staging):
    if z <= MIN_Z:
        return
    pg, ag, dg, ug = grids
    H = TILE // 2
    p2 = pg.reshape(H, 2, H, 2)
    pop_red = p2.sum(axis=(1, 3))

    def wavg(dg):
        d = dg.reshape(H, 2, H, 2)
        m = (p2 > 0) & np.isfinite(d)
        ws = np.where(m, d * p2, 0).sum(axis=(1, 3))
        ps = np.where(m, p2, 0).sum(axis=(1, 3))
        return np.where(ps > 0, ws / ps, np.inf)

    pz = z - 1
    pk = (x // 2, y // 2)
    if pk not in staging[pz]:
        staging[pz][pk] = (
            np.zeros((TILE, TILE), np.float32),
            np.full((TILE, TILE), np.inf, np.float32),
            np.full((TILE, TILE), np.inf, np.float32),
            np.full((TILE, TILE), np.inf, np.float32),
        )
    pp, pa, pd, pu = staging[pz][pk]
    qx, qy = (x % 2) * H, (y % 2) * H
    pp[qy:qy+H, qx:qx+H] = pop_red
    pa[qy:qy+H, qx:qx+H] = wavg(ag)
    pd[qy:qy+H, qx:qx+H] = wavg(dg)
    pu[qy:qy+H, qx:qx+H] = wavg(ug)


def flush_row(z, row, staging, all_tiles):
    if z < MIN_Z:
        return
    from pmtiles.tile import zxy_to_tileid
    keys = [k for k in staging[z] if k[1] == row]
    for k in keys:
        x, y = k
        grids = staging[z].pop(k)
        png = encode_png(*grids)
        if png:
            all_tiles.append((zxy_to_tileid(z, x, y), png))
        if z > MIN_Z:
            propagate_up(z, x, y, grids, staging)
    if z > MIN_Z and row % 2 == 1:
        flush_row(z - 1, row // 2, staging, all_tiles)


def build_tiles(xm, ym, pop, d_ac, d_dc, d_ultra):
    from pmtiles.tile import zxy_to_tileid, tileid_to_zxy, TileType, Compression
    from pmtiles.writer import Writer

    fp_x0, fp_x1, fp_y0, fp_y1 = build_footprints(xm, ym)

    ty0 = fp_y0 // TILE
    ty1 = fp_y1 // TILE
    valid = (fp_x1 >= fp_x0) & (ty1 >= ty0)
    row_min = int(ty0[valid].min())
    row_max = int(ty1[valid].max())
    print(f"  tile rows: {row_min}-{row_max} ({row_max - row_min + 1} rows)")

    print("  building row index...")
    t0 = time.time()
    n_rows = row_max - row_min + 1
    row_cells = [[] for _ in range(n_rows)]
    for i in range(len(fp_y0)):
        if not valid[i]:
            continue
        r0 = max(int(ty0[i]) - row_min, 0)
        r1 = min(int(ty1[i]) - row_min, n_rows - 1)
        for r in range(r0, r1 + 1):
            row_cells[r].append(i)
    print(f"  row index in {time.time()-t0:.1f}s")

    y_start = row_min & ~1
    y_end = row_max | 1
    staging = [dict() for _ in range(MAX_Z + 1)]
    all_tiles = []
    t0 = time.time()

    print(f"  rendering z{MAX_Z}...")
    for tile_y in range(y_start, y_end + 1):
        ri = tile_y - row_min
        if 0 <= ri < n_rows and row_cells[ri]:
            idx = np.array(row_cells[ri], dtype=np.int32)
            row_tiles = render_row(tile_y, idx, fp_x0, fp_x1, fp_y0, fp_y1,
                                   pop, d_ac, d_dc, d_ultra)
            for (x, y), grids in row_tiles.items():
                png = encode_png(*grids)
                if png:
                    all_tiles.append((zxy_to_tileid(MAX_Z, x, y), png))
                propagate_up(MAX_Z, x, y, grids, staging)

        if tile_y % 2 == 1:
            flush_row(MAX_Z - 1, tile_y // 2, staging, all_tiles)

        done = tile_y - y_start + 1
        total_rows = y_end - y_start + 1
        if done % 10 == 0 or tile_y == y_end:
            print(f"    row {done}/{total_rows} | {len(all_tiles):,} tiles | {time.time()-t0:.1f}s")

    # flush remaining staging
    for z in range(MAX_Z - 1, MIN_Z - 1, -1):
        for k in list(staging[z].keys()):
            x, y = k
            grids = staging[z].pop(k)
            png = encode_png(*grids)
            if png:
                all_tiles.append((zxy_to_tileid(z, x, y), png))
            if z > MIN_Z:
                propagate_up(z, x, y, grids, staging)

    print(f"  {len(all_tiles):,} tiles total")
    all_tiles.sort(key=lambda t: t[0])
    total_bytes = sum(len(d) for _, d in all_tiles)
    print(f"  PNG data: {total_bytes / 1e6:.1f} MB")

    with open(str(OUT_PMTILES), "wb") as f:
        w = Writer(f)
        for tid, data in all_tiles:
            w.write_tile(tid, data)
        w.finalize(
            header={
                "tile_type": TileType.PNG,
                "tile_compression": Compression.NONE,
                "min_lon_e7": int(5.5e7), "min_lat_e7": int(47e7),
                "max_lon_e7": int(15.5e7), "max_lat_e7": int(55.5e7),
                "center_lon_e7": int(10.5e7), "center_lat_e7": int(51e7),
                "center_zoom": 7,
            },
            metadata={
                "name": "Germany Population + Charger Distance",
                "description": "R=pop(log2) G=dist_ac B=dist_dc A=dist_ultra",
                "format": "png",
            },
        )
    sz = OUT_PMTILES.stat().st_size / 1e6
    print(f"  → {OUT_PMTILES.name} ({sz:.1f} MB)")

    zoom_counts = {}
    for tid, _ in all_tiles:
        z = tileid_to_zxy(tid)[0]
        zoom_counts[z] = zoom_counts.get(z, 0) + 1
    for z in sorted(zoom_counts):
        print(f"    z{z}: {zoom_counts[z]:,}")


# ═══════════════════════════ main ════════════════════════════════════════════

def main():
    t_all = time.time()

    print("=" * 60)
    print("Phase 1: Extract Germany from GHS-POP TIFF")
    print("=" * 60)
    xm, ym, lo, la, po = extract_pixels()
    print(f"  {len(po):,} cells, {po.sum()/1e6:.1f}M pop")

    print(f"\n{'='*60}")
    print("Phase 2: Charger distances (3 tiers, cKDTree)")
    print("=" * 60)
    d_ac, d_dc, d_ultra = compute_distances(lo, la)
    d_any = np.minimum(np.minimum(d_ac, d_dc), d_ultra)
    print(f"  any: median {np.median(d_any):.1f} km, p95 {np.percentile(d_any, 95):.1f} km, max {d_any.max():.1f} km")

    print(f"\n{'='*60}")
    print("Phase 3: Coverage stats + boundary assignment")
    print("=" * 60)
    compute_coverage_stats(lo, la, po, d_ac, d_dc, d_ultra)

    print(f"\n{'='*60}")
    print("Phase 4: Tile pyramid → PMTiles")
    print("=" * 60)
    build_tiles(xm, ym, po, d_ac, d_dc, d_ultra)

    print(f"\nDone in {time.time() - t_all:.1f}s total")


if __name__ == "__main__":
    main()
