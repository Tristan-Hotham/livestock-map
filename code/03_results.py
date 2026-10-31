"""Step 3. data/results.json (every number quoted anywhere), data/site.json (embedded in the page),
data/page/series.json (country time series, loaded by the page), data/country_summary.csv.
Run: python3 code/03_results.py"""
import csv
import numpy as np
from common import *

F = jload(f"{WORK}/fao.json")
GR = jload(f"{WORK}/grids.json")
Y1 = F["last"]; Y0 = F["years"][0]
C = F["countries"]; S = F["series"]; P = F["pop"]; WD = F["world"]
yk = lambda d, y: (d or {}).get(str(y))
ALL = list(FAO_ITEMS.values())
LIVE = [s for s in ALL if s != "bees"]


def val(iso, sp, y=Y1):
    return yk(S.get(iso, {}).get(sp), y) or 0.0


def pop(iso, y=Y1):
    return yk(P.get(iso), y)


R = {"meta": {"page": URL, "repo": REPO, "slug": SLUG, "retrieved": RETRIEVED, "last": Y1, "first": Y0, "lsu_year": F["lsu_year"], "glw_year": 2015}}

# ---------- world ----------
wpop = F["world_pop"][str(Y1)]
w = {}
for sp in ALL:
    a, b = yk(WD.get(sp), Y0), yk(WD.get(sp), Y1)
    w[sp] = {"n": b, "n0": a, "x": (b / a) if a else None, "pp": b / wpop}
R["world"] = {"sp": w, "pop": wpop, "pop0": F["world_pop"][str(Y0)], "pop_x": wpop / F["world_pop"][str(Y0)]}
mam = sum(w[s]["n"] for s in MAMMALS)
bird = sum(w[s]["n"] for s in BIRDS)
R["world"].update({"mammals": mam, "birds": bird, "animals": sum(w[s]["n"] for s in LIVE), "mammals_pp": mam / wpop, "birds_pp": bird / wpop,
                   "mammals0": sum(w[s]["n0"] or 0 for s in MAMMALS), "chick_share_birds": w["chickens"]["n"] / bird * 100,
                   "animals_pp": sum(w[s]["n"] for s in LIVE) / wpop})
R["world"]["mammals_x"] = mam / R["world"]["mammals0"]
R["world"]["cattle_pp0"] = w["cattle"]["n0"] / R["world"]["pop0"]
R["world"]["cattle_pp"] = w["cattle"]["n"] / wpop
# biggest climbers, 1961 to last year (species with a 1961 figure)
xs = sorted([(sp, w[sp]["x"]) for sp in LIVE if w[sp]["x"]], key=lambda t: -t[1])
R["world"]["growth"] = [{"sp": sp, "label": FAO_LABEL[sp], "x": x, "n0": w[sp]["n0"], "n": w[sp]["n"]} for sp, x in xs]
# pigs: peak and the 2019 fall (African swine fever in China)
pw = {int(y): v for y, v in WD["pigs"].items()}
pk = max(pw, key=pw.get)
R["pigs"] = {"peak_year": pk, "peak": pw[pk], "y2018": pw[2018], "y2019": pw[2019], "fall_pct": (1 - pw[2019] / pw[2018]) * 100, "last": pw[Y1]}
cp = S["CHN"]["pigs"]
R["pigs"].update({"chn2018": cp["2018"], "chn2019": cp["2019"], "chn_fall_pct": (1 - cp["2019"] / cp["2018"]) * 100, "chn_last": cp[str(Y1)],
                  "chn_fall_n": cp["2018"] - cp["2019"]})
# regions: where the chickens and goats went
RG = F["regions"]
R["regions"] = {r: {sp: {"n0": yk(d.get(sp), Y0), "n": yk(d.get(sp), Y1)} for sp in ("chickens", "cattle", "goats", "pigs", "sheep")} for r, d in RG.items()}
R["chick_asia_share"] = R["regions"]["Asia"]["chickens"]["n"] / w["chickens"]["n"] * 100
R["chick_asia_share0"] = R["regions"]["Asia"]["chickens"]["n0"] / w["chickens"]["n0"] * 100
R["goats_afr_asia_share"] = (R["regions"]["Asia"]["goats"]["n"] + R["regions"]["Africa"]["goats"]["n"]) / w["goats"]["n"] * 100
R["sheep_eu_share0"] = R["regions"]["Europe"]["sheep"]["n0"] / w["sheep"]["n0"] * 100
R["sheep_eu_share"] = R["regions"]["Europe"]["sheep"]["n"] / w["sheep"]["n"] * 100

