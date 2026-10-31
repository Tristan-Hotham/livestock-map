"""Step 2. The GLW 4 grids (2015): country sums, densities, livestock units, the dominant animal, concentration,
hotspots, UK counties and nations, and the coded PNG grids the page draws in the browser.

  data/page/grid_a.png  RGB = cattle, sheep, goats       (coded density, head per km2)
  data/page/grid_b.png  RGB = pigs, chickens, buffaloes
  data/page/grid_c.png  RGB = horses, ducks, livestock units per km2
  data/page/grid_d.png  RGB = dominant animal by livestock units (0 none, 1..8 in SPECIES order), country index, 0
Grids run from 85N to 60S (1740 rows) and 180W to 180E (4320 columns), 1/12 degree cells.
Code: v = 0 when d < lo, else 1 + round(254 * (log10 d - log10 lo) / (log10 hi - log10 lo)), clipped to 255.
Run: python3 code/02_grids.py"""
import numpy as np
import rasterio
from rasterio import features
from rasterio.transform import from_origin
from scipy import ndimage
from shapely.geometry import shape, Point
from PIL import Image
from common import *

F = jload(f"{WORK}/fao.json")
H, W = 2160, 4320
T = from_origin(-180, 90, 1 / 12, 1 / 12)


def grid(code):
    with rasterio.open(f"{GLW}/{code}.tif") as r:
        a = r.read(1).astype(np.float64)
    a[~np.isfinite(a) | (a < 0)] = 0
    return a


G = {k: grid(f"{c}_Da") for k, c, *_ in SPECIES}
with rasterio.open(f"{GLW}/Areakm.tif") as r:
    AREA = r.read(1).astype(np.float64)
AREA[~np.isfinite(AREA) | (AREA <= 0)] = np.nan

# ---------- country index grid ----------
NE = jload(NE50)
ISOS = []
shapes = []
for f in NE["features"]:
    p = f["properties"]
    iso = p["ISO_A3_EH"] if p["ISO_A3_EH"] not in ("-99", None) else p["ADM0_A3"]
    if iso not in ISOS:
        ISOS.append(iso)
    shapes.append((f["geometry"], ISOS.index(iso) + 1))
assert len(ISOS) < 255
CID = features.rasterize(shapes, out_shape=(H, W), transform=T, fill=0, dtype=np.uint8)
tot = sum(G.values())
# cells with animals but outside every outline (coasts, small islands): give them the nearest country
miss = (CID == 0) & (tot > 0)
_, (ri, ci) = ndimage.distance_transform_edt(CID == 0, return_indices=True)
CIDF = CID.copy()
CIDF[miss] = CID[ri[miss], ci[miss]]
print("cells with animals outside outlines:", int(miss.sum()), "share of cattle there:", round(G["cattle"][miss].sum() / G["cattle"].sum() * 100, 3), "%")

# ---------- country sums of the grid ----------
gsum = {}
for k in SKEYS:
    s = np.bincount(CIDF.ravel(), weights=G[k].ravel(), minlength=len(ISOS) + 1)
    for i, iso in enumerate(ISOS):
        if s[i + 1] > 0:
            gsum.setdefault(iso, {})[k] = float(s[i + 1])
gworld = {k: float(G[k].sum()) for k in SKEYS}

# ---------- livestock units ----------
coef_c = {k: np.full(len(ISOS) + 1, F["world_coef"].get(k if k != "ducks" else "chickens", 0.01)) for k in SKEYS}
for i, iso in enumerate(ISOS):
    cc = F["lsu_coef"].get(iso, {})
    for k in SKEYS:
        kk = "chickens" if k == "ducks" else k
        if kk in cc:
            coef_c[k][i + 1] = cc[kk]
LSU = {k: G[k] * coef_c[k][CIDF] for k in SKEYS}
LTOT = sum(LSU.values())
stack = np.stack([LSU[k] for k in SKEYS])
DOM = (np.argmax(stack, axis=0) + 1).astype(np.uint8)
DOM[LTOT < 1e-9] = 0
area0 = np.nan_to_num(AREA)
dens_l = np.where(area0 > 0, LTOT / np.where(area0 > 0, area0, 1), 0)
DOM[dens_l < 1] = 0                                       # fewer than one livestock unit per km2: shown as empty
land = (CID > 0) & (area0 > 0) & ~((CID == ISOS.index("ATA") + 1) if "ATA" in ISOS else False)
land_area = float(area0[land].sum())
dom_area = {k: float(area0[land & (DOM == i + 1)].sum()) for i, k in enumerate(SKEYS)}
dom_lsu = {k: float(LTOT[DOM == i + 1].sum()) for i, k in enumerate(SKEYS)}
empty_area = float(area0[land & (DOM == 0)].sum())
print("dominant by area", {k: round(v / land_area * 100, 1) for k, v in dom_area.items()}, "empty", round(empty_area / land_area * 100, 1))

