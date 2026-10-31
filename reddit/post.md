## Title

[OC] There are 3.4 chickens for every person on Earth. Here is the main farm animal in every 10 km square of the planet

## Body

I mapped the world's farm animals using the FAO's Gridded Livestock of the World (a 10 km model of cattle, buffaloes, sheep, goats, pigs, chickens, ducks and horses in 2015) and FAOSTAT's country counts from 1961 to 2024. Each square is coloured by the animal with the most livestock units, so a cow outweighs a chicken. In 2024 there were about 35.3 billion farm animals alive at once for 8.1 billion people. Chickens have multiplied 7.1 times since 1961; farm mammals outnumber people in 40 countries, led by Mongolia (16.4 per person); China has 44% of the world's pigs and India 53% of its buffaloes. New Zealand has lost two thirds of its sheep since 1982. Caveats: the grid is a model that spreads census counts over the land, and it is a 2015 snapshot; stocks are animals alive at one time, not animals raised per year. Interactive map, where you can switch animals and zoom to your own area: https://maps.tristanhotham.com/livestock-map/

## Source comment

Source: FAO Gridded Livestock of the World v4, 2015 layers (Gilbert et al. 2018, Scientific Data; Harvard Dataverse doi:10.7910/DVN/LHBICE and companions, CC BY 4.0); FAOSTAT livestock stocks, livestock units and land use, 1961 to 2024 (FAO, CC BY 4.0); World Bank population (CC BY 4.0); Natural Earth outlines (public domain).

Tools: Python (numpy, rasterio, pandas, matplotlib); Leaflet for the interactive map.

Interactive version: https://maps.tristanhotham.com/livestock-map/
Paper: {{DOI_URL}}
Blog post: https://blog.tristanhotham.com/2026/10/31/livestock-map/
