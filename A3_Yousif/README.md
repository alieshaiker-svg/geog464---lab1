# Montreal Playgrounds MVP

Live map: https://alieshaiker-svg.github.io/464/site/
https://alieshaiker-svg.github.io/geog464---lab1/A2_Yousif/site/ 

This project is a small, browser-based map MVP for exploring playground locations in Montreal. It loads a local GeoJSON dataset, displays features categorized as **Aire de jeu - enfant**, and lets users click a playground to see its borough and type.

## Pre-flight report (Lab 7)

| Check | Result | What I did |
| --- | --- | --- |
| 1. Cold start | PASS: The map loaded correctly, with no fautls after the refresh.

| 2. Read every label | PASS | Checked the header, ranking panel, legend, popups, and other visible text for `undefined`, `null`, `NaN`, or `[object Object]`. |

| 3. Ask twice | PASS | Changed the selected borough more than once and checked that the playground count and ranking updated correctly. |

| 4. The edge | PASS | Tested an edge case and checked that the page responded clearly without leaving an incorrect old result or producing an error. |

| 5. The data does not come | PASS | Blocked one of the GeoJSON requests, refreshed, its gone or data couldnt load, then unblocked it, refreshed and it came back. |

| 6. On a phone | FAULT: Tested the live site on my phone. The page works, but some header, control, and ranking content extends beyond the screen and is clipped horizontally. So I pressed CTRL+SHIFT+M to change the dimension that suits a iphone 16 and then used copilot to help write a block of code to create the dimensions I want. |

| 7. Mouse in my pocket | PASS | Used Tab, Enter, and Space without the mouse to check whether the page controls could be reached and used from the keyboard. |

| 8. Accessibility audit | PASS | With a minor accesbility issue report of "Document does not have a main landmark, otherwise the score was a 98. |

## Source and licence

### Playground locations