# ---------- countries: concentration ----------
isos = [i for i in S if i in C]
conc = {}
for sp in LIVE:
    rows = sorted([(i, val(i, sp)) for i in isos if val(i, sp) > 0], key=lambda t: -t[1])
    tot = w[sp]["n"]
    conc[sp] = {"n_countries": len(rows), "top": [{"iso": i, "name": C[i]["name"], "n": v, "pct": v / tot * 100} for i, v in rows[:8]]}
    conc[sp]["top1_pct"] = conc[sp]["top"][0]["pct"]
    conc[sp]["top3_pct"] = sum(t["pct"] for t in conc[sp]["top"][:3])
R["conc"] = conc

# ---------- per person: where animals outnumber people ----------
pp = {}
MINPOP = 1_000_000
for sp in ["cattle", "sheep", "goats", "pigs", "chickens", "buffalo", "camels", "horses"]:
    rows = []
    for i in isos:
        p = pop(i)
        if p and val(i, sp) > 0:
            rows.append((i, val(i, sp) / p, p))
    big = sorted([r for r in rows if r[2] >= MINPOP], key=lambda t: -t[1])
    pp[sp] = {"more_than_people": sorted([C[i]["name"] for i, x, p in rows if x > 1 and p >= MINPOP]),
              "n_more": sum(1 for i, x, p in rows if x > 1 and p >= MINPOP),
              "top": [{"iso": i, "name": C[i]["name"], "pp": x} for i, x, p in big[:10]],
              "top_any": [{"iso": i, "name": C[i]["name"], "pp": x, "pop": p} for i, x, p in sorted(rows, key=lambda t: -t[1])[:5]]}
R["pp"] = pp
# all grazing and farm mammals per person
mrows = []
for i in isos:
    p = pop(i)
    if p and p >= MINPOP:
        m = sum(val(i, s) for s in MAMMALS)
        mrows.append((i, m / p))
mrows.sort(key=lambda t: -t[1])
R["mam_pp"] = {"n_more": sum(1 for i, x in mrows if x > 1), "n_countries": len(mrows), "top": [{"iso": i, "name": C[i]["name"], "pp": x} for i, x in mrows[:12]],
               "min": [{"iso": i, "name": C[i]["name"], "pp": x} for i, x in mrows[-5:]]}
# New Zealand and the sheep peak
nz = {int(y): v for y, v in S["NZL"]["sheep"].items()}
nzp = {int(y): v for y, v in P["NZL"].items()}
nk = max(nz, key=nz.get)
R["nz"] = {"peak_year": nk, "peak": nz[nk], "peak_pp": nz[nk] / nzp[nk], "last": nz[Y1], "last_pp": nz[Y1] / nzp[Y1], "fall_pct": (1 - nz[Y1] / nz[nk]) * 100,
           "cattle_last": val("NZL", "cattle"), "cattle_x_since_peak": val("NZL", "cattle") / S["NZL"]["cattle"][str(nk)]}
mn = {sp: val("MNG", sp) for sp in MAMMALS}
R["mongolia"] = {"pop": pop("MNG"), "mammals": sum(mn.values()), "pp": sum(mn.values()) / pop("MNG"), "goats": mn["goats"], "sheep": mn["sheep"],
                 "goats_x": val("MNG", "goats") / S["MNG"]["goats"][str(Y0)], "goats0": S["MNG"]["goats"][str(Y0)]}

# ---------- livestock units per country and the main animal ----------
coef = F["lsu_coef"]; wc = F["world_coef"]
LSP = ["cattle", "buffalo", "sheep", "goats", "pigs", "chickens", "ducks", "horses", "camels", "asses", "mules"]


def lsu(i, sp, y=Y1):
    k = "chickens" if sp in ("ducks",) else sp
    c = coef.get(i, {}).get(k, wc.get(k, 0.01 if k == "chickens" else 0))
    return val(i, sp, y) * c


main = {}
for i in isos:
    l = {sp: lsu(i, sp) for sp in LSP}
    t = sum(l.values())
    if t > 0:
        m = max(l, key=l.get)
        main[i] = {"main": m, "share": l[m] / t * 100, "lsu": t, "lsu_by": {k: v for k, v in l.items() if v > 0}}
from collections import Counter
mc = Counter(v["main"] for v in main.values())
R["main"] = {"counts": dict(mc), "n": len(main)}
wl = {sp: sum(lsu(i, sp) for i in isos) for sp in LSP}
wt = sum(wl.values())
R["lsu_world"] = {"total": wt, "share": {k: v / wt * 100 for k, v in wl.items()}}

