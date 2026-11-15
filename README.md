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

## Run it and reproduce
Prerequisites: Python >= 3.10 (standard library only) and Node >= 22.

```bash
# scientific engine tests (147 tests; 28 are skipped when the NASA data are absent)
python -m unittest discover -s tests -t .

# scientific engine and web exporter (need the NASA FIRMS data you download yourself; see docs)
python -I tools/export_web/exportar_web.py --bruto <raw.db> --resultados <results_m05.db> --saidas <outputs_m05> --saida web/public/data/real
python -I tools/export_web/validar_export.py --bruto <raw.db> --saidas <outputs_m05> --export web/public/data/real

# web application
cd web
npm ci --ignore-scripts
npm run dev                     # http://127.0.0.1:5173
npm run lint && npx tsc -b && npm test && npm run build
```

Without `web/public/data/real` the application shows "data not available" instead of any substitute data (8 data-dependent
web tests are then not defined: 39 run and pass; 47 with the derived data). To download FIRMS data you need your own
`FIRMS_MAP_KEY` (environment variable only; it is never written to files); see `tools/aquisicao/`.

## Tests
- Python: 147 tests (28 skipped without data), standard library `unittest`.
- Web: 39 tests without data (47 with the derived data) using the Node test runner; `oxlint` and `tsc -b` run clean.

## Licence and attributions
- **Code:** MIT, Copyright (c) 2026 Otalicio Americo de Melo Junior (Ikarus Aurora). See [`LICENSE`](LICENSE).
- **Ikarus Aurora** is the project owner's authorial development identity, **not a registered company**. Its logos and
  visual identity are **reserved** and not covered by MIT: [`BRAND_AND_RIGHTS.md`](BRAND_AND_RIGHTS.md).
- **Third-party software:** [`web/public/THIRD_PARTY_NOTICES.txt`](web/public/THIRD_PARTY_NOTICES.txt) (React, MapLibre GL,
  lucide-react, Inter font under OFL-1.1, and others).
- **NASA data:** *We acknowledge the use of data and/or imagery from NASA's Fire Information for Resource Management
  System (FIRMS) (https://earthdata.nasa.gov/firms), part of NASA's Earth Science Data and Information System (ESDIS).*
  NASA Earthdata CMR metadata. NASA does not endorse this project.
- **IBGE data:** Source: IBGE, *Malha Municipal Digital 2025*, provided under a licence compatible with Creative Commons
  BY 4.0. The geometry here is simplified and processed; it is not the official mesh.
- More: [`docs/LICENCAS_E_ATRIBUICOES.md`](docs/LICENCAS_E_ATRIBUICOES.md) (Portuguese).

## Team
- **Otalicio Americo de Melo Junior ("Junior")** - project owner; problem choice, direction, development and integration.
- **David** - critical review of the evidence.
- **Tony** - public-utility perspective and fit to the challenge.

## Use of AI
Anthropic's **Claude Code** (model Claude Sonnet 5.5) was used, under the team's direction, to write and review code
(scientific engine, tests, web application), analysis scripts, documentation and the deployment procedure. This code and
these texts are therefore AI-assisted or AI-generated, and are acknowledged as such here, in `package.json`, and in
[`AI_DISCLOSURE.md`](AI_DISCLOSURE.md). No scientific conclusion was validated by AI. The team's human contributions
and the exact scope of AI help are described in `AI_DISCLOSURE.md`.