# ---------- concentration: the least land that holds half and 90% of each species ----------
conc = {}
for k in SKEYS + ["lsu"]:
    a = LTOT if k == "lsu" else G[k]
    m = land & (a > 0)
    d = a[m] / area0[m]
    o = np.argsort(-d)
    ca = np.cumsum(area0[m][o])
    cn = np.cumsum(a[m][o])
    tn = a[land].sum()
    r = {}
    for q in (50, 90):
        j = np.searchsorted(cn, tn * q / 100)
        r[f"land{q}_pct"] = float(ca[min(j, len(ca) - 1)] / land_area * 100)
    r["none_pct"] = float(area0[land & (a / np.where(area0 > 0, area0, 1) < 1)].sum() / land_area * 100)   # under one animal per km2
    conc[k] = r
print({k: {kk: round(v, 2) for kk, v in r.items()} for k, r in conc.items()})

# ---------- hotspots: densest cell for each species, named by the nearest big place ----------
PL = jload(PLACES)["features"]
pl = np.array([[f["geometry"]["coordinates"][0], f["geometry"]["coordinates"][1], f["properties"].get("pop_max") or 0] for f in PL])
pn = [f["properties"]["name"] for f in PL]
pc = [f["properties"].get("adm0_a3") for f in PL]


def near(lat, lon, minpop=50000):
    ok = pl[:, 2] >= minpop
    d = (pl[:, 1] - lat) ** 2 + ((pl[:, 0] - lon) * np.cos(np.radians(lat))) ** 2
    d[~ok] = 1e9
    j = int(np.argmin(d))
    return pn[j], float(np.sqrt(d[j]) * 111.2)


hot = {}
for k in SKEYS:
    d = np.where(land, G[k] / np.where(area0 > 0, area0, 1), 0)
    # smooth over 3 x 3 cells so that a single odd cell is not the 'hotspot'
    ds = ndimage.uniform_filter(d, 3)
    r, c = np.unravel_index(np.argmax(ds), ds.shape)
    lat, lon = 90 - (r + .5) / 12, -180 + (c + .5) / 12
    nm, km = near(lat, lon)
    hot[k] = {"lat": round(lat, 3), "lon": round(lon, 3), "dens": float(ds[r, c]), "iso": ISOS[CIDF[r, c] - 1], "near": nm, "km": round(km)}
print("hotspots", hot)

# ---------- the UK: counties and nations (cell fractions from a 1/120 degree rasterisation) ----------
UKC = jload(f"{GEO}/counties_uk.geojson")["features"]
r0, r1, c0, c1 = int((90 - 61) * 12), int((90 - 49.8) * 12), int((180 - 8.7) * 12), int((180 + 2) * 12)
sub = 10
Tf = from_origin(-180 + c0 / 12, 90 - r0 / 12, 1 / 120, 1 / 120)
fine = features.rasterize([(f["geometry"], i + 1) for i, f in enumerate(UKC)], out_shape=((r1 - r0) * sub, (c1 - c0) * sub), transform=Tf, fill=0, dtype=np.int16)
nU = len(UKC)
frac = np.zeros((nU + 1, r1 - r0, c1 - c0))
for i in range(nU + 1):
    frac[i] = (fine == i).reshape(r1 - r0, sub, c1 - c0, sub).mean(axis=(1, 3))
