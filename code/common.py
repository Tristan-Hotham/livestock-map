"""Shared paths and helpers for the livestock-map project.

Raw inputs (read in place, never copied into the repo):
  GLW    /home/claude/newdata/raw/glw/{Ct,Sh,Gt,Pg,Ch,Bf,Ho,Dk}_Da.tif, Areakm.tif, Ct_meta.html
         FAO Gridded Livestock of the World v4 (2015), 5 arc minute, dasymetric heads per cell. Harvard Dataverse, CC BY 4.0.
  FAO    /home/claude/newdata/raw/fao/Production_Crops_Livestock_E_All_Data_(Normalized).csv   (FAOSTAT QCL, 1961 to 2024)
         /home/claude/newdata/raw/fao/Environment_LivestockPatterns_E_All_Data_(Normalized).csv (FAOSTAT EK, livestock units)
         /home/claude/newdata/raw/fao/Inputs_LandUse_E_All_Data_(Normalized).csv               (FAOSTAT RL, land use)
         FAOSTAT bulk downloads, retrieved 2026, CC BY 4.0. Latin-1 encoding.
  WB     /home/claude/newdata/raw/wb/population.csv  World Bank total population (SP.POP.TOTL), as packaged at
         https://github.com/datasets/population (data/population.csv), CC BY 4.0.
  GEO    /home/claude/newdata/raw/geo/ne_50m_admin_0_countries.geojson, ne_10m_populated_places_simple.geojson,
         uk_topo.json (ONS boundaries, OGL), counties_uk.geojson. Natural Earth is public domain.
"""
import json, gzip, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAWD = "/home/claude/newdata/raw"
GLW = f"{RAWD}/glw"
FAO = f"{RAWD}/fao"
WB = f"{RAWD}/wb/population.csv"
GEO = f"{RAWD}/geo"
NE50 = f"{GEO}/ne_50m_admin_0_countries.geojson"
PLACES = f"{GEO}/ne_10m_populated_places_simple.geojson"
DATA = os.path.join(ROOT, "data")
PAGE = os.path.join(DATA, "page")
WORK = os.environ.get("LSTMP", "/dev/shm/livestock")   # intermediates live in memory, not in the repo
for d in (DATA, PAGE, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "livestock-map"
URL = "https://maps.tristanhotham.com/livestock-map/"
REPO = "https://github.com/Tristan-Hotham/livestock-map"
DOI = "{{DOI}}"
BLOG = "https://blog.tristanhotham.com/2026/10/31/livestock-map/"
RETRIEVED = "2026"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")

# The eight gridded species (GLW 4, 2015). key, GLW code, label, plural, colour, FAOSTAT item code
SPECIES = [
    ("cattle", "Ct", "Cattle", "cattle", "#8C4A2F", 866),
    ("buffalo", "Bf", "Buffaloes", "buffaloes", "#4B4E6D", 946),
    ("sheep", "Sh", "Sheep", "sheep", "#6E8B3D", 976),
    ("goats", "Gt", "Goats", "goats", "#4F9CC4", 1016),
    ("pigs", "Pg", "Pigs", "pigs", "#D46A8C", 1034),
    ("chickens", "Ch", "Chickens", "chickens", "#E0A106", 1057),
    ("ducks", "Dk", "Ducks", "ducks", "#2E7D6B", 1068),
    ("horses", "Ho", "Horses", "horses", "#6B4C7A", 1096),
]
SKEYS = [s[0] for s in SPECIES]
# FAOSTAT stock items (head, or 1000 head for birds and rodents)
FAO_ITEMS = {866: "cattle", 946: "buffalo", 976: "sheep", 1016: "goats", 1034: "pigs", 1057: "chickens", 1068: "ducks",
             1096: "horses", 1072: "geese", 1079: "turkeys", 1107: "asses", 1110: "mules", 1126: "camels",
             1157: "camelids", 1140: "rabbits", 1150: "rodents", 1083: "birds", 1181: "bees"}
FAO_LABEL = {"cattle": "Cattle", "buffalo": "Buffaloes", "sheep": "Sheep", "goats": "Goats", "pigs": "Pigs",
             "chickens": "Chickens", "ducks": "Ducks", "horses": "Horses", "geese": "Geese", "turkeys": "Turkeys",
             "asses": "Donkeys", "mules": "Mules and hinnies", "camels": "Camels", "camelids": "Llamas and alpacas",
             "rabbits": "Rabbits and hares", "rodents": "Other rodents (guinea pigs)", "birds": "Other birds (pigeons, quail)",
             "bees": "Beehives"}
MAMMALS = ["cattle", "buffalo", "sheep", "goats", "pigs", "horses", "asses", "mules", "camels", "camelids"]
BIRDS = ["chickens", "ducks", "geese", "turkeys", "birds"]


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def nodash(v):
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [nodash(x) for x in v]
    if isinstance(v, dict):
        return {k: nodash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = nodash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def getp(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmtv(v, f):
    """Number formats shared by the page, blog, README and post builders."""
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "bn": return f"{float(v) / 1e9:.1f} billion"
    if f == "bn2": return f"{float(v) / 1e9:.2f} billion"
    if f == "m": return f"{float(v) / 1e6:.1f} million"
    if f == "m0": return f"{round(float(v) / 1e6):,} million"
    if f == "x": return f"{float(v):.1f} times"
    raise ValueError(f)


TOKEN = re.compile(r"\{\{(?!IMG|DOI|BLOG_URL|TABLE_)([^}|]+)(\|(\w+))?\}\}")


def fill(text, R, tex=False):
    def rep(m):
        s = fmtv(getp(R, m.group(1)), m.group(3))
        if tex:
            s = s.replace("%", "\\%").replace("&", "\\&").replace("_", "\\_").replace("#", "\\#")
        return s
    return TOKEN.sub(rep, text)


def check_dashes(text, where):
    for bad in ("—", "–", "--"):
        assert bad not in text, (where, bad, text[max(0, text.find(bad) - 80):text.find(bad) + 80])
    for bad in ("DSIT", "DCMS", "civil serv", "Civil Serv"):
        assert bad not in text, (where, bad)
