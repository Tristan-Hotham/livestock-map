"""r/dataisbeautiful collage for livestock-map: 2400 x 3000 px, light background. Numbers from data/results.json.
Run: python3 reddit/collage.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figstyle import *
from matplotlib.patches import Patch

R = jload(f"{DATA}/results.json"); SER = jload(f"{PAGE}/series.json")
W = R["world"]; S = W["sp"]; Y0, Y1 = R["meta"]["first"], R["meta"]["last"]
cf = R["grid"]["coef"]
assert 6 < cf["cattle"] / cf["sheep"] < 7 and 2 < cf["cattle"] / cf["pigs"] < 3 and 60 < cf["cattle"] / cf["chickens"] < 70
BGC = "#F6F2E6"
fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BGC)
fig.text(.045, .968, "Where the world's farm animals are", fontproperties=DISP, fontsize=50, color=FG, va="top")
fig.text(.045, .915, f"The main farm animal in every 10 km square of the planet, weighted by livestock units (on FAO's world\naverages a cow counts as much as six or seven sheep, two or three pigs or over sixty chickens).",
         fontproperties=SERP, fontsize=15.5, color=FG, va="top", linespacing=1.45)

# hero map
ext = (-12.4e6, 15.7e6, -6.1e6, 8.4e6)
ax = fig.add_axes([0, .47, 1, .40])
outlines(ax, fc="#E4DCC7", ec="none")
d = sample_ee("dom", ext, 2600); l = sample_ee("lsu", ext, 2600)
ax.imshow(dom_rgba(d, l), extent=ext, origin="upper", interpolation="nearest", zorder=2)
outlines(ax, ec="#FFFFFF", lw=.3, z=3, fill=False)
frame(ax, ext)
# callouts on the sea, each with a short leader to its place
CALL = [(f"Pigs: China has {R['conc']['pigs']['top1_pct']:.0f}%\nof the world's pigs", (112, 31), (146, 12), SPC["pigs"], "center"),
        (f"Buffaloes: India has {R['conc']['buffalo']['top1_pct']:.0f}%\nof the world's buffaloes", (80, 25), (72, -8), SPC["buffalo"], "center"),
        ("Sheep: Patagonia", (-69, -46), (-104, -47), SPC["sheep"], "center"),
        ("Sheep and goats:\nthe edge of the Sahel", (-8, 16), (-47, 8), SPC["goats"], "center"),
        ("Chickens: the US\nsouth-east", (-84, 33.5), (-58, 25), SPC["chickens"], "left"),
        (f"Mongolia: {R['mongolia']['pp']:.0f} farm\nmammals a person", (103, 47), (134, 27), FG, "left"),
        ("Sheep: Wales", (-3.6, 52.3), (-30, 45), SPC["sheep"], "center"),
        ("Pigs: Denmark and\nthe Netherlands", (8, 54), (-27, 59), SPC["pigs"], "center")]
for txt, (lo, la), (tx, ty), col, ha in CALL:
    x0, y0 = tr.transform(lo, la); x1, y1 = tr.transform(tx, ty)
    ax.annotate(txt, xy=(x0, y0), xytext=(x1, y1), fontsize=11, color=FG, ha=ha, va="center", family=MONO, zorder=6,
                arrowprops=dict(arrowstyle="-", color=FG, lw=.8, shrinkA=4, shrinkB=0),
                bbox=dict(boxstyle="round,pad=.25", fc=BGC, ec=col, lw=1.4, alpha=.95))
    ax.plot([x0], [y0], "o", ms=3.2, color=FG, zorder=7)
items = [(SPL[k], SPC[k]) for k in ["cattle", "buffalo", "sheep", "goats", "pigs", "chickens", "horses"]]
LEGP = SERP.copy(); LEGP.set_size(14)
fig.legend(handles=[Patch(fc=c, ec="none", label=n) for n, c in items], loc="upper left", bbox_to_anchor=(.04, .468), ncol=7, frameon=False, prop=LEGP,
           handlelength=1.1, columnspacing=1.2)
fig.text(.045, .432, "Paler colour: fewer animals per km². Blank: under one livestock unit per km² (deserts, ice, forest). Ducks are never the main animal.", family=MONO, fontsize=10, color=MUT)

# big numbers
nums = [(f"{W['animals'] / 1e9:.1f}bn", HOT, f"farm animals alive at once\nin {Y1}, for {W['pop'] / 1e9:.1f} billion\npeople"),
        (f"{S['chickens']['pp']:.1f}", "#C08A00", f"chickens for every person;\n{S['chickens']['x']:.1f} times as many as\nin {Y0}"),
        (f"{R['mam_pp']['n_more']}", COOL, f"countries where farm\nmammals outnumber people\n(of {R['mam_pp']['n_countries']} with 1m+ people)"),
        (f"{R['grid']['conc']['pigs']['land50_pct']:.1f}%", SPC["pigs"], f"of the world's land holds\nhalf of its pigs (cattle:\n{R['grid']['conc']['cattle']['land50_pct']:.1f}%)")]
for i, (big, col, small) in enumerate(nums):
    x = .045 + i * .235
    fig.text(x, .405, big, fontproperties=DISP, fontsize=44, color=col, va="top")
    fig.text(x, .352, small, family=MONO, fontsize=11.5, color=FG, va="top", linespacing=1.45)

# growth since 1961
w = SER["c"]["WLD"]; yrs = SER["years"]
a = fig.add_axes([.07, .1, .42, .155]); a.set_facecolor(BGC)
idx = lambda v: np.array(v, float) / v[0]
a.plot(yrs, idx(w["_pop"]), color="#9A937F", lw=2.4, ls=(0, (5, 3)))
ends = [("People", idx(w["_pop"])[-1], "#9A937F")]
for k in ["chickens", "goats", "pigs", "cattle", "sheep", "horses"]:
    v = idx(w[k]); a.plot(yrs, v, color=SPC[k], lw=2.2); ends.append((SPL[k], v[-1], SPC[k]))
ends.sort(key=lambda e: e[1]); last = -9
for n, y, c in ends:
    yy = max(y, last + .42); last = yy
    a.text(yrs[-1] + 1.5, yy, f"{n} {y:.1f}×", color=c, fontsize=10.5, va="center", family=MONO)
a.set_xlim(yrs[0], yrs[-1] + 22); a.set_ylim(0, 7.6); a.set_xticks([1961, 1980, 2000, 2024]); a.set_yticks([1, 2, 4, 6]); a.set_yticklabels(["1×", "2×", "4×", "6×"])
for s in ("top", "right"): a.spines[s].set_visible(False)
a.grid(axis="y", color=RULE, lw=.8); a.set_axisbelow(True); a.tick_params(labelsize=10)
a.set_title(f"World farm animals, multiple of {Y0} (FAOSTAT)", family=MONO, fontsize=12.5, color=FG, loc="left", pad=8)

# per person bars
b = fig.add_axes([.69, .1, .27, .155]); b.set_facecolor(BGC)
top = R["mam_pp"]["top"][:8]
y = np.arange(len(top))[::-1]
b.barh(y, [t["pp"] for t in top], color=SPC["cattle"], height=.68)
b.set_yticks(y); b.set_yticklabels([t["name"] for t in top], fontsize=10.5)
for yy, t in zip(y, top):
    b.text(t["pp"] + .3, yy, f"{t['pp']:.1f}", va="center", fontsize=10.5, color=FG)
b.axvline(1, color=MUT, lw=1, ls=(0, (3, 3)))
for s in ("top", "right", "bottom"): b.spines[s].set_visible(False)
b.set_xticks([]); b.set_xlim(0, top[0]["pp"] * 1.18)
b.set_title(f"Farm mammals per person, {Y1}", family=MONO, fontsize=12.5, color=FG, loc="left", pad=8)

fig.text(.045, .022, f"Sources: FAO Gridded Livestock of the World v4, 2015 (Gilbert et al. 2018, CC BY 4.0); FAOSTAT livestock stocks {Y0} to {Y1} and livestock\n"
         "units (CC BY 4.0); World Bank population; Natural Earth. The grid is a model of census counts; stocks are animals alive at one time.\n"
         "Analysis and chart: Tristan Hotham, with Python and matplotlib  ·  maps.tristanhotham.com/livestock-map", family=MONO, fontsize=9.5, color=MUT, linespacing=1.5, va="bottom")
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "where_the_animals_are.png")
fig.savefig(out, facecolor=BGC, dpi=200)
print("ok", out)

# ---------- post.md ----------
post = f"""## Title

