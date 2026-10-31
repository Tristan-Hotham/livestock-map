"""Step 4. Geometry and place names for the page: data/page/world.json (Natural Earth 1:50m countries, simplified),
data/page/uk_counties.json (UK counties, simplified), data/page/cities.json (Natural Earth populated places).
Run: python3 code/04_page_data.py"""
from shapely.geometry import shape, mapping
from common import *


def simp(feats, tol, props, nd=3):
    out = []
    for f in feats:
        g = shape(f["geometry"]).simplify(tol, preserve_topology=True)
        if g.is_empty:
            continue
        def r(c):
            if isinstance(c[0], (int, float)):
                return [round(c[0], nd), round(c[1], nd)]
            return [r(x) for x in c]
        m = mapping(g)
        out.append({"type": "Feature", "properties": props(f["properties"]), "geometry": {"type": m["type"], "coordinates": r(m["coordinates"])}})
    return {"type": "FeatureCollection", "features": out}


NE = jload(NE50)
iso = lambda p: p["ISO_A3_EH"] if p["ISO_A3_EH"] not in ("-99", None) else p["ADM0_A3"]
w = simp([f for f in NE["features"] if iso(f["properties"]) != "ATA"], .04, lambda p: {"iso": iso(p)})
jsave(w, f"{PAGE}/world.json")
u = simp(jload(f"{GEO}/counties_uk.geojson")["features"], .004, lambda p: {"n": p["county"], "nat": p["nation"]})
jsave(u, f"{PAGE}/uk_counties.json")
pl = []
for f in jload(PLACES)["features"]:
    p = f["properties"]
    if (p.get("pop_max") or 0) >= 40000 or (p.get("adm0_a3") in ("GBR", "IRL") and (p.get("pop_max") or 0) >= 8000):
        x, y = f["geometry"]["coordinates"]
        pl.append([p["name"], round(y, 3), round(x, 3), int(p["pop_max"])])
pl.sort(key=lambda r: -r[3])
jsave(pl, f"{PAGE}/cities.json")
for n in ("world.json", "uk_counties.json", "cities.json"):
    print(n, os.path.getsize(f"{PAGE}/{n}") // 1024, "KB")
