# Montreal Playgrounds MVP

Live map:
https://alieshaiker-svg.github.io/geog464---lab1/A3_Yousif/site/ 

## A3 feature

My map is designed for parents with young children who want to compare playgrounds in Montréal. The current version lets users select a borough, view playground locations, and see nearby tree-canopy coverage. For A3, the ranking panel orders playgrounds in the selected borough by `canopy_pct_250m`, from highest to lowest, and shows the canopy percentage rounded to one decimal place. Only playgrounds with numeric canopy data are ranked, and the panel shows at most the top 10.

## A3 feature explanation

The main A3 ranking feature is implemented in `site/app.js`. Lines 29–32 read and validate each playground's `canopy_pct_250m` value. Lines 40–142 build the ranking panel. Within that section, lines 49–66 remove playgrounds without valid canopy data, sort the remaining playgrounds from highest to lowest canopy coverage, and keep only the Top 10.

For the Part 3 usability fix, lines 80–120 make each ranked playground interactive. When a ranking item is selected, the code finds its matching Leaflet marker, highlights it, moves the map to that location, and opens its popup. Lines 228–239 add the same playground ID to the popup so it can be matched to the ranking.

Lines 275–297 handle the borough interaction. When the borough changes, the playgrounds are filtered to that borough and the ranking is rebuilt using the filtered features.

I understand how the filtering, sorting, Top 10 selection, and ranking-to-marker interaction work. I am still less confident about how Leaflet manages the GeoJSON feature objects and their corresponding marker layers internally.

### A3 test cases (Lab 6)

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


## Pre-flight report (Lab 7)

| Check | Result | What I did |
| --- | --- | --- |
| 1. Cold start | PASS | Opened the live site in a private window and refreshed it. The map loaded correctly with no console faults. |
| 2. Read every label | PASS | Checked the header, ranking panel, legend, popups, and other visible text for `undefined`, `null`, `NaN`, or `[object Object]`. |
| 3. Ask twice | PASS | Changed the selected borough more than once and checked that the playground count and ranking updated correctly. |
| 4. The edge | PASS | Tested an edge case and checked that the page responded clearly without leaving an incorrect old result or producing an error. |
| 5. The data does not come | PASS | Blocked one of the GeoJSON requests and refreshed the page to test the failure case. I then unblocked the request and refreshed again, and the data loaded normally. |
| 6. On a phone | PASS — fixed | The first phone test showed horizontal clipping in the header, controls, and ranking panel. I updated the mobile CSS and retested the live page at phone size and on my phone. The content now fits within the viewport without horizontal overflow. |
| 7. Mouse in my pocket | PASS | Used Tab, Enter, and Space without the mouse to check whether the page controls could be reached and used from the keyboard. |
| 8. Accessibility audit | PASS — minor issue noted | Ran Lighthouse Accessibility in mobile mode. The site scored 98/100. Lighthouse reported one issue: "Document does not have a main landmark." |


## Part 3: what I found, and one fix

**Evidence:** During usability testing, one tester tried clicking ranked playgrounds but nothing happened. Another tester used the greener canopy squares around playground markers instead of clearly connecting the Top 10 ranking to a specific playground on the map.

**Severity:** 2 — this slowed users down because they could identify which playground ranked highest in the list but could not easily identify its corresponding location on the map.

**My change:** I made each Top 10 ranking item interactive so selecting it moves the map to that playground, highlights the corresponding marker, and opens its popup with the matching playground ID.

**Recheck:** Give the same greener-surroundings task to someone new using the live site without helping them. Fixed means they can use the ranking and identify the corresponding playground on the map without hesitating at this point.

**Before:** `screenshots/before.png`

**After:** `screenshots/after.png`

**The one fix I made:** I made the Top 10 ranking items interactive so selecting a ranked playground moves the map to that playground, highlights the matching marker, and opens its popup with the same playground ID.

**Recheck result:** A new tester used the live site and was able to select the highest-ranked playground and identify its corresponding location on the map without help. The fix worked.


