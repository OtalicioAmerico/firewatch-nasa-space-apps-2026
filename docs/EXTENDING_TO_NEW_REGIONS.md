# Extending Firewatch to other states or countries

**Status: not implemented.** Firewatch works today for **one region, Tocantins (Brazil), 2021-2025**, with MODIS
(Terra, Aqua) and VIIRS NOAA-20. Nothing in this repository has been run for another region, and the application does
**not** adapt automatically. This guide lists what is region-specific and what a developer would have to change. Every
step below is a **proposal**, not tested procedure.

## What is already general (by design, not verified on other regions)
- The scientific engine in `firecal/` (cell-day indicators, extent/intensity, coverage states, agreement K, historical
  reference) takes a region object (`firecal/geo.py`): a rectangle (`Region.rectangle`) or the union of IBGE
  municipalities whose code starts with a given UF code (`region_from_ibge_municipios`). It contains no Tocantins
  constants, but its tests were only run with Tocantins data.
- The 0.25 degree grid, the fixed 7-day weeks, the rules of the coverage scenarios and the exporter schema are not tied to
  a place.

## What is hard-wired to Tocantins today
| Where | What is fixed | What to change |
|---|---|---|
| `tools/aquisicao/historico_firms.py` | bounding box `(-51.0, -13.75, -45.5, -4.9)`, products `MODIS_SP` + `VIIRS_NOAA20_SP`, period 2021-2025 (1,826 days) | box, products, dates; the request plan and expected counts derive from them |
| `tools/historico/importar.py`, `cobertura_celulas.py`, `cobertura_cmr.py` | `region_from_ibge_municipios(..., "17", "Tocantins")` (IBGE UF code 17) | the UF code and name; outside Brazil you need a different boundary source and reader |
| `tools/pesquisa/cmr_*.py` | CMR collections for Aqua, Terra and NOAA-20 (`N20`); the bounding box is a parameter | satellites if you add NOAA-21 / Suomi-NPP |
| `firecal/calendario.py`, `harmonize.py` | satellite families `Terra`/`Aqua` -> MODIS, `N20` -> VIIRS | the table, if other satellites are added (the method was not evaluated for them) |
| `tools/mock_geo/gerar_geometria_tocantins.py`, `web/src/geo/` | simplified Tocantins boundaries from IBGE | regenerate for the new region; outside Brazil use another open boundary source and attribute it |
| `web/src/geo/region.ts`, `web/src/services/realDataSource.ts`, `web/src/pages/OverviewPage.tsx`, `web/src/i18n/*.json` | region id/name, map bounds, Tocantins wording in texts | region metadata and text keys |
| `tools/export_web/*`, `tools/historico/analise_m05.py`, `processar.py` | region label and some Tocantins-specific summaries | labels; check the summaries |
| `docs/` results and the README numbers | Tocantins results | recompute; never reuse them for another region |

## Suggested procedure (proposal, untested)
1. Fork the repository; replace the Ikarus Aurora logo and brand strings (see `BRAND_AND_RIGHTS.md`).
2. Decide the region, period and products; get your own FIRMS MAP_KEY (README, step 3).
3. Obtain boundaries with an open licence; adapt `firecal/geo.py` loading if the source is not IBGE.
4. Parameterise (or copy and edit) the acquisition and processing scripts listed above; run them as in README step 4.
5. Check that the coverage assumptions still hold: CMR granule collections, product versions (MODIS versions changed
   during 2021-2025 in this study), catalogue gaps, and the number of reference years.
6. Export (`exportar_web.py`), validate (`validar_export.py`), then update the web region files and texts.
7. Re-read the limitations in the README. A different region, climate or sensor set may break assumptions that were never
   tested (for example 0.25 degree cells saturating on very active days, or too few reference years per version block).

## Honest limits
No scientific validation exists even for Tocantins. Do not present results for another region as validated, and do not
mix MODIS and VIIRS counts into a combined score.
