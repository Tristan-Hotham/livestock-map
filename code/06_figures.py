"""Step 6. Static figures: header.png (1200 x 630), blog figures (release/blog/b_*.png) and paper figures
(release/paper/f_*.png). Maps are drawn from the coded page grids and Natural Earth outlines; no web tiles.
Run: python3 code/06_figures.py"""
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from figstyle import *

R = jload(f"{DATA}/results.json"); SITE = jload(f"{DATA}/site.json"); SER = jload(f"{PAGE}/series.json")
UKC = jload(f"{PAGE}/uk_counties.json")
REL = os.path.join(ROOT, "release"); os.makedirs(f"{REL}/blog", exist_ok=True); os.makedirs(f"{REL}/paper", exist_ok=True)
Y0, Y1 = R["meta"]["first"], R["meta"]["last"]
DOMSHOW = ["cattle", "buffalo", "sheep", "goats", "pigs", "chickens", "horses"]


def both(name):
    return [f"{REL}/blog/b_{name}.png", f"{REL}/paper/f_{name}.png"]


def leg(fig, items, y, ncol=4, x=.03, fs=10.5):
    h = [Patch(fc=c, ec="none", label=l) for l, c in items]
    fig.legend(handles=h, loc="upper left", bbox_to_anchor=(x, y), ncol=ncol, frameon=False, fontsize=fs, handlelength=1.1,
               handleheight=1.0, columnspacing=1.3, labelspacing=.5)


def dom_map(ax, extent=WORLD_EXT, w=2400, sea=None):
    outlines(ax, fc="#E6DECA", ec="none", lw=0)
    d = sample_ee("dom", extent, w); l = sample_ee("lsu", extent, w)
    ax.imshow(dom_rgba(d, l), extent=extent, origin="upper", interpolation="nearest", zorder=2)
    outlines(ax, ec="#FFFFFF", lw=.25, z=3, fill=False)
    frame(ax, extent)


# ---------- header ----------
fig = plt.figure(figsize=(6, 3.15), facecolor=BG)
ax = fig.add_axes([.33, .03, .69, .94]); dom_map(ax, (-12.0e6, 15.6e6, -6.0e6, 8.3e6), 1600)
fig.text(.04, .86, "Where the", fontproperties=DISP, fontsize=22, color=FG, va="top")
fig.text(.04, .725, "animals are", fontproperties=DISP, fontsize=22, color=HOT, va="top")
fig.text(.04, .55, f"{R['world']['animals'] / 1e9:.1f} billion farm animals for\n{R['world']['pop'] / 1e9:.1f} billion people. The main\nanimal in every 10 km square.",
         fontproperties=SERP, fontsize=8.6, color=FG, va="top", linespacing=1.45)