[OC] There are {S['chickens']['pp']:.1f} chickens for every person on Earth. Here is the main farm animal in every 10 km square of the planet

## Body

I mapped the world's farm animals using the FAO's Gridded Livestock of the World (a 10 km model of cattle, buffaloes, sheep, goats, pigs, chickens, ducks and horses in 2015) and FAOSTAT's country counts from {Y0} to {Y1}. Each square is coloured by the animal with the most livestock units, so a cow outweighs a chicken. In {Y1} there were about {W['animals'] / 1e9:.1f} billion farm animals alive at once for {W['pop'] / 1e9:.1f} billion people. Chickens have multiplied {S['chickens']['x']:.1f} times since {Y0}; farm mammals outnumber people in {R['mam_pp']['n_more']} countries, led by Mongolia ({R['mongolia']['pp']:.1f} per person); China has {R['conc']['pigs']['top1_pct']:.0f}% of the world's pigs and India {R['conc']['buffalo']['top1_pct']:.0f}% of its buffaloes. New Zealand has lost two thirds of its sheep since {R['nz']['peak_year']}. Caveats: the grid is a model that spreads census counts over the land, and it is a 2015 snapshot; stocks are animals alive at one time, not animals raised per year. Interactive map, where you can switch animals and zoom to your own area: https://maps.tristanhotham.com/livestock-map/

## Source comment

Source: FAO Gridded Livestock of the World v4, 2015 layers (Gilbert et al. 2018, Scientific Data; Harvard Dataverse doi:10.7910/DVN/LHBICE and companions, CC BY 4.0); FAOSTAT livestock stocks, livestock units and land use, {Y0} to {Y1} (FAO, CC BY 4.0); World Bank population (CC BY 4.0); Natural Earth outlines (public domain).

Tools: Python (numpy, rasterio, pandas, matplotlib); Leaflet for the interactive map.

Interactive version: https://maps.tristanhotham.com/livestock-map/
Paper: {{{{DOI_URL}}}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/livestock-map/}}
"""
assert 0.6 < R["nz"]["fall_pct"] / 100 < 0.7
check_dashes(post, "reddit post")
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "post.md"), "w", encoding="utf-8").write(post)
print("post.md written")