# animals in GBR cells: share among counties by area fraction (cells half in the sea keep their animals on land)
gbr = CIDF[r0:r1, c0:c1] == ISOS.index("GBR") + 1
landfrac = frac[1:].sum(axis=0)
uk = []
for i, f in enumerate(UKC):
    w = np.where(gbr & (landfrac > 0), frac[i + 1] / np.where(landfrac > 0, landfrac, 1), 0)
    e = {"name": f["properties"]["county"], "nation": f["properties"]["nation"]}
    e["area_km2"] = float((frac[i + 1] * area0[r0:r1, c0:c1]).sum())
    for k in SKEYS:
        e[k] = float((G[k][r0:r1, c0:c1] * w).sum())
    e["lsu"] = float((LTOT[r0:r1, c0:c1] * w).sum())
    lk = {k: float((LSU[k][r0:r1, c0:c1] * w).sum()) for k in SKEYS}
    e["dom"] = max(lk, key=lk.get)
    e["lsu_share"] = {k: round(v / e["lsu"] * 100, 1) for k, v in lk.items()} if e["lsu"] else {}
    uk.append(e)
ukg = sum(gsum["GBR"][k] for k in ("sheep",))
print("UK sheep: counties", round(sum(e["sheep"] for e in uk)), "country", round(ukg))

# ---------- page grids ----------
R0, R1 = int((90 - 85) * 12), int((90 + 60) * 12)
RANGE = {"cattle": (0.1, 1000), "buffalo": (0.1, 1000), "sheep": (0.1, 1000), "goats": (0.1, 1000), "pigs": (0.1, 3000),
         "chickens": (1, 100000), "ducks": (1, 30000), "horses": (0.01, 100), "lsu": (0.1, 1000)}


def code(d, lo, hi):
    v = 1 + np.round(254 * (np.log10(np.maximum(d, 1e-12)) - np.log10(lo)) / (np.log10(hi) - np.log10(lo)))
    v = np.clip(v, 1, 255)
    v[d < lo] = 0
    return v.astype(np.uint8)


def dens(a):
    return np.where(area0 > 0, a / np.where(area0 > 0, area0, 1), 0)[R0:R1]


C = {k: code(dens(G[k]), *RANGE[k]) for k in SKEYS}
C["lsu"] = code(dens(LTOT), *RANGE["lsu"])
for name, keys in (("grid_a", ["cattle", "sheep", "goats"]), ("grid_b", ["pigs", "chickens", "buffalo"]), ("grid_c", ["horses", "ducks", "lsu"])):
    Image.fromarray(np.dstack([C[k] for k in keys]), "RGB").save(f"{PAGE}/{name}.png", optimize=True)
Image.fromarray(np.dstack([DOM[R0:R1], CIDF[R0:R1], np.zeros_like(DOM[R0:R1])]), "RGB").save(f"{PAGE}/grid_d.png", optimize=True)
for n in ("grid_a", "grid_b", "grid_c", "grid_d"):
    print(n, os.path.getsize(f"{PAGE}/{n}.png") // 1024, "KB")

# ---------- data/grid_country_2015.csv: what the grid holds per country ----------
import csv
with open(f"{DATA}/grid_country_2015.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["iso3", "country"] + [f"{k}_2015_grid" for k in SKEYS] + ["livestock_units_grid", "dominant_by_lsu"])
    lsum = np.bincount(CIDF.ravel(), weights=LTOT.ravel(), minlength=len(ISOS) + 1)
    for i, iso in enumerate(ISOS):
        if iso not in gsum:
            continue
        nm = F["countries"].get(iso, {}).get("name", iso)
        lk = {k: gsum[iso].get(k, 0) * coef_c[k][i + 1] for k in SKEYS}
        w.writerow([iso, nm] + [round(gsum[iso].get(k, 0)) for k in SKEYS] + [round(lsum[i + 1]), max(lk, key=lk.get)])
with open(f"{DATA}/uk_counties_2015.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["county", "nation", "area_km2"] + [f"{k}_2015" for k in SKEYS] + ["livestock_units", "dominant_by_lsu"])
    for e in sorted(uk, key=lambda e: (e["nation"], e["name"])):
        w.writerow([e["name"], e["nation"], round(e["area_km2"])] + [round(e[k]) for k in SKEYS] + [round(e["lsu"]), e["dom"]])

jsave({"isos": ISOS, "gsum": gsum, "gworld": gworld, "land_area": land_area, "dom_area": dom_area, "dom_lsu": dom_lsu, "empty_area": empty_area,
       "conc": conc, "hot": hot, "uk": uk, "range": RANGE, "rows": [R0, R1], "lsu_world": float(LTOT.sum()),
       "coef_used": {k: {ISOS[i]: float(coef_c[k][i + 1]) for i in range(len(ISOS))} for k in SKEYS},
       "outside_cells": int(miss.sum())}, f"{WORK}/grids.json")
print("done")
