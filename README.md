# Where the animals are

A world map of farm animals: where the world's cattle, buffaloes, sheep, goats, pigs, chickens, ducks and horses live, every 10 km (FAO Gridded Livestock of the World, 2015), and how the herds and flocks of 18 kinds of farm animal have changed in every country from 1961 to 2024 (FAOSTAT).

Interactive page: https://maps.tristanhotham.com/livestock-map/
Paper: https://doi.org/10.5281/zenodo.23842985
Blog post: https://blog.tristanhotham.com/2026/10/31/livestock-map/

A data study by Dr Tristan Hotham (Independent researcher, ORCID 0000-0003-4931-9349).

## Headline results

- In 2024 there were about 35.3 billion farm animals alive at once, 4.3 for each of 8.1 billion people: 27.68 billion chickens (3.4 per person), 1.58 billion cattle, 1.36 billion sheep, 1.19 billion goats and 962 million pigs.
- Since 1961 people have multiplied 2.7 times, chickens 7.1 times, ducks 6.6, goats 3.4 and camels 3.4; cattle 1.7 (from 0.31 to 0.19 per person); horses 0.9. China's pig herd fell 28% from 2018 to 2019 (African swine fever), taking 12% off the world total.
- Farm mammals outnumber people in 40 of 159 countries of a million people or more; Mongolia has 16.4 per person, Uruguay 3.5 cattle per person, Denmark 1.9 pigs per person. New Zealand's sheep peaked in 1982 at 22.3 per person and are now 4.5.
- Concentration: China has 44% of the world's pigs, 65% of its ducks and 87% of its geese; India 53% of its buffaloes; Chad 26% of its camels. Half of all pigs live on 1.3% of the world's land, half of all cattle on 5.9%.
- By livestock units, cattle are the main farm animal in 127 of 194 countries and on 42% of the world's land.
- United Kingdom: 31.0 million sheep, the most in Europe outside Turkey. Wales has 9% of UK land and 26% of its sheep; Powys alone 10%. Cattle are densest in Northern Ireland, pigs in the East Riding of Yorkshire, chickens in Herefordshire and Lincolnshire.

Every number is in `data/results.json`, which the page, paper, blog and collage are built from.

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/05_build_site.py`; results embedded, grids and other page data load from `data/page/`). |
| `header.png` | Social card, 1200 x 630. |
| `data/country_stocks.csv` | FAOSTAT stocks by country, animal and year, 1961 to 2024, plus world totals (0.8 MB). |
| `data/country_summary.csv` | Every country in 2024: population, land, head of each animal, per person figures, livestock units and main animal. |
| `data/grid_country_2015.csv` | The GLW grid summed by country (2015), with the main animal by livestock units. |
| `data/uk_counties_2015.csv` | UK counties from the grid (2015): area, head of each animal, livestock units, main animal. |
| `data/results.json` | Every number used in the page, paper, blog and collage. |
| `data/site.json` | Country and county tables embedded in the page. |
| `data/page/grid_a.png` to `grid_d.png` | Coded 10 km grids (85N to 60S): cattle, sheep, goats / pigs, chickens, buffaloes / horses, ducks, livestock units / main animal and country index (3.2 MB, 2.4 MB, 3.0 MB, 0.4 MB). Code: v = 1 + round(254 (log10 d - log10 lo) / (log10 hi - log10 lo)), 0 below lo; lo and hi per animal in `results.json` (`grid.range`). |
| `data/page/series.json`, `world.json`, `uk_counties.json`, `cities.json` | Country time series, outlines and place names for the page. |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source, blog figures and post, Zenodo files. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `qa/` | Screenshots from the Playwright check (`code/12_qa.py`). |

## Method in brief

- Grid: GLW 4 dasymetric layers for 2015 at 5 arc minutes. Census counts are shared among the cells of each census area by random forest predictions (Gilbert et al. 2018). Summed over the world the grid is within 5% of FAOSTAT's 2015 totals for every animal.
- Countries: FAOSTAT 'Stocks' (animals alive at one time) for 18 items, matched to Natural Earth countries by M49 code. China is mainland China; former states (USSR, Yugoslavia and others) count in world totals only. Per person: World Bank population of the same year.
- Livestock units: each country's FAOSTAT stocks in livestock units divided by its head count (2023); ducks take the chicken factor. The main animal has most livestock units; grid cells under one unit per km² have none.
- Concentration: the smallest share of land (Antarctica excluded) holding half of each animal, densest cells first.
- UK counties: county outlines rasterised ten times finer than the grid; each UK cell's animals shared among counties by area.
- Caveats: the grid is a model and a 2015 snapshot; FAOSTAT figures vary in quality; stocks are animals alive at once, not animals raised per year; livestock units are a rough common currency; wild animals, reindeer and fish are not included.

## How to rerun

Needs Python 3 with numpy, pandas, rasterio, scipy, shapely, pyproj, Pillow, matplotlib and fontTools, xelatex and pdftotext, and Playwright for the QA step. Raw inputs are read in place from the paths in `code/common.py`: the GLW 4 GeoTIFFs (`*_Da.tif`, `Areakm.tif`) from Harvard Dataverse, the FAOSTAT bulk downloads (QCL, EK, RL, normalised CSV, retrieved in 2026), World Bank population from github.com/datasets/population, and Natural Earth and UK county boundaries. Intermediate files go to `/dev/shm/livestock` (set `LSTMP` to change).

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

Hotham, T. (2026) Where the animals are: the world's cattle, sheep, goats, pigs, chickens and other farm animals, mapped every 10 km and counted by country, 1961 to 2024. Zenodo. https://doi.org/10.5281/zenodo.23842985

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
