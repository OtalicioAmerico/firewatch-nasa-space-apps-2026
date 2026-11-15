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

## 3. Logos and visual identity (rights reserved)
* The Ikarus Aurora wing mark (`web/src/assets/brand/ikarus-wing-white.svg`),
  the name "Ikarus Aurora" as a logo/brand, and the Ikarus Aurora visual
  identity are **not** licensed under the MIT licence.
* They are included only so the application builds and renders as published.
  Publishing the code under MIT **does not** grant any right to use these
  marks, and does not transfer their ownership.
* If you fork or reuse this code, replace the logo files and the "Ikarus
  Aurora" branding (see `web/src/components/Brand.tsx` and
  `web/src/i18n/*.json`, keys `brand.*`) with your own.
* The name "Firewatch" is used here as the public name of this independent
  project; no trademark right is claimed.

## 4. Original Aurora design tokens
`web/src/design/aurora/{tokens,themes,base}.css` are original Aurora design
system files authored by the project owner and reused from an earlier private
project of the same owner (provenance and hashes in
`web/src/design/aurora-source.json`). The owner authorises their use and redistribution as part of this repository.
Unless a file header says otherwise they are distributed with the rest of the
code under the MIT licence (this choice is recorded as pending the owner's
final confirmation in `docs/LICENCAS_E_ATRIBUICOES.md`). This never extends to
the logos in section 3.

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
