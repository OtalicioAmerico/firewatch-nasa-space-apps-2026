/**
 * SIMULATED universe of cells for the mockup: 0.25 degree cells whose centre lies inside the REAL IBGE outline.
 * (The REAL source uses the 433-cell universe of Mission 05 instead; see services/realDataSource.ts.)
 */
import type { Cell } from '../types'
import { CELL_SIZE, OUTLINE_RING, REGION, makeCell } from '../geo/region'
import { pointInRing, ringBounds } from '../lib/geo'

export { CELL_SIZE, REGION }

function build(): Cell[] {
  const [w, s, e, n] = ringBounds(OUTLINE_RING)
  const out: Cell[] = []
  for (let i = Math.floor(s / CELL_SIZE); i <= Math.floor(n / CELL_SIZE); i++) {
    for (let j = Math.floor(w / CELL_SIZE); j <= Math.floor(e / CELL_SIZE); j++) {
      if (pointInRing(j * CELL_SIZE + CELL_SIZE / 2, i * CELL_SIZE + CELL_SIZE / 2, OUTLINE_RING)) out.push(makeCell(i, j))
    }
  }
  return out
}

export const CELLS: Cell[] = build()
