# Contributing

Firewatch is an experimental, independent project built for the NASA Space Apps Challenge 2026. Contributions,
questions and forks are welcome.

## Before you start
- Read the [README](README.md) (method, limits, how to reproduce) and [`BRAND_AND_RIGHTS.md`](BRAND_AND_RIGHTS.md).
- Code contributions are accepted under the repository's MIT licence.
- **Scientific rules** that must not be broken by a change:
  - never merge MODIS and VIIRS into a combined score and never add their counts;
  - never read "no detection" as "no fire" (coverage state and detection state stay separate);
  - a detection is a thermal-anomaly flag, not a confirmed fire;
  - the evaluated year is always excluded from its historical reference;
  - keep "Experimental / not validated" visible until an independent validation exists.
- Do not add NASA raw data, SQLite files, FIRMS keys, credentials or `.env` files. The FIRMS key lives only in
  `FIRMS_MAP_KEY` (environment variable). `.gitignore` blocks raw data; do not weaken it.
- Use of AI tools is allowed, but disclose it in your pull request (what was AI-assisted or generated).

## Development
```bash
python -m unittest discover -s tests -t .     # engine tests (28 need real data and are skipped without it)
cd web && npm ci --ignore-scripts && npm run lint && npx tsc -b && npm test && npm run build
```
Tests that depend on real data use `NASA_DATA_DIR`, `FIRECAL_BANCO_DIR` and `FIRECAL_GRANULOS` (README, step 2).
Add tests with fictitious or simulated inputs; do not commit real NASA files.

## Pull requests
Keep changes small, explain the scientific reasoning when a rule or threshold changes, update the documentation, and
run the commands above. Changes to the method need a note in `docs/DECISOES.md`.

## Forks and new regions
See [`docs/EXTENDING_TO_NEW_REGIONS.md`](docs/EXTENDING_TO_NEW_REGIONS.md). Replace the Ikarus Aurora logos and branding
in your fork; the rest of the code can be reused under MIT.

## Language
The README and this file are in English. Some technical notes in `docs/` are in Portuguese (see the README).
