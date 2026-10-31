"""Step 8. README.md and LICENSE, numbers from data/results.json.
Run: python3 code/08_readme.py"""
from common import *

R = jload(f"{DATA}/results.json")
W = R["world"]; S = W["sp"]; Y0, Y1 = R["meta"]["first"], R["meta"]["last"]
size = lambda f: f"{os.path.getsize(os.path.join(DATA, f)) / 1e6:.1f} MB"
pg = lambda f: f"{os.path.getsize(os.path.join(PAGE, f)) / 1e6:.1f} MB"
bn = lambda v: f"{v / 1e9:.2f} billion"
u = R["uk"]
readme = f"""# Where the animals are

A world map of farm animals: where the world's cattle, buffaloes, sheep, goats, pigs, chickens, ducks and horses live, every 10 km (FAO Gridded Livestock of the World, 2015), and how the herds and flocks of {len(FAO_ITEMS)} kinds of farm animal have changed in every country from {Y0} to {Y1} (FAOSTAT).

Interactive page: {URL}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}

A data study by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349).

## Headline results

- In {Y1} there were about {W['animals'] / 1e9:.1f} billion farm animals alive at once, {W['animals_pp']:.1f} for each of {W['pop'] / 1e9:.1f} billion people: {bn(S['chickens']['n'])} chickens ({S['chickens']['pp']:.1f} per person), {bn(S['cattle']['n'])} cattle, {bn(S['sheep']['n'])} sheep, {bn(S['goats']['n'])} goats and {S['pigs']['n'] / 1e6:,.0f} million pigs.
- Since {Y0} people have multiplied {W['pop_x']:.1f} times, chickens {S['chickens']['x']:.1f} times, ducks {S['ducks']['x']:.1f}, goats {S['goats']['x']:.1f} and camels {S['camels']['x']:.1f}; cattle {S['cattle']['x']:.1f} (from {W['cattle_pp0']:.2f} to {W['cattle_pp']:.2f} per person); horses {S['horses']['x']:.1f}. China's pig herd fell {R['pigs']['chn_fall_pct']:.0f}% from 2018 to 2019 (African swine fever), taking {R['pigs']['fall_pct']:.0f}% off the world total.
- Farm mammals outnumber people in {R['mam_pp']['n_more']} of {R['mam_pp']['n_countries']} countries of a million people or more; Mongolia has {R['mongolia']['pp']:.1f} per person, Uruguay {R['pp']['cattle']['top'][0]['pp']:.1f} cattle per person, Denmark {R['pp']['pigs']['top'][0]['pp']:.1f} pigs per person. New Zealand's sheep peaked in {R['nz']['peak_year']} at {R['nz']['peak_pp']:.1f} per person and are now {R['nz']['last_pp']:.1f}.
- Concentration: China has {R['conc']['pigs']['top1_pct']:.0f}% of the world's pigs, {R['conc']['ducks']['top1_pct']:.0f}% of its ducks and {R['conc']['geese']['top1_pct']:.0f}% of its geese; India {R['conc']['buffalo']['top1_pct']:.0f}% of its buffaloes; Chad {R['conc']['camels']['top1_pct']:.0f}% of its camels. Half of all pigs live on {R['grid']['conc']['pigs']['land50_pct']:.1f}% of the world's land, half of all cattle on {R['grid']['conc']['cattle']['land50_pct']:.1f}%.
- By livestock units, cattle are the main farm animal in {R['main']['counts']['cattle']} of {R['main']['n']} countries and on {R['grid']['dom_pct']['cattle']:.0f}% of the world's land.
- United Kingdom: {u['fao']['sheep'] / 1e6:.1f} million sheep, the most in Europe outside Turkey. Wales has {u['wales_area_share']:.0f}% of UK land and {u['nations']['Wales']['sheep_share']:.0f}% of its sheep; Powys alone {u['top_sheep_n'][0]['share']:.0f}%. Cattle are densest in Northern Ireland, pigs in the East Riding of Yorkshire, chickens in Herefordshire and Lincolnshire.

Every number is in `data/results.json`, which the page, paper, blog and collage are built from.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/05_build_site.py`; results embedded, grids and other page data load from `data/page/`). |
| `header.png` | Social card, 1200 x 630. |
| `data/country_stocks.csv` | FAOSTAT stocks by country, animal and year, {Y0} to {Y1}, plus world totals ({size('country_stocks.csv')}). |
| `data/country_summary.csv` | Every country in {Y1}: population, land, head of each animal, per person figures, livestock units and main animal. |
| `data/grid_country_2015.csv` | The GLW grid summed by country (2015), with the main animal by livestock units. |
| `data/uk_counties_2015.csv` | UK counties from the grid (2015): area, head of each animal, livestock units, main animal. |
| `data/results.json` | Every number used in the page, paper, blog and collage. |
| `data/site.json` | Country and county tables embedded in the page. |
| `data/page/grid_a.png` to `grid_d.png` | Coded 10 km grids (85N to 60S): cattle, sheep, goats / pigs, chickens, buffaloes / horses, ducks, livestock units / main animal and country index ({pg('grid_a.png')}, {pg('grid_b.png')}, {pg('grid_c.png')}, {pg('grid_d.png')}). Code: v = 1 + round(254 (log10 d - log10 lo) / (log10 hi - log10 lo)), 0 below lo; lo and hi per animal in `results.json` (`grid.range`). |
| `data/page/series.json`, `world.json`, `uk_counties.json`, `cities.json` | Country time series, outlines and place names for the page. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source, blog figures and post, Zenodo files. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `qa/` | Screenshots from the Playwright check (`code/12_qa.py`). |

## Method in brief

- Grid: GLW 4 dasymetric layers for 2015 at 5 arc minutes. Census counts are shared among the cells of each census area by random forest predictions (Gilbert et al. 2018). Summed over the world the grid is within {max(abs(v - 100) for v in R['grid']['vs_fao2015'].values()):.0f}% of FAOSTAT's 2015 totals for every animal.
- Countries: FAOSTAT 'Stocks' (animals alive at one time) for {len(FAO_ITEMS)} items, matched to Natural Earth countries by M49 code. China is mainland China; former states (USSR, Yugoslavia and others) count in world totals only. Per person: World Bank population of the same year.
- Livestock units: each country's FAOSTAT stocks in livestock units divided by its head count ({R['meta']['lsu_year']}); ducks take the chicken factor. The main animal has most livestock units; grid cells under one unit per km² have none.
- Concentration: the smallest share of land (Antarctica excluded) holding half of each animal, densest cells first.
- UK counties: county outlines rasterised ten times finer than the grid; each UK cell's animals shared among counties by area.
- Caveats: the grid is a model and a 2015 snapshot; FAOSTAT figures vary in quality; stocks are animals alive at once, not animals raised per year; livestock units are a rough common currency; wild animals, reindeer and fish are not included.

## How to rerun

Needs Python 3 with numpy, pandas, rasterio, scipy, shapely, pyproj, Pillow, matplotlib and fontTools, xelatex and pdftotext, and Playwright for the QA step. Raw inputs are read in place from the paths in `code/common.py`: the GLW 4 GeoTIFFs (`*_Da.tif`, `Areakm.tif`) from Harvard Dataverse, the FAOSTAT bulk downloads (QCL, EK, RL, normalised CSV, retrieved in {RETRIEVED}), World Bank population from github.com/datasets/population, and Natural Earth and UK county boundaries. Intermediate files go to `/dev/shm/livestock` (set `LSTMP` to change).

```
python3 code/01_fao.py          # FAOSTAT stocks, livestock units, land, population
python3 code/02_grids.py        # GLW grids: country sums, main animal, concentration, UK counties, page grids
python3 code/03_results.py      # results.json, site.json, series.json, CSVs
python3 code/04_page_data.py    # outlines and place names for the page
python3 code/05_build_site.py   # index.html (with checks of every fact stated in words)
python3 code/06_figures.py      # header, blog and paper figures
python3 code/07_paper.py        # paper PDF (set PAPER_DOI to print the DOI)
python3 code/08_readme.py       # README and LICENSE
python3 code/09_release.py      # blog post, Zenodo files
python3 reddit/collage.py       # collage
python3 code/12_qa.py           # browser check and screenshots
```

## Sources and licences

- Gilbert, M., Nicolas, G., Cinardi, G., Wint, G. R. W., Vanwambeke, S. O. and Robinson, T. P. (2018) Global distribution data for cattle, buffaloes, horses, sheep, goats, pigs, chickens and ducks in 2010. Scientific Data 5, 180227. GLW 4 layers for 2015 on Harvard Dataverse: cattle doi:10.7910/DVN/LHBICE, sheep VZOYHM, goats YYG6ET, pigs CIVCPB, chickens SXHLF3, buffaloes I1WCAB, horses JJGCTX, ducks S9ONXV. CC BY 4.0.
- FAO, FAOSTAT: Crops and livestock products (QCL), Livestock patterns (EK), Land use (RL), https://www.fao.org/faostat/. CC BY 4.0.
- World Bank, World Development Indicators, SP.POP.TOTL, via https://github.com/datasets/population. CC BY 4.0.
- Natural Earth countries and populated places (public domain); UK county boundaries from ONS and partners (Open Government Licence v3.0).
- Base map tiles on the page: © Esri.

## Citation

Hotham, T. (2026) Where the animals are: the world's cattle, sheep, goats, pigs, chickens and other farm animals, mapped every 10 km and counted by country, {Y0} to {Y1}. Zenodo. https://doi.org/{DOI}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
check_dashes(readme.replace("|---|---|", ""), "README")
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
lic = open("/home/claude/ref/drinks-map/LICENSE", encoding="utf-8").read().split("\n\n\nThis licence covers")[0]
lic += """


This licence covers the code in code/, reddit/collage.py and the page scripts.
The text of the page, the paper and the blog post, the figures and the derived
data files in data/ are released under the Creative Commons Attribution 4.0
International licence (CC BY 4.0). They are derived from FAO data (Gridded
Livestock of the World v4 and FAOSTAT, CC BY 4.0, (c) FAO), World Bank population
data (CC BY 4.0), Natural Earth (public domain) and UK boundaries from ONS and
partners (Open Government Licence v3.0), which must be credited when reused.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)
print("README", len(readme.split()), "words")
