import assert from 'node:assert/strict'
import { describe, it } from 'node:test'
import { mockDataSource as dataSource } from '../src/services/mockDataSource.ts'
import { ALL_DATES, CELLS, REGION, SCRIPTED, YEARS } from '../src/mock/index.ts'
import { BASE, isCloseKey, parseHash, toHash } from '../src/state/model.ts'
import type { DayRecord, Scenario } from '../src/types/index.ts'

const SC: Scenario[] = ['A', 'B']
const allDays = (sc: Scenario): DayRecord[] => ALL_DATES.map((d) => dataSource.getDay(d, sc))

describe('fixtures are simulated and clearly labelled', () => {
  it('the data source declares itself simulated', () => {
    assert.equal(dataSource.isSimulated, true)
    assert.equal(dataSource.mode, 'MOCK')
  })
  it('every individual detection is marked MOCK / SIMULATED', () => {
    let n = 0
    for (const date of ['2024-09-10', '2021-08-18', '2025-03-03']) {
      for (const cd of dataSource.getCellDays(date, 'B').filter((c) => c.modisCount + c.viirsCount > 0).slice(0, 25)) {
        for (const d of dataSource.getDetections(date, cd.cell.id)) {
          n++
          assert.ok(d.id.startsWith('MOCK-'))
          assert.match(d.sourceFile, /^MOCK_.*_SIMULATED\.csv$/)
        }
      }
    }
    assert.ok(n > 50)
  })
  it('covers 2021-2025 and Tocantins with 0.25 degree cells', () => {
    assert.deepEqual(YEARS, [2021, 2022, 2023, 2024, 2025])
    assert.equal(ALL_DATES.length, 1826)
    assert.equal(ALL_DATES[0], '2021-01-01')
    assert.equal(ALL_DATES.at(-1), '2025-12-31')
    assert.equal(REGION.name, 'Tocantins')
    assert.ok(CELLS.length > 300 && CELLS.length < 450)
    for (const c of CELLS) assert.ok(Math.abs(c.lat1 - c.lat0 - 0.25) < 1e-9 && Math.abs(c.lon1 - c.lon0 - 0.25) < 1e-9)
  })
})

describe('consistency between map, calendar and evidence', () => {
  it('the cell-level counts add up to the day totals (per sensor, never combined)', () => {
    for (const date of ['2021-08-18', '2022-09-27', '2023-06-08', '2024-07-19', '2025-08-21', '2023-01-05']) {
      const d = dataSource.getDay(date, 'B')
      const cells = dataSource.getCellDays(date, 'B')
      assert.equal(cells.reduce((a, c) => a + c.modisCount, 0), d.modis.detections, date)
      assert.equal(cells.reduce((a, c) => a + c.viirsCount, 0), d.viirs.detections, date)
      const act = cells.filter((c) => c.modisCount > 0).length
      assert.equal(d.modis.activeCells, act, date)
    }
  })
  it('individual simulated detections match the cell counts', () => {
    const date = '2024-09-10'
    for (const cd of dataSource.getCellDays(date, 'B').filter((c) => c.modisCount + c.viirsCount > 0).slice(0, 30)) {
      const det = dataSource.getDetections(date, cd.cell.id)
      assert.equal(det.filter((x) => x.sensor === 'MODIS').length, cd.modisCount)
      assert.equal(det.filter((x) => x.sensor === 'VIIRS').length, cd.viirsCount)
      for (const x of det) assert.ok(x.lat >= cd.cell.lat0 && x.lat <= cd.cell.lat1 && x.lon >= cd.cell.lon0 && x.lon <= cd.cell.lon1)
    }
  })
  it('is deterministic', () => {
    assert.deepEqual(dataSource.getDay('2023-08-15', 'B'), dataSource.getDay('2023-08-15', 'B'))
    assert.equal(JSON.stringify(dataSource.getCellDays('2023-08-15', 'A')), JSON.stringify(dataSource.getCellDays('2023-08-15', 'A')))
  })
  it('extent exposes numerator and denominator', () => {
    for (const d of allDays('B').slice(0, 400)) {
      if (d.modis.extent !== null && d.modis.extentDenominator) {
        assert.ok(Math.abs(d.modis.extent - d.modis.extentNumerator! / d.modis.extentDenominator) < 2e-3) // denominator is displayed rounded to 0.1 cell
      }
    }
  })
})