- Dataset: Installations récréatives, sportives et culturelles extérieures
- Publisher: Ville de Montréal
- Source: [Ville de Montréal open data](https://www.donneesquebec.ca/recherche/dataset/vmtl-installations-recreatives-sportives-et-culturelles/resource/1c239e86-8b36-476c-bd51-91a3cd20f687)
- Date accessed: September 29, 2026
- Licence: CC BY 4.0

### Canopée

- Publisher: Ville de Montréal
- Source: [Canopée dataset](https://www.donneesquebec.ca/recherche/dataset/vmtl-canopee)
- Licence: CC BY 4.0
- Date accessed: October 23, 2026
- Source file used: `canopee-2019.geojson`

## MVP scope

- Show filtered playground locations on an interactive Leaflet map.
- Compare playgrounds by nearby tree-canopy coverage and show a 1 km canopy grid.
- Fit the map to the displayed playgrounds.
- Show playground borough, type, and 250 m canopy percentage in its popup.
- Report the number of playgrounds displayed.
- Filter displayed playgrounds by borough.

## Not in this iteration

- Exact walking-distance or routing calculations
- Census analysis of young children by borough
- Playground photos or additional park information
These features were left out of A2 so I could focus on making the borough-filter interaction and playground map work reliably first.

## Project layout

```text
A2_Yousif/
├── data/
│   ├── playgrounds.geojson
│   ├── playgrounds_canopy.geojson
│   ├── canopy_grid.geojson
│   ├── playground_grid.geojson
│   └── terrain_sport_ext.json
├── notebooks/
│   ├── A2_pipeline.ipynb
│   ├── lab5_playground_grid.ipynb
│   └── lab5_canopy_analysis.ipynb
├── site/
│   ├── app.js
│   ├── index.html
│   └── style.css
└── README.md
```

## Run the map

- Open the project folder in VS Code.
- Open site/index.html.
- Start it with Live Server.

## Data and map behavior

The A2 notebook reads `data/terrain_sport_ext.json`, a GeoJSON FeatureCollection with 3,476 features, and keeps the 1,008 features whose `TYPE` is exactly `Aire de jeu - enfant`. It validates the filtered output and writes `data/playgrounds.geojson`. The Lab 5 canopy notebook enriches those playgrounds with `canopy_pct_250m` and creates the canopy grid described below. The Leaflet site shows playground locations with their surrounding 250 m canopy percentage and the 1 km canopy grid as environmental context.

The map uses Leaflet 1.9.4 from the unpkg CDN and © OpenStreetMap contributors for its basemap.

## After the demo

At my demo, I was least confident explaining exactly how Leaflet's L.geoJSON turns GeoJSON features into interactive map layers.
The second layer now shows tree-canopy coverage per 1 km square so parents can compare playgrounds with the surrounding environment.

### Lab 5 method

The canopy dataset is the environmental second dataset, used to add context while keeping playgrounds as the main subject. The Canopée source coordinates and metadata indicate that the data is in EPSG:2950, so it was interpreted in that CRS for area calculations. Ten invalid geometries were repaired in memory only; the source file itself was not modified.

A regular 1 km × 1 km grid was created over the playground study area. Canopy polygons were combined to avoid double-counting overlaps, and the canopy area inside each grid square was measured. Coverage was calculated as canopy area / grid-cell area × 100. The final grid was converted to EPSG:4326 for Leaflet and written to `data/canopy_grid.geojson`.

The verified output contains 1,122 grid polygons, with canopy coverage from 0% to 79.47%. The map uses five classes based on the observed values: 0%, >0–<10%, 10–<20%, 20–<40%, and 40%+. Darker squares show 1 km areas with higher tree-canopy coverage.

### Five-second test

Neighbour answer — What is this map about?  
TO BE COMPLETED BY ME AFTER THE REAL TEST?

Neighbour answer — What do the darkest colours mean?  
TO BE COMPLETED BY ME AFTER THE REAL TEST?

## Limitations

- The map requires internet access for the basemap and externally hosted Leaflet files.
- The point layer displays one playground type and provides basic popups; the map does not include search or category controls.

## Testing evidence

I tested the borough dropdown by selecting different boroughs and checking that the map showed only the playgrounds in the selected borough and that the displayed count changed correctly; selecting Saint-Laurent showed 74 playgrounds. Browser verification also confirmed that both GeoJSON layers load, can be switched independently, and display their respective canopy percentage popups, and that the canopy legend is visible.

## AI disclosure

I used GitHub Copilot in VS Code in the Bring your own agent / Blue lane to help with the technical implementation of my Montréal playground project. Copilot helped me implement the Python filtering and validation code that reads terrain_sport_ext.json, keeps the features where TYPE is Aire de jeu - enfant, and writes the filtered result to playgrounds.geojson. It also helped me adapt the Leaflet site so it could load the processed GeoJSON and filter playgrounds by borough using the ARROND field. I reviewed the proposed code changes before accepting them and tested the final result by running the notebook, checking the feature counts and validation results, and selecting different boroughs on the map to confirm that the markers and displayed count changed correctly. I chose the project idea, audience, dataset, core action, scope, and the features to leave out of A2. I also wrote the README and project description myself. Copilot mainly supported the coding and implementation, while the project decisions, testing, written explanation, and final review remained my own.

I used GitHub Copilot in VS Code through GitHub Education. I did not record which specific model was being used.

## A3 feature

My map is designed for parents with young children who want to compare playgrounds in Montréal. The current version lets users select a borough, view playground locations, and see nearby tree-canopy coverage. For A3, the ranking panel orders playgrounds in the selected borough by `canopy_pct_250m`, from highest to lowest, and shows the canopy percentage rounded to one decimal place. Only playgrounds with numeric canopy data are ranked, and the panel shows at most the top 10.

### A3 test cases

#### Test 1 — Ranking appears for a borough
**Action:** Select Saint-Laurent from the borough menu.
**Expected result:** A list titled “Greenest playground surroundings” appears, ordered from highest to lowest `canopy_pct_250m`. It contains no more than 10 playgrounds and shows each actual canopy percentage to one decimal place.

#### Test 2 — Ranking updates when the borough changes
**Action:** Change the selected borough from Saint-Laurent to another borough.
**Expected result:** The list refreshes using only playgrounds in the newly selected borough, sorted by `canopy_pct_250m`; no playgrounds from the previous borough remain.

#### Test 3 — Missing canopy data
**Action:** A playground has a null, missing, or non-numeric `canopy_pct_250m` value.
**Expected result:** It is excluded from the ranking, and the map and remaining rankings continue working without an error.

### A3 test results

#### Test 1 — Ranking appears for a borough
**Result:** PASS — Tested on November 3, 2026. Selecting Saint-Laurent displayed a Top 10 ranking of Saint-Laurent playgrounds ordered from highest to lowest `canopy_pct_250m`. The visible ranking began at 42.5% and decreased from there.

#### Test 2 — Ranking updates when the borough changes
**Result:** PASS — Tested on November 3, 2026. Changing the borough from Saint-Laurent to Anjou refreshed both the playground count and the ranking. The Anjou ranking showed only Anjou playgrounds and was ordered from highest to lowest canopy percentage.

#### Test 3 — Missing canopy data
**Result:** PASS — Programmatically verified on November 3, 2026 using test data. Missing, null, and non-numeric canopy values were excluded from the ranking rather than treated as zero, and the page continued working without a JavaScript error.