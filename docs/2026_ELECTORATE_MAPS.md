# Victorian geographic electorate maps

The Electorate maps tab offers statewide Assembly, Greater Melbourne, inner Melbourne and the eight Legislative Council regions. Mobile-friendly zoom and reset buttons work in each view. Statewide regional presets cover Geelong, Ballarat, Bendigo, Shepparton, Mildura, Warrnambool, Wodonga and the Latrobe Valley. The statewide Assembly layers display the 27 November experimental forecast and contest closeness. The Council map displays region boundaries and opens the Upper House analysis. Greater Melbourne retains its existing held-seat layer. Each map has a keyboard-accessible selector.

The [VEC boundary review](https://vec.vic.gov.au/electoral-boundaries/state-boundary-reviews) and [Electoral Boundaries Commission](https://ebc.vic.gov.au/Past-Redivisions/Default.html) identify the 2021 redivision as current for 2026. The two GeoJSONs in the public archive have no explicit CRS member. Their coordinates are longitude and latitude in Victoria. The Assembly district and Council region names reconcile one-for-one to the project's 2026 membership registry. Geographic boundary codes are preserved in the asset. The restricted VEC media feed's separate contest identifiers are outside this crosswalk.

The generator validates each polygon and shared edges before and after simplifying and quantising the coverage. It records the public archive SHA-256 and projects approximate regional-centre coordinates after checking they fall within Assembly boundaries. The site serves only the simplified path asset. Inputs are the [VEC public geographic ZIP](https://vec.vic.gov.au/-/media/f67f3c2562c9439c880150ede051991f.zip) and the State of Victoria's [Assembly](https://discover.data.vic.gov.au/dataset/vicmap-admin-state-assembly-polygon-2022) and [Council](https://discover.data.vic.gov.au/dataset/vicmap-admin-state-council-polygon-2022) Vicmap datasets. The source data and published adaptation are attributed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

To rebuild with Shapely 2.2 (GEOS 3.12 or later), run:

```sh
python scripts/build-election-state-maps.py /path/to/state_assembly_and_council_2022.zip
python scripts/build-election-state-maps.py /path/to/state_assembly_and_council_2022.zip --check
```