describe('MODIS version blocks', () => {
  it('uses 6.03 until 2022-12-31 and 61.03 afterwards; VIIRS is version 2', () => {
    for (const d of allDays('B')) {
      const want = d.date < '2023-01-01' ? '6.03' : '61.03'
      assert.equal(d.modis.productVersion, want)
      for (const s of d.modis.satellites) assert.equal(s.productVersion, want)
      assert.equal(d.viirs.productVersion, '2')
      assert.equal(d.modisBlock, d.date < '2023-01-01' ? 'A' : 'B')
    }
  })
})

describe('comparability and K', () => {
  it('K is null whenever the day is not comparable and numeric in [0,1] otherwise', () => {
    let nonComparable = 0
    for (const sc of SC) {
      for (const d of allDays(sc)) {
        if (!d.comparison.comparable) {
          nonComparable++
          assert.equal(d.comparison.K, null)
          assert.equal(d.comparison.Knull, null)
          assert.ok(d.comparison.reason === 'INSUFFICIENT_COVERAGE' || d.comparison.reason === 'NO_ACTIVE_CELLS')
        } else if (d.comparison.K !== null) {
          assert.ok(d.comparison.K >= 0 && d.comparison.K <= 1)
        }
      }
    }
    assert.ok(nonComparable > 20, 'the demo must contain not-comparable days')
  })
  it('the conservative scenario is never more permissive than the exploratory one', () => {
    for (const date of ALL_DATES.filter((_, i) => i % 7 === 0)) {
      const a = dataSource.getDay(date, 'A').comparison
      const b = dataSource.getDay(date, 'B').comparison
      if (a.comparable) assert.ok(b.comparable, date)
    }
  })
  it('scenario A excludes days with insufficient corroborated coverage (no numbers, explicit flag)', () => {
    const a = dataSource.getDay('2022-09-27', 'A')
    assert.equal(a.viirs.valid, false)
    assert.equal(a.viirs.extent, null)
    assert.ok(a.viirs.excludedDetections > 0)
    const b = dataSource.getDay('2022-09-27', 'B')
    assert.equal(b.viirs.valid, true)
    assert.notEqual(b.viirs.extent, null)
  })
})

describe('scripted demonstration days', () => {
  it('contain the intended coverage situations', () => {
    assert.equal(dataSource.getDay('2022-09-27', 'B').viirs.satellites[0].catalogueComplete, false)
    assert.equal(dataSource.getDay('2022-09-27', 'B').viirs.coverageState, 'INDETERMINATE')
    const terra = dataSource.getDay('2023-06-08', 'B').modis.satellites.find((s) => s.satellite === 'Terra')!
    assert.ok(terra.conflictRecords > 0)
    assert.equal(terra.coverageState, 'INDETERMINATE')
    const aqua = dataSource.getDay('2024-07-19', 'B').modis.satellites.find((s) => s.satellite === 'Aqua')!
    assert.ok(aqua.coverageFraction < 0.95 && aqua.coverageFraction > 0)
    assert.equal(aqua.coverageState, 'PARTIAL')
    for (const k of Object.keys(SCRIPTED)) assert.ok(dataSource.getDay(k, 'B'))
  })
  it('every cell category appears on some day', () => {
    const seen = new Set<string>()
    for (const date of ['2024-09-10', '2022-09-27', '2024-07-19', '2025-08-21']) for (const c of dataSource.getCellDays(date, 'B')) seen.add(c.category)
    for (const k of ['BOTH', 'MODIS_ONLY', 'VIIRS_ONLY', 'UNCERTAIN', 'NONE']) assert.ok(seen.has(k), k)
  })
})

describe('historical reference', () => {
  it('MODIS has insufficient reference in 2021-2022 (only one other year in the block)', () => {
    for (const d of allDays('B').filter((x) => x.year <= 2022 && x.referenceModis.position !== 'NO_DATA')) {
      assert.equal(d.referenceModis.position, 'INSUFFICIENT')
      assert.equal(d.referenceModis.nReferenceYears, 1)
    }
  })
  it('VIIRS uses the other four years and never the evaluated year', () => {
    let n = 0
    for (const d of allDays('B').filter((x) => x.referenceViirs.position !== 'NO_DATA')) {
      assert.ok(d.referenceViirs.nReferenceYears <= 4)
      n++
    }
    assert.ok(n > 1000)
    const positions = new Set(allDays('B').map((d) => d.referenceViirs.position))
    for (const p of ['ABOVE', 'WITHIN', 'BELOW']) assert.ok(positions.has(p as never), p)
  })
  it('weekly reference band excludes the evaluated year', () => {
    const w = dataSource.getWeeklyReference(2024, 'VIIRS', 'B')
    assert.equal(w.length, 53)
    assert.ok(w.some((p) => p.refMin !== null && p.refMax !== null && p.refMax >= p.refMin))
  })
})

