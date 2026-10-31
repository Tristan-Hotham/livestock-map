"""Step 7. The paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Run: python3 code/07_paper.py"""
import re, shutil, subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Where_the_Animals_Are"
Y0, Y1 = R["meta"]["first"], R["meta"]["last"]
tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")
W = R["world"]["sp"]

ORDER = ["chickens", "cattle", "sheep", "ducks", "goats", "pigs", "geese", "turkeys", "buffalo", "rabbits", "horses", "asses", "camels", "rodents", "camelids", "mules", "birds"]
rows = ""
for k in ORDER:
    v = W[k]
    n0 = f"{v['n0'] / 1e6:,.1f}" if v["n0"] else "n/a"
    x = f"{v['x']:.2f}" if v["x"] else "n/a"
    rows += f"{tex(FAO_LABEL[k])} & {n0} & {v['n'] / 1e6:,.1f} & {x} & {v['pp'] * 100:.1f}\\\\\n"
TW = ("\\begin{table}[tbp]\\centering\\small\\caption{World farm animals alive in " + str(Y0) + " and " + str(Y1) + " (FAOSTAT stocks, millions), growth, and animals per 100 people in " + str(Y1) + ".}\\label{tab:world}"
      "\\begin{tabular}{lrrrr}\\toprule Animal & " + str(Y0) + " & " + str(Y1) + " & Multiple & Per 100 people\\\\\\midrule\n" + rows +
      f"\\midrule People & {R['world']['pop0'] / 1e6:,.1f} & {R['world']['pop'] / 1e6:,.1f} & {R['world']['pop_x']:.2f} & \\\\\\bottomrule\\end{{tabular}}\\end{{table}}")

site = jload(f"{DATA}/site.json")["c"]
rows = ""
for t in R["mam_pp"]["top"]:
    c = site[t["iso"]]; p = c["p"]
    g = lambda k: c["v"].get(k, 0) / p
    rows += f"{tex(t['name'])} & {p / 1e6:.1f} & {t['pp']:.1f} & {g('cattle'):.2f} & {g('sheep'):.2f} & {g('goats'):.2f} & {g('camels'):.2f} & {g('horses'):.2f}\\\\\n"
TP = ("\\begin{table}[tbp]\\centering\\small\\caption{Countries with most farm mammals per person, " + str(Y1) + " (countries of a million people or more).}\\label{tab:pp}"
      "\\begin{tabular}{lrrrrrrr}\\toprule Country & People (m) & Mammals & Cattle & Sheep & Goats & Camels & Horses\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")

rows = ""
for n in ("England", "Scotland", "Wales", "Northern Ireland"):
    v = R["uk"]["nations"][n]
    rows += f"{n} & {v['area_km2']:,.0f} & {v['sheep'] / 1e6:.1f} & {v['cattle'] / 1e6:.2f} & {v['pigs'] / 1e6:.2f} & {v['chickens'] / 1e6:.1f} & {v['sheep_km2']:.0f} & {v['cattle_km2']:.0f}\\\\\n"
t = R["uk"]["total"]
rows += f"\\midrule United Kingdom & {t['area_km2']:,.0f} & {t['sheep'] / 1e6:.1f} & {t['cattle'] / 1e6:.2f} & {t['pigs'] / 1e6:.2f} & {t['chickens'] / 1e6:.1f} & {t['sheep'] / t['area_km2']:.0f} & {t['cattle'] / t['area_km2']:.0f}\\\\\n"
TU = ("\\begin{table}[tbp]\\centering\\small\\caption{UK nations in the grid, 2015 (GLW 4; millions of head, and head per km\\textsuperscript{2}).}\\label{tab:uk}\\setlength{\\tabcolsep}{4pt}"
      "\\begin{tabular}{lrrrrrrr}\\toprule Nation & km\\textsuperscript{2} & Sheep & Cattle & Pigs & Chickens & Sheep/km\\textsuperscript{2} & Cattle/km\\textsuperscript{2}\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")

t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = fill(t, R, tex=True)
t = t.replace("{{TABLE_WORLD}}", TW).replace("{{TABLE_PP}}", TP).replace("{{TABLE_UK}}", TU)
left = set(re.findall(r"\{\{[^}]+\}\}", t)) - {"{{DOI}}"}
assert not left, left
check_dashes(t, "paper")
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    pass
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
# compile a copy with a visible placeholder DOI (the coordinator fills {{DOI}} in the .tex and recompiles, or the PDF is rebuilt)
tc = t.replace("{{DOI}}", os.environ.get("PAPER_DOI", "10.5281/zenodo.DOI"))
open(os.path.join(OUT, "_build.tex"), "w", encoding="utf-8").write(tc)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", "_build.tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, "_build.log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
shutil.move(os.path.join(OUT, "_build.pdf"), os.path.join(OUT, NAME + ".pdf"))
for ext in (".aux", ".log", ".out", ".tex"):
    q = os.path.join(OUT, "_build" + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–") + txt.count("--"))
