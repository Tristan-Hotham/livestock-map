"""Step 9. Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
The links {{DOI}}, {{DOI_URL}} and https://blog.tristanhotham.com/2026/10/31/livestock-map/ are left for the publisher to fill.
Run: python3 code/09_release.py"""
import re, zipfile, importlib.util
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release")
NAME = "Hotham_Where_the_Animals_Are"
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "05_build_site.py"))
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b); b.checks()

# facts stated in words in the blog figures' alt text
mt = [round(t["pp"], 1) for t in R["mam_pp"]["top"]]
assert mt[:6] == [16.4, 7.4, 6.3, 5.4, 4.3, 4.3] and all(2 <= x <= 4 for x in mt[6:12])
assert [t["iso"] for t in R["mam_pp"]["top"][:6]] == ["MNG", "TCD", "NZL", "URY", "AUS", "MRT"]
g = {x["sp"]: round(x["x"], 1) for x in R["world"]["growth"]}
assert (g["chickens"], g["ducks"], g["goats"], g["pigs"], g["cattle"], g["sheep"], g["horses"], round(R["world"]["pop_x"], 1)) == (7.1, 6.6, 3.4, 2.4, 1.7, 1.4, 0.9, 2.7)
assert round(R["nz"]["peak"] / 1e6, 1) == 70.3 and round(R["nz"]["last"] / 1e6, 1) == 23.6
nzc = jload(f"{PAGE}/series.json")["c"]["NZL"]
assert 6e6 <= min(nzc["cattle"]) and max(nzc["cattle"]) <= 10.5e6 and round(nzc["_pop"][-1] / 1e6, 1) == 5.3
cs = [round(R["conc"][k]["top1_pct"]) for k in ("geese", "ducks", "buffalo", "pigs", "camels", "chickens", "goats", "cattle", "sheep", "horses")]
assert cs == [87, 65, 53, 44, 26, 19, 18, 15, 13, 11], cs
assert R["conc"]["chickens"]["top"][0]["iso"] == "CHN" and R["conc"]["goats"]["top"][0]["iso"] == "IND"
dom = {e["name"]: e["dom"] for e in jload(f"{WORK}/grids.json")["uk"]}
assert dom["Northumberland"] == dom["Na h-Eileanan Siar"] == "sheep" and dom["Lincolnshire"] == dom["Essex"] == "chickens"
assert R["uk"]["sheep_pp"] < 1

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = fill(post, R)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert 5 <= len(used) <= 8, len(used)
left = set(re.findall(r"\{\{(?!IMG)[^}]+\}\}", post)) - {"{{DOI_URL}}"}
assert not left, left
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
check_dashes(vis, "blog")
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
W = R["world"]
meta = {"title": "Where the animals are: the world's cattle, sheep, goats, pigs and chickens on one map",
        "slug": "livestock-map",
        "excerpt": f"{W['animals'] / 1e9:.1f} billion farm animals for {W['pop'] / 1e9:.1f} billion people, mapped every 10 km. Chickens have multiplied {W['sp']['chickens']['x']:.1f} times since {R['meta']['first']}, farm mammals outnumber people in {R['mam_pp']['n_more']} countries, and New Zealand has lost two thirds of its sheep.",
        "seo_description": "A world map of farm animals every 10 km: where cattle, sheep, goats, pigs and chickens live, and how the herds have changed since 1961.",
        "tags": ["livestock", "farming", "cattle", "sheep", "pigs", "chickens", "maps", "data visualisation", "FAO"],
        "header_alt": f"Title card reading 'Where the animals are' in black and barn red on cream, beside a world map colouring every 10 km square by its main farm animal: brown cattle across most continents, pink pigs over eastern China, dark blue buffaloes over northern India, green sheep in Patagonia, South Africa and Australia. Text: {W['animals'] / 1e9:.1f} billion farm animals for {W['pop'] / 1e9:.1f} billion people."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
assert 1961 == R["meta"]["first"] and 0.6 < R["nz"]["fall_pct"] / 100 < 0.7     # 'two thirds of its sheep'
check_dashes(json.dumps(meta, ensure_ascii=False), "blog meta")
with open(f"{REL}/blog/meta.json", "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

# ---------- Zenodo ----------
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)


def link(src, dst):
    if os.path.exists(dst):
        os.remove(dst)
    os.link(src, dst)


link(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/livestock-map_code_and_data.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data", "data/page"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            p = os.path.join(ROOT, d, fn)
            if os.path.isdir(p) or fn.endswith(".pyc"):
                continue
            z.write(p, f"livestock-map/{d}/{fn}")
    for fn in ("README.md", "LICENSE", "index.html"):
        z.write(os.path.join(ROOT, fn), f"livestock-map/{fn}")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\textsuperscript{2}", "²").replace("\\&", "&")
zmeta = {"title": "Where the Animals Are: the World's Cattle, Sheep, Goats, Pigs, Chickens and Other Farm Animals, Mapped Every 10 km and Counted by Country, 1961 to 2024",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{URL}\">{URL}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["livestock", "cattle", "sheep", "goats", "pigs", "chickens", "FAOSTAT", "Gridded Livestock of the World", "maps", "open data"],
         "license": "cc-by-4.0", "access_right": "open", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": URL, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "10.7910/DVN/LHBICE", "relation": "isDerivedFrom", "resource_type": "dataset", "scheme": "doi"},
                                 {"identifier": "10.1038/sdata.2018.227", "relation": "references", "resource_type": "publication-article", "scheme": "doi"},
                                 {"identifier": "https://www.fao.org/faostat/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://github.com/datasets/population", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": [f"{NAME}.pdf", "livestock-map_code_and_data.zip"]}
s = json.dumps(zmeta, ensure_ascii=False)
check_dashes(s, "zenodo")
with open(f"{Z}/metadata.json", "w", encoding="utf-8") as f:
    json.dump(zmeta, f, ensure_ascii=False, indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
