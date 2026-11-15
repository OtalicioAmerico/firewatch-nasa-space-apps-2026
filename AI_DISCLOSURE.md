# Use of AI ("Super Intelligence", SI) - disclosure

This file supports the NASA Space Apps Challenge 2026 requirement to describe how SI tools were used and to acknowledge
SI-generated code, data and text. It separates human contributions from AI-assisted ones.

## Tools actually used
| Tool | Used for |
|---|---|
| **Claude Code** (Anthropic; model Claude Sonnet 5.5), from the terminal, under human direction and review | AI-assisted software implementation and testing: the scientific engine (`firecal/`), data tools (`tools/`), tests (`tests/`, `web/tests/`), the web application (`web/src`, including the interface, i18n and the identity changes requested by the owner), documentation drafts, analysis scripts and the deployment procedure |
| **ChatGPT** (OpenAI) | Structuring the development instructions given to Claude Code; research and planning support; review of scientific interpretations and analytical results; drafting or revising project documentation and presentation materials |

Other AI tools: none are recorded. If a team member used another tool, it must be added here.

**What we do not claim:** that ChatGPT directly authored source code (there is no evidence of that); that any part was
hand-programmed when it was generated with Claude Code; or that any result was validated by AI.

## What is human
- The choice of the challenge and of the approach (compare MODIS and VIIRS without merging them, treat missing
  detections as unknown coverage, exclude the evaluated year from its reference). The human team, not an SI tool, chose the
  idea.
- Scientific decisions and constraints imposed on the tools, direction of the development, priorities, interface and
  presentation decisions, acceptance or rejection of results, and the preparation of the demonstration.
- Review of the evidence and of the fit to the use case by the team members named in the README (roles only; no
  independent scientific validation has taken place).

## AI-generated or AI-assisted material in this repository
| Material | Status |
|---|---|
| Source code (Python, TypeScript/React) and tests | AI-assisted (Claude Code); reviewed and run by the team |
| Documentation (`README.md`, `docs/`, this file) | AI-assisted (Claude Code and ChatGPT); drafted by the tools, directed and checked by the owner |
| Images, video, audio | **None AI-generated.** The Ikarus Aurora wing mark is the owner's own artwork |
| Data | **None AI-generated.** NASA FIRMS / CMR and IBGE data are used as published |
| Presentation / demo material | Not part of this repository |

## Timeline and prior work (not hidden)
Based on commit times (UTC-3) and documents; see `docs/PROVENIENCIA.md` for the table.
- **2026-11-09 to 2026-11-12:** earlier private project of the same owner (also named Firewatch): data foundation,
  single-sensor calendar and geographic web MVP (published 2026-11-12), first FIRMS samples and a written MODIS-VIIRS
  harmonization research specification. AI-assisted (Claude Code).
- **2026-11-13 (local event opening, per the owner):** exploratory FIRMS acquisition and an exploratory MODIS x VIIRS study
  in that project, with AI-assisted reports. Used here as input and reference only.
- **2026-11-14 09:58 onward:** development of this repository (first commit 09:58).
- **Pre-existing owner components reused:** generic Aurora design tokens (MIT) and one logo mark (rights reserved).
- The owner understands research and preparation before the official start as permitted and the competing solution as
  built after it; this will be confirmed with the Local Lead. No dates were adjusted.

## Limits
No scientific validation by humans or AI exists beyond what the README and `docs/` state. No external expert review has
taken place.
