"""Step 1. FAOSTAT livestock numbers, livestock units and land use, World Bank population, matched to Natural Earth countries.
Writes WORK/fao.json (country and world series) and data/country_stocks.csv (head by country, species and year, wide).
Run: python3 code/01_fao.py"""
import csv
import numpy as np
import pandas as pd
from common import *

# ---------- countries (Natural Earth 1:50m) ----------
NE = jload(NE50)
countries = {}
n3iso = {}
for f in NE["features"]:
    p = f["properties"]
    iso = p["ISO_A3_EH"] if p["ISO_A3_EH"] not in ("-99", None) else p["ADM0_A3"]
    if iso in countries:
        continue
    countries[iso] = {"iso": iso, "name": p["NAME"], "cont": p["CONTINENT"], "sub": p["SUBREGION"], "ne_pop": p["POP_EST"]}
    n3 = p["ISO_N3_EH"] if p["ISO_N3_EH"] not in ("-99", None) else p["ISO_N3"]
    if n3 not in ("-99", None):
        n3iso[int(n3)] = iso
FIX = {"China; mainland": "CHN", "Sudan": "SDN", "Ethiopia": "ETH", "Belgium": "BEL", "Serbia": "SRB", "Montenegro": "MNE",
       "Norway": "NOR", "France": "FRA", "Kosovo": "XKX"}
NAMEFIX = {"United States of America": "United States", "Dem. Rep. Congo": "DR Congo", "Central African Rep.": "Central African Republic",
           "Dominican Rep.": "Dominican Republic", "Bosnia and Herz.": "Bosnia and Herzegovina", "S. Sudan": "South Sudan",
           "Eq. Guinea": "Equatorial Guinea", "Solomon Is.": "Solomon Islands", "Falkland Is.": "Falkland Islands",
           "Fr. S. Antarctic Lands": "French Southern Lands", "W. Sahara": "Western Sahara", "N. Cyprus": "Northern Cyprus",
           "Cook Is.": "Cook Islands", "Marshall Is.": "Marshall Islands", "Faeroe Is.": "Faroe Islands", "Cayman Is.": "Cayman Islands",
           "Turks and Caicos Is.": "Turks and Caicos Islands", "British Virgin Is.": "British Virgin Islands", "U.S. Virgin Is.": "US Virgin Islands",
           "N. Mariana Is.": "Northern Mariana Islands", "St. Vin. and Gren.": "St Vincent and the Grenadines", "St. Kitts and Nevis": "St Kitts and Nevis",
           "St. Lucia": "St Lucia", "Antigua and Barb.": "Antigua and Barbuda", "Fr. Polynesia": "French Polynesia", "Wallis and Futuna Is.": "Wallis and Futuna",
           "St. Pierre and Miquelon": "St Pierre and Miquelon", "Heard I. and McDonald Is.": "Heard and McDonald Islands", "Br. Indian Ocean Ter.": "British Indian Ocean Territory",
           "S. Geo. and the Is.": "South Georgia", "São Tomé and Principe": "São Tomé and Príncipe", "Côte d'Ivoire": "Côte d'Ivoire",
           "eSwatini": "Eswatini", "Macedonia": "North Macedonia", "Czechia": "Czechia", "Timor-Leste": "Timor-Leste"}
for c in countries.values():
    c["name"] = NAMEFIX.get(c["name"], c["name"])


def fao_iso(area_code, m49, area):
    if area_code >= 5000 or area_code == 351:          # aggregates and 'China' (mainland + Taiwan + HK + Macao)
        return None
    if area in FIX and FIX[area] in countries:
        return FIX[area]
    try:
        n = int(str(m49).strip("'"))
    except ValueError:
        return None
    return n3iso.get(n)


def read(path, keep):
    out = []
    for ch in pd.read_csv(path, encoding="latin1", chunksize=2_000_000,
                          usecols=["Area Code", "Area Code (M49)", "Area", "Item Code", "Item", "Element", "Element Code", "Year", "Unit", "Value", "Flag"]):
        out.append(ch[keep(ch)])
    return pd.concat(out)


# ---------- stocks ----------
st = read(f"{FAO}/Production_Crops_Livestock_E_All_Data_(Normalized).csv", lambda c: (c["Element"] == "Stocks") & c["Item Code"].isin(FAO_ITEMS))
st = st[st["Value"].notna()]
st["head"] = np.where(st["Unit"] == "1000 An", st["Value"] * 1000, st["Value"])
st["sp"] = st["Item Code"].map(FAO_ITEMS)
YEARS = list(range(int(st.Year.min()), int(st.Year.max()) + 1))
Y1 = YEARS[-1]
world = {sp: {int(y): float(v) for y, v in g[["Year", "head"]].values} for sp, g in st[st["Area Code"] == 5000].groupby("sp")}
REG = {5100: "Africa", 5203: "Northern America", 5204: "Central America", 5206: "Caribbean", 5207: "South America", 5300: "Asia",
       5302: "Eastern Asia", 5303: "Southern Asia", 5400: "Europe", 5500: "Oceania", 5707: "European Union"}