# densities on agricultural land
land = F["land"]
dl = []
for i in isos:
    a = land.get(i, {}).get("agri_km2")
    if a and a > 1000 and i in main:
        dl.append((i, main[i]["lsu"] / a))
dl.sort(key=lambda t: -t[1])
R["lsu_density"] = {"top": [{"iso": i, "name": C[i]["name"], "per_km2": x} for i, x in dl[:10]]}

# ---------- the grid (2015) ----------
gw = GR["gworld"]
R["grid"] = {"world": gw, "vs_fao2015": {sp: gw[sp] / WD[sp]["2015"] * 100 for sp in SKEYS},
             "conc": GR["conc"], "hot": GR["hot"], "land_area": GR["land_area"],
             "dom_pct": {k: v / GR["land_area"] * 100 for k, v in GR["dom_area"].items()},
             "empty_pct": GR["empty_area"] / GR["land_area"] * 100, "range": GR["range"]}
R["grid"]["coef"] = F["world_coef"]
R["grid"]["dom_lsu_pct"] = {k: v / sum(GR["dom_lsu"].values()) * 100 for k, v in GR["dom_lsu"].items()}

# ---------- Britain and Ireland ----------
uk = GR["uk"]
nat = {}
for e in uk:
    n = nat.setdefault(e["nation"], {k: 0.0 for k in SKEYS + ["lsu", "area_km2"]})
    for k in SKEYS + ["lsu", "area_km2"]:
        n[k] += e[k]
uks = {k: sum(n[k] for n in nat.values()) for k in SKEYS + ["lsu", "area_km2"]}
R["uk"] = {"nations": {k: {**v, "sheep_share": v["sheep"] / uks["sheep"] * 100, "cattle_share": v["cattle"] / uks["cattle"] * 100,
                           "pigs_share": v["pigs"] / uks["pigs"] * 100, "chickens_share": v["chickens"] / uks["chickens"] * 100,
                           "sheep_km2": v["sheep"] / v["area_km2"], "cattle_km2": v["cattle"] / v["area_km2"]} for k, v in nat.items()},
           "total": uks}
for k in ("sheep", "cattle", "pigs", "chickens"):
    top = sorted(uk, key=lambda e: -e[k] / max(e["area_km2"], 1))
    top = [e for e in top if e["area_km2"] > 300]
    R["uk"][f"top_{k}_km2"] = [{"name": e["name"], "nation": e["nation"], "per_km2": e[k] / e["area_km2"], "n": e[k]} for e in top[:6]]
    tn = sorted(uk, key=lambda e: -e[k])
    R["uk"][f"top_{k}_n"] = [{"name": e["name"], "nation": e["nation"], "n": e[k], "share": e[k] / uks[k] * 100} for e in tn[:5]]
dc = Counter(e["dom"] for e in uk)
R["uk"]["dom_counties"] = dict(dc)
R["uk"]["n_counties"] = len(uk)
R["uk"]["fao"] = {sp: val("GBR", sp) for sp in ("cattle", "sheep", "pigs", "chickens", "goats", "horses", "ducks", "turkeys")}
R["uk"]["pop"] = pop("GBR")
R["uk"]["sheep_pp"] = val("GBR", "sheep") / pop("GBR")
R["uk"]["sheep0"] = S["GBR"]["sheep"][str(Y0)]
R["uk"]["chick0"] = S["GBR"]["chickens"][str(Y0)]
R["uk"]["chick_x"] = val("GBR", "chickens") / S["GBR"]["chickens"][str(Y0)]
uks_peak = {int(y): v for y, v in S["GBR"]["sheep"].items()}
R["uk"]["sheep_peak_year"] = max(uks_peak, key=uks_peak.get); R["uk"]["sheep_peak"] = max(uks_peak.values())
eu = sorted([(val(i, "sheep"), i) for i in isos if C[i]["cont"] == "Europe"], reverse=True)
R["uk"]["sheep_eu_rank"] = 1 + [i for v, i in eu].index("GBR")
R["uk"]["sheep_eu_next"] = {"name": C[eu[1][1]]["name"], "n": eu[1][0]}
R["uk"]["tur_sheep"] = val("TUR", "sheep")
R["uk"]["wales_area_share"] = nat["Wales"]["area_km2"] / uks["area_km2"] * 100
R["uk"]["wales_sheep_x_england"] = (nat["Wales"]["sheep"] / nat["Wales"]["area_km2"]) / (nat["England"]["sheep"] / nat["England"]["area_km2"])
R["ireland"] = {"cattle": val("IRL", "cattle"), "pop": pop("IRL"), "cattle_pp": val("IRL", "cattle") / pop("IRL"), "sheep": val("IRL", "sheep"),
                "cattle_lsu_share": main["IRL"]["lsu_by"]["cattle"] / main["IRL"]["lsu"] * 100}
