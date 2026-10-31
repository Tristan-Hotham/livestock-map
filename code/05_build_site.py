"""Step 5. Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; results and site data are embedded; grids, series, outlines and names load from data/page/.
Facts stated in words are checked here. The full-screen map snippet (code/fullscreen_snippet.html) is pasted before </body>.
Run: python3 code/05_build_site.py"""
import re
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
S = jload(f"{WORK}/fao.json")["series"]


def checks():
    """Facts stated in words anywhere (page, blog, paper, collage)."""
    w = R["world"]["sp"]
    g = {x["sp"]: x["x"] for x in R["world"]["growth"]}
    assert w["chickens"]["x"] > w["ducks"]["x"] > w["goats"]["x"] > R["world"]["pop_x"] and w["camels"]["x"] > R["world"]["pop_x"]
    assert w["cattle"]["x"] < R["world"]["pop_x"] and w["horses"]["x"] < 1 and w["mules"]["x"] < 1
    assert 0.6 < R["world"]["mammals_pp"] < 0.7                     # 'about two for every three people'
    assert 3.5 < R["world"]["animals_pp"] < 4.5                     # 'four farm animals for every person'
    assert R["goats_afr_asia_share"] > 90
    assert R["pigs"]["peak_year"] == 2015 and R["pigs"]["y2019"] < R["pigs"]["y2018"]
    pp = R["pp"]
    assert pp["goats"]["top"][0]["iso"] == "MNG" and pp["sheep"]["top"][0]["iso"] == "MNG"
    assert pp["goats"]["top_any"][0]["iso"] == "MNG" and pp["sheep"]["top_any"][0]["iso"] == "MNG"
    assert pp["cattle"]["top_any"][0]["iso"] == "URY" and pp["pigs"]["more_than_people"] == ["Denmark"]
    assert pp["sheep"]["top"][1]["iso"] == "NZL" and pp["sheep"]["top"][2]["iso"] == "AUS"
    for c in ("Mauritania", "Mali", "Chad", "South Sudan"):
        assert any(c in pp[k]["more_than_people"] for k in ("sheep", "goats", "cattle")), c
    assert R["mam_pp"]["top"][0]["iso"] == "MNG" and R["mam_pp"]["top"][1]["iso"] == "TCD"
    c = R["conc"]
    assert c["pigs"]["top"][0]["iso"] == "CHN" and c["ducks"]["top"][0]["iso"] == "CHN" and c["geese"]["top"][0]["iso"] == "CHN"
    assert c["buffalo"]["top"][0]["iso"] == "IND" and [t["iso"] for t in c["buffalo"]["top"][:3]] == ["IND", "PAK", "CHN"]
    assert c["camels"]["top"][0]["iso"] == "TCD" and 22 < c["camels"]["top1_pct"] < 28
    assert c["cattle"]["top"][0]["iso"] == "BRA" and c["sheep"]["top"][0]["iso"] == "CHN" and c["horses"]["top"][0]["iso"] == "MEX"
    big = ["cattle", "sheep", "goats", "pigs", "buffalo", "chickens", "ducks", "horses", "camels", "geese"]
    assert sorted(big, key=lambda k: c[k]["top1_pct"])[:3] == ["horses", "sheep", "cattle"]
    gc = R["grid"]["conc"]
    assert gc["pigs"]["land50_pct"] < gc["chickens"]["land50_pct"] < gc["sheep"]["land50_pct"] < gc["cattle"]["land50_pct"]
    assert R["grid"]["hot"]["pigs"]["iso"] == "NLD"
    assert all(abs(v - 100) < 6 for v in R["grid"]["vs_fao2015"].values())
    m = R["main"]["counts"]
    assert m["cattle"] > m["chickens"] > m["pigs"] > m["sheep"]
    assert max(R["grid"]["dom_pct"], key=R["grid"]["dom_pct"].get) == "cattle"
    u = R["uk"]
    assert u["sheep_eu_rank"] == 1 and u["tur_sheep"] > u["fao"]["sheep"] and u["main"] == "cattle"
    assert sorted(u["lsu_share"], key=lambda k: -u["lsu_share"][k])[:2] == ["cattle", "sheep"]
    assert u["top_sheep_n"][0]["name"] == "Powys" and u["top_sheep_km2"][0]["name"] == "Powys"
    assert [x["name"] for x in u["top_cattle_km2"][:4]] == ["Northern Ireland", "Cheshire", "Cornwall", "Somerset"]
    assert [x["name"] for x in u["top_pigs_n"][:2]] == ["North Yorkshire", "Norfolk"] and u["top_pigs_n"][3]["name"] == "Suffolk"
    assert u["top_pigs_km2"][0]["name"] == "East Riding of Yorkshire"
    assert [x["name"] for x in u["top_chickens_km2"][:2]] == ["Herefordshire", "Lincolnshire"]
    dom = {e["name"]: e["dom"] for e in jload(f"{WORK}/grids.json")["uk"]}
    assert all(dom[k] == "sheep" for k in ("Shetland Islands", "Scottish Borders", "Powys", "Gwynedd"))
    assert all(dom[k] == "pigs" for k in ("Norfolk", "Suffolk", "East Riding of Yorkshire"))
    assert R["ireland"]["cattle_pp"] > 1 and R["nz"]["peak_year"] == 1982 and 1.15 < R["nz"]["cattle_x_since_peak"] < 1.25
    assert m["goats"] == 2 and m["camels"] == 2 and 2.8 < R["nz"]["peak"] / R["nz"]["last"] < 3.2
    assert c["buffalo"]["top3_pct"] > 85
    assert R["uk"]["nations"]["Northern Ireland"]["cattle_km2"] == max(n["cattle_km2"] for n in R["uk"]["nations"].values())


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = fill(tpl, R)
    assert "{{" not in html.replace("{{DOI}}", "").replace("https://blog.tristanhotham.com/2026/10/31/livestock-map/", ""), re.findall(r"\{\{[^}]+\}\}", html)[:5]
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    check_dashes(vis, "page text")
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    checks()
    build()
