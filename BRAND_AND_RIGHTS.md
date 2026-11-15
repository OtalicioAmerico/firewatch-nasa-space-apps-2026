# Brand, rights and licensing scope

This file separates the different kinds of material in this repository, because
a single MIT licence does not apply to all of them.

## 1. Source code (MIT)
The original source code (`firecal/`, `tools/`, `tests/`, `config/`, `web/src`
except the items below, and the documentation text) is licensed under the MIT
licence in [`LICENSE`](LICENSE). Copyright (c) 2026 Otalicio Americo de Melo
Junior (Ikarus Aurora).

## 2. "Ikarus Aurora" is an authorial development identity
**Ikarus Aurora is not a registered company, legal entity or registered
trademark.** It is the development identity created and used by the project
owner, Otalicio Americo de Melo Junior, who is the author and holder of the
rights over the Ikarus Aurora logos, visual components and original design
elements. No company registration number, corporate name or trademark
registration is claimed anywhere in this repository.

## 3. Logos and brand (rights reserved; everything else can be forked)
* **Reserved (not under MIT):** the Ikarus Aurora wing mark (file
  `web/src/assets/brand/ikarus-wing-white.svg`), the name "Ikarus Aurora" used as a logo or brand, and the Ikarus Aurora
  brand identity. The owner confirms that these remain reserved.
* Publishing the code under MIT **does not** transfer their ownership and **does not** grant a right to use these marks
  to present your own product as Ikarus Aurora's.
* **This reservation does not restrict reproduction, study, modification or forking of the project.** The marks appear
  only in three places: the SVG file above, `web/src/components/Brand.tsx` (which imports it) and the `brand.*` keys of
  `web/src/i18n/en-US.json` and `pt-BR.json`. To publish your own version, replace those with your own identity; the
  build, tests and the scientific method do not depend on them. The file is included only so the application builds and
  renders as published.
* The name "Firewatch" is used as the public name of this independent project; no trademark right is claimed.
* Pending clarification: the Space Apps Terms & Conditions ask that original content be freely available or OSI-licensed.
  The owner will confirm with the Local Lead that reserving the logo marks (not the code) is acceptable, and will release
  or replace them if it is not.

## 4. Generic Aurora design tokens (MIT)
`web/src/design/aurora/{tokens,themes,base}.css` are generic design tokens (colours, spacing, typography variables,
themes) authored by the project owner and reused from an earlier private project of the same owner (provenance and hashes
in `web/src/design/aurora-source.json`). **The owner confirms they are licensed under the MIT licence** together with the
rest of the code, so forks and adaptations may reuse and modify them. They contain no logo.

## 5. Third-party software
Dependencies keep their own licences (MIT, ISC, BSD-2/3-Clause, OFL-1.1, ...):
see [`web/public/THIRD_PARTY_NOTICES.txt`](web/public/THIRD_PARTY_NOTICES.txt).
The Inter typeface is under the SIL Open Font License 1.1.

## 6. Data (not owned by this project)
* **NASA FIRMS** (MODIS, VIIRS) and **NASA Earthdata CMR** data are NASA
  products under NASA/Earthdata open data policy and carry NASA's own
  acknowledgement and disclaimer (in `THIRD_PARTY_NOTICES.txt`). This
  repository does not claim ownership of them, and does not redistribute raw
  FIRMS files.
* **IBGE - Malha Municipal Digital 2025** (Tocantins boundaries, simplified
  copy in `web/src/geo/`). IBGE's methodological note "Malha Municipal Digital
  e Areas Territoriais 2025 - Informacoes tecnicas e legais para a utilizacao
  dos dados publicados" (Notas metodologicas 01/2026) states that IBGE provides
  the mesh and all derived products "sob licenca compativel com Creative
  Commons BY 4.0" (distribute, remix, adapt, even commercially, provided
  credit is given). Required credit: **Source: IBGE, Malha Municipal Digital
  2025**. The note also requires users who generalise the mesh to make clear
  that it was processed: **the geometry used here is a simplified derivative
  and is not the official IBGE mesh.** IBGE is not responsible for the use of
  the data for purposes other than statistical compilation. These terms were
  read from the PDF of the note (IBGE library, catalogue id 2102268).
* Data derived by this project (`resultados/`) are computed from NASA FIRMS
  records; they are provided as research outputs, with no warranty.

## 7. Contributors
David and Tony (first names only) contributed to review and use-case work as
listed in the README. They are credited as contributors; this repository does
not record any copyright claim by them.