regions = {REG[a]: {sp: {int(y): float(v) for y, v in g[["Year", "head"]].values} for sp, g in d.groupby("sp")}
           for a, d in st[st["Area Code"].isin(REG)].groupby("Area Code")}
st["iso"] = [fao_iso(a, m, n) for a, m, n in zip(st["Area Code"], st["Area Code (M49)"], st["Area"])]
unmatched = sorted(set(st.loc[st.iso.isna() & (st["Area Code"] < 5000) & (st["Area Code"] != 351), "Area"]))
print("FAO areas without a Natural Earth country (former states and tiny territories):", unmatched)
cs = st[st.iso.notna()]
dup = cs.groupby(["iso", "sp", "Year"]).size()
assert dup.max() == 1, dup[dup > 1].head()
series = {}
for (iso, sp), g in cs.groupby(["iso", "sp"]):
    series.setdefault(iso, {})[sp] = {int(y): float(v) for y, v in g[["Year", "head"]].values}
fao_name = {iso: a for iso, a in cs[["iso", "Area"]].drop_duplicates().values}

# ---------- livestock units (FAOSTAT EK: stocks expressed in LSU) ----------
ek = read(f"{FAO}/Environment_LivestockPatterns_E_All_Data_(Normalized).csv", lambda c: c["Element Code"] == 5118)
EKY = int(ek.Year.max())
ek["sp"] = ek["Item Code"].map(FAO_ITEMS)
ek = ek[ek.sp.notna()]
ek["iso"] = [fao_iso(a, m, n) for a, m, n in zip(ek["Area Code"], ek["Area Code (M49)"], ek["Area"])]
lsu_coef = {}
for (iso, sp), g in ek[ek.iso.notna()].groupby(["iso", "sp"]):
    g = g.sort_values("Year")
    for y, v in g[["Year", "Value"]].values[::-1]:
        h = series.get(iso, {}).get(sp, {}).get(int(y))
        if h and h > 0 and v > 0:
            lsu_coef.setdefault(iso, {})[sp] = round(float(v) / h, 4)
            break
wl = ek[(ek["Area Code"] == 5000) & (ek.Year == EKY)]
world_coef = {sp: float(v) / world[sp][EKY] for sp, v in wl[["sp", "Value"]].values}
print("world LSU per head", EKY, {k: round(v, 3) for k, v in world_coef.items()})

# ---------- land ----------
lu = read(f"{FAO}/Inputs_LandUse_E_All_Data_(Normalized).csv", lambda c: c["Item Code"].isin([6601, 6610, 6655]) & (c["Element Code"] == 5110))
lu["iso"] = [fao_iso(a, m, n) for a, m, n in zip(lu["Area Code"], lu["Area Code (M49)"], lu["Area"])]
land = {}
LUK = {6601: "land_km2", 6610: "agri_km2", 6655: "pasture_km2"}
for (iso, item), g in lu[lu.iso.notna()].groupby(["iso", "Item Code"]):
    g = g[g.Value.notna()].sort_values("Year")
    if len(g):
        land.setdefault(iso, {})[LUK[item]] = float(g.Value.values[-1]) * 10   # 1000 ha to km2
        land[iso][LUK[item] + "_year"] = int(g.Year.values[-1])
wlu = lu[lu["Area Code"] == 5000]
world_land = {LUK[i]: float(g.sort_values("Year").Value.values[-1]) * 10 for i, g in wlu.groupby("Item Code")}

# ---------- population (World Bank) ----------
pop = {}
wpop = {}
with open(WB, encoding="utf-8") as f:
    for r in csv.DictReader(f):
        y = int(r["Year"])
        if r["Country Code"] == "WLD":
            wpop[y] = float(r["Value"])
        iso = {"XKX": "XKX"}.get(r["Country Code"], r["Country Code"])
        if iso in countries:
            pop.setdefault(iso, {})[y] = float(r["Value"])

out = {"years": YEARS, "last": Y1, "lsu_year": EKY, "world": world, "regions": regions, "series": series, "countries": countries,
       "fao_name": fao_name, "lsu_coef": lsu_coef, "world_coef": world_coef, "land": land, "world_land": world_land,
       "pop": pop, "world_pop": wpop, "unmatched": unmatched}
jsave(out, f"{WORK}/fao.json")

# ---------- data/country_stocks.csv ----------
with open(f"{DATA}/country_stocks.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["iso3", "country", "species", "unit"] + YEARS)
    for iso in sorted(series, key=lambda i: countries[i]["name"]):
        for sp in FAO_ITEMS.values():
            s = series[iso].get(sp)
            if not s or not any(s.values()):
                continue
            w.writerow([iso, countries[iso]["name"], sp, "hives" if sp == "bees" else "head"] + [("" if s.get(y) is None else round(s[y])) for y in YEARS])
    for sp in FAO_ITEMS.values():
        s = world.get(sp, {})
        w.writerow(["WLD", "World", sp, "hives" if sp == "bees" else "head"] + [("" if s.get(y) is None else round(s[y])) for y in YEARS])
print("countries with series", len(series), "years", YEARS[0], Y1, "LSU year", EKY)
