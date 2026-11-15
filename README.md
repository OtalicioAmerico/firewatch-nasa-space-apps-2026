# Firewatch - Harmonization of MODIS and VIIRS Hot Spots

**NASA Space Apps Challenge 2026** - challenge *Harmonization of MODIS and VIIRS Hot Spots*
(listed on the event site as [*MODIS and VIIRS Hot Spots*](https://www.spaceappschallenge.org/2026/challenges/modis-and-viirs-hot-spots/)).

- **Live application:** https://firewatch.ikarusaurora.tech (Portuguese by default, English available)
- **Source code:** https://github.com/OtalicioAmerico/firewatch-nasa-space-apps-2026 (MIT, see [Licence and attributions](#licence-and-attributions))

> **Independent project. Not developed, endorsed or validated by NASA.** NASA data are used under their open data
> policy; this is not an official NASA product.
> **Experimental and not scientifically validated.** A thermal detection is an anomaly flag, **not a confirmed fire**.
> Firewatch does not predict fires, does not count fires, and no result here has been validated by independent
> evidence or external expert review.

## The scientific problem
MODIS (Terra, Aqua; ~1 km pixels) and VIIRS (here on NOAA-20; 375 m pixels) both report thermal
anomalies ("hot spots"), but they do not see the same land in the same way: pixel size, overpass time and swath coverage
differ, product versions change over the years, and the catalogue of observations has gaps. A plain count of hot spots
mixes all of that. Adding MODIS and VIIRS counts, or reading "no detection" as "no fire", is misleading.

## The solution
Firewatch is a **historical calendar** (2021-2025, state of Tocantins, Brazil) that **keeps each sensor separate** and
makes the differences between them visible instead of hiding them. For any day it shows:

- **Spatial extent** - the share of observed 0.25 degree cells with at least one detection (numerator and denominator
  always shown) - and **intensity** (detections per active cell), per sensor, next to the **raw detections**.
- **Observation coverage** per satellite and cell, estimated from NASA CMR granule footprints; conflicts between FIRMS
  records and the catalogue are flagged, never hidden. Absence of detections is never read as absence of fire.
- **Spatial agreement** between sensors (Jaccard index K, with its chance level), shown **only** on days when both
  sensors could observe; otherwise "N/A".
- The position of each week or month against the **available historical reference** (always excluding the evaluated
  year; "insufficient reference" when fewer than two comparison years exist).
- An **Evidence Explorer**: for a cell and day, every individual FIRMS detection (UTC time, coordinates, FRP,
  confidence, pixel size, product version) with the SHA-256 and line number of the imported source file.
- Two coverage scenarios: **A (conservative)** and **B (exploratory, default)**.
- A map of Tocantins (cells, municipalities, individual detections), Portuguese and English interface, light and dark
  themes.

## Data sources
- **NASA FIRMS** archive downloads (standard products): MODIS Terra and Aqua (version labels observed: 6.03 for
  2021-2022 and 61.03 for 2023-2025; their equivalence with a specific collection is **not** confirmed) and VIIRS
  NOAA-20 375 m (version 2).
- **NASA Earthdata CMR**: granule footprints and counts, used only to estimate geometric coverage.
- **IBGE** - *Malha Municipal Digital 2025*: Tocantins and municipality boundaries, **simplified** for display (not the
  official IBGE mesh). Source: IBGE.

Raw NASA files, the research SQLite databases and the large derived JSON files are **not stored** in this repository.
How they were obtained and derived is described in
[`docs/RESULTADO_AQUISICAO_HISTORICA_2021_2025.md`](docs/RESULTADO_AQUISICAO_HISTORICA_2021_2025.md),
[`docs/VALIDACAO_DADOS.md`](docs/VALIDACAO_DADOS.md) and [`docs/PROVENIENCIA.md`](docs/PROVENIENCIA.md)
(supplementary technical notes, written in Portuguese). The published results can be explored in the live
application, which serves the derived files (with a `MANIFEST.json` of SHA-256 hashes).

## Scientific method
1. **Sensors are never merged into a combined score.** Each sensor is reduced independently to a cell-day indicator on
   a 0.25 degree grid (presence, count, intensity).
2. **Extent is normalised by the area actually covered**, using CMR granule footprints; coverage state and detection
   state are kept separate.
3. **Comparison between sensors (K)** is allowed only where coverage is comparable on that day.
4. **Weeks are fixed 7-day blocks** (not ISO weeks); the **historical reference excludes the evaluated year**, and MODIS
   is compared only inside its own product-version block.
5. Records are traceable to the source file by SHA-256 and line number; nothing is silently dropped.

Details: [`docs/METODO_HARMONIZACAO.md`](docs/METODO_HARMONIZACAO.md) and
[`docs/RESULTADOS_MISSAO_05.md`](docs/RESULTADOS_MISSAO_05.md) (Portuguese).

## Results obtained (Tocantins, 2021-01-01 to 2025-12-31, 1,826 days)
- 1,154,932 unique detections in the acquired area; **602,856** inside Tocantins (MODIS 122,496; NOAA-20 480,360).
- Median daily extent (scenario B): MODIS 2.3 %-3.8 %, VIIRS 5.1 %-9.2 % of observed cells depending on the year. VIIRS
  occupies about 2-3 times more cells than MODIS, so raw counts of the two sensors are **not comparable**.
- Extent and intensity change the reading of about 18-22 % of the weeks compared with a plain count (example: MODIS
  block 47/2023 has 163 detections, *below* the available reference, while its extent is *above* it).
- Spatial agreement exists above chance (K roughly 4-5 times the chance level) but depends on activity level, and is
  withheld on days without comparable coverage. Scenarios A and B differ on very few days.
- A FIRMS x CMR conflict (Terra, 13-16 May 2025) is detected and flagged.

## Limitations and uncertainty
Five years of history; the MODIS reference per version block has only 1-2 years; CMR coverage is geometric (not
cloud-free) and the catalogue has gaps; 0.25 degree cells saturate on very active days; K is not a reliability measure
and depends on activity; one region only; no independent validation (burned area, imagery) and no external expert review
yet. Part of the data (FIRMS acquisition and an exploratory comparison of sensors) was prepared the day before the
event; see [`docs/PROVENIENCIA.md`](docs/PROVENIENCIA.md). "Experimental" and "Not validated" are shown in the interface.

## Install, test and reproduce
Everything below is **implemented and used to produce the published Tocantins results**. Prerequisites: Python >= 3.10
(standard library only, nothing to install) and Node >= 22 / npm.

### 1. Install and run the application
```bash
git clone https://github.com/OtalicioAmerico/firewatch-nasa-space-apps-2026.git
cd firewatch-nasa-space-apps-2026/web
npm ci --ignore-scripts
npm run dev                     # http://127.0.0.1:5173
npm run lint && npx tsc -b && npm test && npm run build
```
Without the derived data in `web/public/data/real` (see step 5) the application shows "data not available" instead of any
substitute data.

### 2. Run the tests
```bash
python -m unittest discover -s tests -t .      # from the repository root
cd web && npm test
```
| Suite | Runs without NASA data | Needs the real data (not in this repository) |
|---|---|---|
| Python (147 tests) | 119 pass (engine, matching, coverage rules, calendar maths, importers, hygiene) | 28 are **skipped**: 18 need `NASA_DATA_DIR` (a folder with the downloaded FIRMS files and IBGE shapefiles: `test_poc_real`, `test_regressao_missao01`) and 10 need `FIRECAL_BANCO_DIR` + `FIRECAL_GRANULOS` (the research SQLite databases and the CMR granule JSON: `test_m05_real`) |
| Web (`npm test`) | 39 pass (interface logic, i18n, simulated source) | 8 more run only when `web/public/data/real/meta.json` exists (`real.test.ts`, the exported derived data): 47 in total |

A green run therefore proves the software on fictitious/simulated inputs; the real-data tests are what check the
published numbers, and they can only run after you reproduce the data (steps 3-5).

### 3. Get your own NASA FIRMS key and acquire data
FIRMS downloads need a free **MAP_KEY** that you request from NASA FIRMS (https://firms.modaps.eosdis.nasa.gov/api/map_key/). Put it in an environment variable only: it is never read from files and never printed or logged.
```bash
export FIRMS_MAP_KEY=<your key>                     # PowerShell: $env:FIRMS_MAP_KEY = '<your key>'
python -I tools/aquisicao/sondagem_firms.py --plan       # no network, no key: shows the plan
python -I tools/aquisicao/sondagem_firms.py --check-key  # key status and quota (numbers only)
python -I tools/aquisicao/historico_firms.py --plan
python -I tools/aquisicao/historico_firms.py --run --out <folder outside Git> [--workers 3]
```
`historico_firms.py` downloads MODIS (`MODIS_SP`) and VIIRS NOAA-20 (`VIIRS_NOAA20_SP`) standard products for Tocantins,
2021-01-01 to 2025-12-31, in windows of up to 5 days, with a persistent manifest (SHA-256 of every response),
resumable runs and a conservative local rate limit. The region and the period are fixed in the script (see
[`docs/EXTENDING_TO_NEW_REGIONS.md`](docs/EXTENDING_TO_NEW_REGIONS.md)). Downloaded files must stay **outside** the repository.

### 4. Process the data and reproduce the Tocantins results
Download the IBGE *Malha Municipal Digital 2025* shapefile `BR_Municipios_2025` yourself and place it as
`<IBGE dir>/IBGE_2025/municipios/BR_Municipios_2025.{shp,dbf}`. Then, in this order (each script's header documents its
arguments; paths are your own folders, outside Git):
```bash
# a) NASA CMR granule footprints and global granule counts (read-only public catalogue, no key)
python -I tools/pesquisa/cmr_granulos_periodo.py --ini 2021-01-01 --fim 2025-12-31 --bbox -51.0,-13.75,-45.5,-4.9 --saida granulos.json
python -I tools/pesquisa/cmr_contagem_global.py --ini 2021-01-01 --fim 2025-12-31 --saida contagem_global.json
# b) import the validated FIRMS files into a local SQLite database
python tools/historico/importar.py --dados <acquisition dir> --banco bruto.db --ibge <IBGE dir>
# c) coverage per cell and satellite-day (writes into a separate results database)
python tools/historico/cobertura_celulas.py --bruto bruto.db --resultados resultados.db --granulos granulos.json --ibge <IBGE dir> --contagem contagem_global.json
# d) calendar indicators, scenarios A/B, spatial agreement K and historical reference
python tools/historico/calendario.py --bruto bruto.db --resultados resultados.db --granulos granulos.json --saida saidas
python tools/historico/analise_m05.py --saidas saidas --resultados resultados.db --bruto bruto.db
```
Note: the order above follows the scripts' documented inputs and outputs. The complete chain was run by the team during
the event; it was **not re-run end to end from this public repository**, so expect small path or argument adjustments.
Set `FIRECAL_BANCO_DIR` and `FIRECAL_GRANULOS` (and `NASA_DATA_DIR`) to enable the data-dependent tests.

### 5. Export the JSON for the front end
```bash
python -I tools/export_web/exportar_web.py --bruto bruto.db --resultados resultados.db --saidas saidas --saida web/public/data/real
python -I tools/export_web/validar_export.py --bruto bruto.db --saidas saidas --export web/public/data/real
cd web && npm run build
```
The exporter does not recompute the method: it reuses the engine, checks day by day that the cell-level sets reproduce
the daily totals, and writes `MANIFEST.json` with the SHA-256 of every file. `web/public/data/real` is ignored by Git.
The simplified boundaries in `web/src/geo/` come from `tools/mock_geo/gerar_geometria_tocantins.py`.

### 6. Other states or countries
**Not automatic.** The method (`firecal/`) is region-independent in design, but the acquisition scripts, the processing
tools, the boundary files, the satellite list and the web interface are currently wired to Tocantins. What would need to
change, and what has never been tested, is listed in
[`docs/EXTENDING_TO_NEW_REGIONS.md`](docs/EXTENDING_TO_NEW_REGIONS.md). Contributions: [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Licence and attributions
- **Code:** MIT, Copyright (c) 2026 Otalicio Americo de Melo Junior (Ikarus Aurora). See [`LICENSE`](LICENSE). The generic
  Aurora design tokens (`web/src/design/aurora/`) are also MIT.
- **Ikarus Aurora** is the project owner's authorial development identity, **not a registered company**. Its **logos and
  brand are reserved** and are not covered by MIT, but they are isolated in two places so that any fork can replace them
  and build, run and reproduce everything: [`BRAND_AND_RIGHTS.md`](BRAND_AND_RIGHTS.md).
- **Third-party software:** [`web/public/THIRD_PARTY_NOTICES.txt`](web/public/THIRD_PARTY_NOTICES.txt) (React, MapLibre GL,
  lucide-react, Inter font under OFL-1.1, and others), each under its own licence.
- **NASA data:** *We acknowledge the use of data and/or imagery from NASA's Fire Information for Resource Management
  System (FIRMS) (https://earthdata.nasa.gov/firms), part of NASA's Earth Science Data and Information System (ESDIS).*
  NASA Earthdata CMR metadata. NASA does not endorse this project; NASA data keep their own terms.
- **IBGE data:** Source: IBGE, *Malha Municipal Digital 2025*, provided under a licence compatible with Creative Commons
  BY 4.0. The geometry here is simplified and processed; it is not the official mesh.
- More: [`docs/LICENCAS_E_ATRIBUICOES.md`](docs/LICENCAS_E_ATRIBUICOES.md) (Portuguese).

## Team
- **Otalicio Americo de Melo Junior ("Junior")** - project owner; problem choice, direction, development and integration.
- **David** - critical review of the evidence.
- **Tony** - public-utility perspective and fit to the challenge.

(Only the roles above are recorded; no other claim is made about individual contributions.)

## Originality and prior work (full disclosure)
- **Before the event (2026-11-13):** the NASA FIRMS data acquisition and an exploratory research study comparing MODIS
  and VIIRS were prepared in an earlier private project of the same owner. They are used as input and reference only; the
  conclusions were treated as hypotheses and re-verified (see `docs/PROVENIENCIA.md`, `docs/VALIDACAO_DADOS.md`).
- **During the event (2026-11-14 to 2026-11-15):** this repository's scientific engine, tools, tests, calendar results,
  web application and documentation were developed.
- **Pre-existing, reused components of the owner:** the Aurora design tokens and one Ikarus Aurora logo mark.
- Whether work prepared on 2026-11-13 is compatible with the event rule that teams may not start working on the challenge
  before the hackathon is an open question that the team will clarify with its Local Lead.

## Use of AI (Super Intelligence)
Two AI tools were used, under human direction. Full details: [`AI_DISCLOSURE.md`](AI_DISCLOSURE.md).
- **Claude Code** (Anthropic, Claude Sonnet 5.5): AI-assisted software implementation and testing, scripts, web
  application, documentation and the deployment procedure.
- **ChatGPT** (OpenAI): structuring the development instructions given to Claude Code, research and planning support,
  review of scientific interpretations and analytical results, and drafting or revising documentation and presentation
  materials. We do not claim that ChatGPT directly authored source code.

The code and texts of this repository are therefore AI-assisted or AI-generated and are acknowledged as such here, in
`package.json` and in `AI_DISCLOSURE.md`. The choice of the challenge and of the approach was made by the human team. No
scientific conclusion was validated by AI, and no independent human scientific validation has taken place.