### Lab 5 method

The canopy dataset is the environmental second dataset, used to add context while keeping playgrounds as the main subject. The Canopée source coordinates and metadata indicate that the data is in EPSG:2950, so it was interpreted in that CRS for area calculations. Ten invalid geometries were repaired in memory only; the source file itself was not modified.

A regular 1 km × 1 km grid was created over the playground study area. Canopy polygons were combined to avoid double-counting overlaps, and the canopy area inside each grid square was measured. Coverage was calculated as canopy area / grid-cell area × 100. The final grid was converted to EPSG:4326 for Leaflet and written to `data/canopy_grid.geojson`.

The verified output contains 1,122 grid polygons, with canopy coverage from 0% to 79.47%. The map uses five classes based on the observed values: 0%, >0–<10%, 10–<20%, 20–<40%, and 40%+. Darker squares show 1 km areas with higher tree-canopy coverage.


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

## Project scope

- Show filtered playground locations on an interactive Leaflet map.
- Compare playgrounds by nearby tree-canopy coverage and show a 1 km canopy grid.
- Fit the map to the displayed playgrounds.
- Show playground borough, type, and 250 m canopy percentage in its popup.
- Report the number of playgrounds displayed.
- Filter displayed playgrounds by borough.
- Rank up to the Top 10 playgrounds in the selected borough by nearby tree-canopy coverage within 250 m.

## Project layout

```text
A3_Yousif/
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
├── screenshots/
│   ├── before.png
│   └── after.png
├── site/
│   ├── app.js
│   ├── index.html
│   └── style.css
└── README.md
```

## Data and map behavior

The A2 notebook reads `data/terrain_sport_ext.json`, a GeoJSON FeatureCollection with 3,476 features, and keeps the 1,008 features whose `TYPE` is exactly `Aire de jeu - enfant`. It validates the filtered output and writes `data/playgrounds.geojson`. The Lab 5 canopy notebook enriches those playgrounds with `canopy_pct_250m` and creates the canopy grid described below. The Leaflet site shows playground locations with their surrounding 250 m canopy percentage and the 1 km canopy grid as environmental context.

The map uses Leaflet 1.9.4 from the unpkg CDN and © OpenStreetMap contributors for its basemap.


## Limitations

- The map requires internet access for the basemap and externally hosted Leaflet files.
- The point layer displays one playground type and provides basic popups; the map does not include search or category controls.


## AI disclosure

I used GitHub Copilot in VS Code through GitHub Education in the Bring your own agent / Blue lane to help with the technical implementation of my A3 feature. I did not record which specific model was being used.

For A3, I asked Copilot to help add a ranking panel that compares playgrounds in the selected borough using nearby tree-canopy coverage. An early version introduced a heat-exposure proxy and a combined environmental suitability score, which was not what I wanted for the project, so I rejected that approach and changed the feature to use only the existing `canopy_pct_250m` field. The final version filters out playgrounds without valid canopy values, sorts the remaining playgrounds from highest to lowest canopy coverage, and displays up to the Top 10 for the selected borough.

I also used Copilot to help improve the mobile responsive layout after testing showed that some headings, controls, and ranking content were clipped on a phone. I reviewed the suggested CSS changes and tested the updated site again on a mobile-sized browser view and on my phone.

I reviewed and tested the code rather than accepting the generated changes without checking them. I ran the three A3 test cases, including the missing-canopy edge case, and completed the Lab 7 pre-flight checks on the live GitHub Pages site. The project idea, intended audience, decision to rank playgrounds using tree canopy only, A3 test cases, usability-test plan, and final project decisions remained my own.

For Part 3, I gave Copilot the usability-testing evidence that users could see the ranking but had difficulty connecting a ranked item to its map marker. I asked it to make the smallest focused change without altering the ranking calculation. Copilot made the ranking items interactive, added matching IDs to the popups, and added subtle hover/focus styling. I tested the result by clicking different ranked items, using Tab, Enter and Space, checking the matching ID and highlighted marker, and rechecking the live site with another user.