R["uk"]["main"] = main["GBR"]["main"]; R["uk"]["main_share"] = main["GBR"]["share"]
R["uk"]["lsu_share"] = {k: v / main["GBR"]["lsu"] * 100 for k, v in main["GBR"]["lsu_by"].items()}
R["n_countries"] = len(isos)
WLU = F["world_land"]
R["land"] = {"agri_km2": WLU["agri_km2"], "pasture_km2": WLU["pasture_km2"], "pasture_share": WLU["pasture_km2"] / WLU["agri_km2"] * 100}
R["unmatched"] = F["unmatched"]

# ---------- site.json (embedded) and series.json (lazy) ----------
site = {"species": [[k, lab, pl, col] for k, _, lab, pl, col, _ in SPECIES], "label": FAO_LABEL, "last": Y1, "first": Y0, "years": F["years"],
        "range": GR["range"], "isos": GR["isos"], "c": {}}
for i in C:
    e = {"n": C[i]["name"]}
    if i in isos:
        e["v"] = {sp: round(val(i, sp)) for sp in ALL if val(i, sp) > 0}
    if pop(i):
        e["p"] = round(pop(i))
    if land.get(i, {}).get("land_km2"):
        e["a"] = round(land[i]["land_km2"])
    if land.get(i, {}).get("agri_km2"):
        e["g"] = round(land[i]["agri_km2"])
    if i in main:
        e["m"] = main[i]["main"]; e["ms"] = round(main[i]["share"], 1); e["l"] = round(main[i]["lsu"])
        e["lb"] = {k: round(v / main[i]["lsu"] * 100, 1) for k, v in main[i]["lsu_by"].items()}
    if i in GR["gsum"]:
        e["gr"] = {k: round(v) for k, v in GR["gsum"][i].items()}
    site["c"][i] = e
site["world"] = {sp: round(w[sp]["n"]) for sp in ALL}
site["wpop"] = round(wpop)
site["uk"] = [{"n": e["name"], "nat": e["nation"], "a": round(e["area_km2"]), **{k: round(e[k]) for k in SKEYS}, "l": round(e["lsu"]), "d": e["dom"]} for e in uk]
jsave(site, f"{DATA}/site.json")
ser = {"years": F["years"], "c": {}}
for i in isos:
    ser["c"][i] = {sp: [None if yk(S[i][sp], y) is None else round(yk(S[i][sp], y)) for y in F["years"]] for sp in S[i] if any(S[i][sp].values())}
    if i in P:
        ser["c"][i]["_pop"] = [None if yk(P[i], y) is None else round(yk(P[i], y)) for y in F["years"]]
ser["c"]["WLD"] = {sp: [None if yk(WD.get(sp), y) is None else round(yk(WD.get(sp), y)) for y in F["years"]] for sp in ALL}
ser["c"]["WLD"]["_pop"] = [round(F["world_pop"][str(y)]) for y in F["years"]]
jsave(ser, f"{PAGE}/series.json")

with open(f"{DATA}/country_summary.csv", "w", newline="", encoding="utf-8") as f:
    wr = csv.writer(f)
    wr.writerow(["iso3", "country", f"population_{Y1}", "land_km2", "agricultural_land_km2"] + [f"{sp}_{Y1}" for sp in LIVE] +
                [f"{sp}_per_person" for sp in ("cattle", "sheep", "goats", "pigs", "chickens")] + ["livestock_units", "main_animal_by_lsu", "main_animal_lsu_share_pct"])
    for i in sorted(isos, key=lambda i: C[i]["name"]):
        p = pop(i)
        wr.writerow([i, C[i]["name"], round(p) if p else "", round(land.get(i, {}).get("land_km2", 0)) or "", round(land.get(i, {}).get("agri_km2", 0)) or ""] +
                    [round(val(i, sp)) for sp in LIVE] + [(round(val(i, sp) / p, 3) if p else "") for sp in ("cattle", "sheep", "goats", "pigs", "chickens")] +
                    [round(main[i]["lsu"]) if i in main else "", main.get(i, {}).get("main", ""), round(main[i]["share"], 1) if i in main else ""])
jsave(R, f"{DATA}/results.json", indent=1)
print(json.dumps({k: R[k] for k in ("world",)}, indent=0)[:3000])