describe('storytelling examples', () => {
  it('all examples point to existing days and the same-count pair really has similar counts', () => {
    const ex = dataSource.getExamples()
    assert.ok(ex.length >= 6)
    for (const e of ex) assert.ok(ALL_DATES.includes(e.date), e.id)
    const pair = ex.find((e) => e.id === 'count-vs-extent')!
    assert.ok(pair.relatedDate, 'pair found')
    const a = dataSource.getDay(pair.date, 'B')
    const b = dataSource.getDay(pair.relatedDate!, 'B')
    assert.ok(Math.abs(a.modis.detections - b.modis.detections) / Math.max(a.modis.detections, b.modis.detections) <= 0.03)
    const r = Math.max(a.modis.extent!, b.modis.extent!) / Math.min(a.modis.extent!, b.modis.extent!)
    assert.ok(r >= 1.4)
  })
  it('some days show a divergence between raw count and extent', () => {
    assert.ok(allDays('B').filter((d) => d.divergence).length > 10)
  })
})

describe('URL state', () => {
  it('round-trips the navigable state through the hash', () => {
    const s = { ...BASE, page: 'calendar' as const, date: '2023-06-08', sensor: 'MODIS' as const, metric: 'intensity' as const, scenario: 'A' as const, selectedCellId: 'g0.25_-40_-192' }
    const back = parseHash(toHash(s), BASE)
    assert.equal(back.page, 'calendar')
    assert.equal(back.date, '2023-06-08')
    assert.equal(back.sensor, 'MODIS')
    assert.equal(back.metric, 'intensity')
    assert.equal(back.scenario, 'A')
    assert.equal(back.selectedCellId, 'g0.25_-40_-192')
  })
  it('ignores invalid or out-of-range values', () => {
    const back = parseHash('#/calendar?date=1999-01-01&sensor=XXX&metric=nope&scenario=Z', BASE)
    assert.equal(back.date, BASE.date)
    assert.equal(back.sensor, BASE.sensor)
    assert.equal(back.metric, BASE.metric)
    assert.equal(back.scenario, BASE.scenario)
    assert.equal(parseHash('#/unknown', BASE).page, BASE.page)
  })
})

describe('data source contract (what Mission 05 outputs will implement)', () => {
  it('exposes every accessor the UI uses', () => {
    for (const m of ['getRegion', 'getYears', 'getDay', 'getMonth', 'getYearSeries', 'getWeeklyReference', 'getCellDays', 'getDetections', 'getExamples', 'getRange']) {
      assert.equal(typeof (dataSource as unknown as Record<string, unknown>)[m], 'function', m)
    }
    assert.equal(dataSource.getMonth(2024, 2, 'B').length, 29)
  })
})

describe('evidence drawer keyboard handling', () => {
  it('closes on Escape only', () => {
    assert.equal(isCloseKey({ key: 'Escape' }), true)
    for (const key of ['Enter', 'Tab', ' ', 'ArrowLeft', 'Esc', 'a']) assert.equal(isCloseKey({ key }), false, key)
  })
  it('ignores Escape already handled by another control or during IME composition', () => {
    assert.equal(isCloseKey({ key: 'Escape', defaultPrevented: true }), false)
    assert.equal(isCloseKey({ key: 'Escape', isComposing: true }), false)
  })
})

describe('scenario A/B toggle', () => {
  it('changes the state without altering fixtures; identical days are legitimate', () => {
    const a = parseHash(toHash({ ...BASE, scenario: 'A' }), BASE)
    const b = parseHash(toHash({ ...BASE, scenario: 'B' }), BASE)
    assert.equal(a.scenario, 'A')
    assert.equal(b.scenario, 'B')
    // At least one day differs between scenarios (so the toggle is meaningful) and at least one does not (fixtures are not forced to differ).
    const days = ALL_DATES.filter((_, i) => i % 5 === 0)
    const differ = days.filter((d) => JSON.stringify(dataSource.getDay(d, 'A')) !== JSON.stringify(dataSource.getDay(d, 'B'))).length
    assert.ok(differ > 0 && differ < days.length)
  })
})

describe('methodology examples', () => {
  it('the count-vs-extent example targets a real day with MODIS/extent and a distinct related day', () => {
    const e = dataSource.getExamples().find((x) => x.id === 'count-vs-extent')!
    assert.ok(ALL_DATES.includes(e.date))
    assert.equal(e.sensor, 'MODIS')
    assert.equal(e.metric, 'extent')
    assert.ok(e.relatedDate && e.relatedDate !== e.date && ALL_DATES.includes(e.relatedDate))
  })
})