for i, k in enumerate(["cattle", "sheep", "pigs", "buffalo", "chickens", "goats"]):
    x, y = .046 + (i % 3) * .095, .245 - (i // 3) * .055
    fig.add_artist(Line2D([x], [y], marker="s", ms=4, mfc=SPC[k], mec="none", ls="", transform=fig.transFigure))
    fig.text(x + .012, y + .012, SPL[k].lower(), fontsize=5.4, color=FG, va="top")
fig.text(.04, .06, "maps.tristanhotham.com/livestock-map", fontsize=5.8, color=MUT)
save(fig, os.path.join(ROOT, "header.png"))

# ---------- main animal map ----------
for out in both("main_map"):
    fig = plt.figure(figsize=(7.6, 4.5), facecolor=BG)
    ax = fig.add_axes([0, .1, 1, .9]); dom_map(ax)
    leg(fig, [(SPL[k], SPC[k]) for k in DOMSHOW], .1, ncol=7, fs=8.6)
    save(fig, out)

# ---------- small multiples: density of six animals ----------
SIX = ["cattle", "sheep", "goats", "pigs", "chickens", "buffalo"]
for out in both("species"):
    fig = plt.figure(figsize=(7.6, 7.3), facecolor=BG)
    for i, k in enumerate(SIX):
        ax = fig.add_axes([(i % 2) * .5 + .02, .685 - (i // 2) * .315, .46, .25])
        outlines(ax, fc="#ECE5D3", ec="none")
        ax.imshow(ramp_rgba(sample_ee(k, w=1300), SPC[k]), extent=WORLD_EXT, origin="upper", interpolation="nearest", zorder=2)
        frame(ax)
        n = R["world"]["sp"][k]["n"]
        ax.set_title(f"{SPL[k]}  {n / 1e9:.2f} billion" if n >= 1e9 else f"{SPL[k]}  {n / 1e6:.0f} million", fontsize=10, color=FG, loc="left", pad=1)
    fig.text(.02, .015, f"Animals per km², 2015 (FAO GLW 4), log scale: palest about 0.1 per km² (chickens 1),\ndarkest 1,000 or more (chickens 100,000). World totals: FAOSTAT {Y1}.", fontsize=8, color=MUT, linespacing=1.5)
    save(fig, out)

# ---------- growth since 1961 ----------
w = SER["c"]["WLD"]; yrs = SER["years"]
for out in both("growth"):
    fig, ax = plt.subplots(figsize=(7.6, 4.4), facecolor=BG); ax.set_facecolor(BG)
    idx = lambda a: np.array(a, float) / a[0]
    ax.plot(yrs, idx(w["_pop"]), color="#9A937F", lw=2.6, ls=(0, (5, 3)))
    ends = [("People", idx(w["_pop"])[-1], "#9A937F")]
    for k in ["chickens", "ducks", "goats", "pigs", "cattle", "sheep", "horses"]:
        v = idx(w[k]); ax.plot(yrs, v, color=colof(k), lw=2.2); ends.append((SPL[k], v[-1], colof(k)))
    ends.sort(key=lambda e: e[1]); last = -9
    for n, y, c in ends:
        yy = max(y, last + .3); last = yy
        ax.text(yrs[-1] + 1, yy, f"{n} {y:.1f}×", color=c, fontsize=9, va="center")
    ax.set_xlim(yrs[0], yrs[-1] + 14); ax.set_ylim(0, 7.6); ax.set_xticks([1961, 1980, 2000, 2020])
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.set_yticks([0, 1, 2, 4, 6]); ax.set_yticklabels(["0", "1×", "2×", "4×", "6×"]); ax.grid(axis="y", color=RULE, lw=.8); ax.set_axisbelow(True)
    ax.set_title(f"World farm animals as a multiple of {Y0} (FAOSTAT); grey dashes: people", fontsize=10, color=FG, loc="left")
    fig.tight_layout(); save(fig, out)

# ---------- farm mammals per person ----------
def hbar(out, rows, title, fmtv, ref=None, figsize=(7.6, 4.6), xmax=None):
    fig, ax = plt.subplots(figsize=figsize, facecolor=BG); ax.set_facecolor(BG)
    y = np.arange(len(rows))[::-1]
    ax.barh(y, [r[1] for r in rows], color=[r[2] for r in rows], height=.7)
    ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows], fontsize=10)
    mx = xmax or max(r[1] for r in rows)
    for yy, r in zip(y, rows):
        ax.text(r[1] + mx * .01, yy, fmtv(r[1]), va="center", fontsize=9.5, color=FG)
    if ref:
        ax.axvline(ref[0], color=MUT, ls=(0, (3, 3)), lw=1); ax.text(ref[0], len(rows) - .3, " " + ref[1], color=MUT, fontsize=8.5, va="bottom")
    for s in ("top", "right", "bottom"): ax.spines[s].set_visible(False)
    ax.set_xticks([]); ax.set_xlim(0, mx * 1.13)
    ax.set_title(title, fontsize=10, color=FG, loc="left")
    fig.tight_layout(); save(fig, out)


for out in both("outnumber"):
    hbar(out, [(t["name"], t["pp"], "#8C4A2F") for t in R["mam_pp"]["top"]], f"Farm mammals per person, {Y1} (countries of a million people or more)", lambda v: f"{v:.1f}", ref=(1, "one per person"))
CK = ["geese", "ducks", "buffalo", "pigs", "camels", "chickens", "goats", "cattle", "sheep", "horses"]
LABF = {"geese": "Geese", "ducks": "Ducks", "buffalo": "Buffaloes", "pigs": "Pigs", "camels": "Camels", "chickens": "Chickens", "goats": "Goats", "cattle": "Cattle", "sheep": "Sheep", "horses": "Horses"}
for out in both("concentration"):
    hbar(out, [(f"{LABF[k]}: {R['conc'][k]['top'][0]['name']}", R["conc"][k]["top1_pct"], colof(k)) for k in CK], f"Share of the world's stock in the country with most, {Y1}", lambda v: f"{v:.0f}%", xmax=100)
LK = sorted(SKEYS, key=lambda k: R["grid"]["conc"][k]["land50_pct"])
for out in both("land_half"):
    hbar(out, [(SPL[k], R["grid"]["conc"][k]["land50_pct"], SPC[k]) for k in LK], "Share of the world's land that holds half of each animal (GLW, 2015)", lambda v: f"{v:.1f}%", figsize=(7.6, 3.6))

# ---------- New Zealand: sheep to cattle ----------
nz = SER["c"]["NZL"]
for out in both("new_zealand"):
    fig, ax = plt.subplots(figsize=(7.6, 3.8), facecolor=BG); ax.set_facecolor(BG)
    ax.plot(yrs, np.array(nz["sheep"], float) / 1e6, color=SPC["sheep"], lw=2.6, label="Sheep")
    ax.plot(yrs, np.array(nz["cattle"], float) / 1e6, color=SPC["cattle"], lw=2.6, label="Cattle")
    ax.plot(yrs, np.array(nz["_pop"], float) / 1e6, color="#9A937F", lw=2.2, ls=(0, (5, 3)), label="People")
    pk = R["nz"]["peak_year"]; ax.annotate(f"{R['nz']['peak'] / 1e6:.1f} million sheep in {pk},\n{R['nz']['peak_pp']:.1f} per person", (pk, R["nz"]["peak"] / 1e6), xytext=(pk + 8, 66), fontsize=9, color=FG, arrowprops=dict(arrowstyle="-", color=MUT, lw=.8))
    ax.text(yrs[-1] + 1, nz["sheep"][-1] / 1e6, f"{nz['sheep'][-1] / 1e6:.1f}m", color=SPC["sheep"], fontsize=9, va="center")
    ax.text(yrs[-1] + 1, nz["cattle"][-1] / 1e6, f"{nz['cattle'][-1] / 1e6:.1f}m", color=SPC["cattle"], fontsize=9, va="center")
    ax.text(yrs[-1] + 1, nz["_pop"][-1] / 1e6 - 1.5, f"{nz['_pop'][-1] / 1e6:.1f}m", color="#9A937F", fontsize=9, va="center")
    ax.set_xlim(yrs[0], yrs[-1] + 7); ax.set_ylim(0, 78)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.grid(axis="y", color=RULE, lw=.8); ax.set_axisbelow(True); ax.legend(frameon=False, loc="center left", bbox_to_anchor=(.01, .38), fontsize=9)
    ax.set_xticks([1961, 1980, 2000, 2020])
    ax.set_title(f"New Zealand: sheep, cattle and people, millions, {Y0} to {Y1} (FAOSTAT, World Bank)", fontsize=10, color=FG, loc="left")
    fig.tight_layout(); save(fig, out)

# ---------- Britain and Ireland ----------
ext = (-10.7, 2.0, 49.8, 59.0)
kx = np.cos(np.radians(54.5))
for out in both("britain_ireland"):
    fig = plt.figure(figsize=(7.6, 5.6), facecolor=BG)
    for j, k in enumerate(["dom", "sheep"]):
        ax = fig.add_axes([j * .5, .1, .5, .86])
        for iso, ps in SHAPES:
            pass
        for f in NE["features"]:
            for ring in rings(f["geometry"]):
                ax.add_patch(MPoly(np.column_stack([ring[:, 0] * kx, ring[:, 1]]), closed=True, fc="#ECE5D3", ec="none", zorder=1))
        if k == "dom":
            img = dom_rgba(sample_ll("dom", *ext, w=900), sample_ll("lsu", *ext, w=900))
        else:
            img = ramp_rgba(sample_ll("sheep", *ext, w=900), SPC["sheep"])
        ax.imshow(img, extent=(ext[0] * kx, ext[1] * kx, ext[2], ext[3]), origin="upper", interpolation="nearest", zorder=2, aspect="auto")
        for f in UKC["features"]:
            for ring in rings(f["geometry"]):
                ax.add_patch(MPoly(np.column_stack([ring[:, 0] * kx, ring[:, 1]]), closed=True, fc="none", ec="#FFFFFF", lw=.35, zorder=3))
        for f in NE["features"]:
            for ring in rings(f["geometry"]):
                ax.add_patch(MPoly(np.column_stack([ring[:, 0] * kx, ring[:, 1]]), closed=True, fc="none", ec="#5A5446", lw=.4, zorder=4))
        ax.set_xlim(ext[0] * kx, ext[1] * kx); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.axis("off")
        ax.set_title("Main animal by livestock units" if k == "dom" else "Sheep per km² (darkest 1,000)", fontsize=10, color=FG, loc="left", pad=2)
    leg(fig, [(SPL[k], SPC[k]) for k in ["cattle", "sheep", "pigs", "chickens"]], .1, ncol=4, fs=9)
    fig.text(.02, .02, "FAO Gridded Livestock of the World 4, 2015; UK counties outlined.", fontsize=7.6, color=MUT)
    save(fig, out)
print("figures done:", sorted(os.listdir(f"{REL}/blog")))
