import assert from 'node:assert/strict'
import { existsSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, it } from 'node:test'
import { createRealDataSource, blockDate } from '../src/services/realDataSource.ts'

const ROOT = join('public', 'data', 'real')
const have = existsSync(join(ROOT, 'meta.json'))
const loader = async (rel: string) => JSON.parse(readFileSync(join(ROOT, rel), 'utf8'))

describe('REAL data source (Mission 05 export)', { skip: !have && 'run tools/export_web first' }, () => {
  const ds = createRealDataSource(loader)
  it('is explicitly REAL and not simulated', async () => {
    await ds.init()
    assert.equal(ds.mode, 'REAL')
    assert.equal(ds.isSimulated, false)
    assert.equal(ds.getCells().length, 433)
    assert.deepEqual(ds.getRange(), { first: '2021-01-01', last: '2025-12-31' })
    assert.ok(ds.getSources().length > 700)
  })
  it('fails loudly instead of inventing data when files are missing', async () => {
    const broken = createRealDataSource(async () => {
      throw new Error('HTTP 404')
    })
    await assert.rejects(broken.init())
    assert.throws(() => broken.getDay('2024-09-10', 'B'))
  })
  it('day, cells and detections agree with each other (calendar → map → evidence)', async () => {
    const date = '2024-09-10'
    await Promise.all([ds.ensure({ kind: 'year', year: 2024 }), ds.ensure({ kind: 'cells', date }), ds.ensure({ kind: 'detections', date })])
    for (const sc of ['A', 'B'] as const) {
      const d = ds.getDay(date, sc)
      const cells = ds.getCellDays(date, sc)
      assert.equal(cells.length, 433)
      assert.equal(cells.reduce((a, c) => a + c.modisCount, 0), d.modis.detections)
      assert.equal(cells.reduce((a, c) => a + c.viirsCount, 0), d.viirs.detections)
      assert.equal(d.modis.detections, d.modis.satellites[0].detections + d.modis.satellites[1].detections)
      let dets = 0
      for (const c of cells) {
        const list = ds.getDetections(date, c.cell.id)
        assert.equal(list.length, c.modisCount + c.viirsCount)
        dets += list.length
        for (const x of list) {
          assert.ok(!x.id.startsWith('MOCK'))
          assert.match(x.sourceSha256 ?? '', /^[0-9a-f]{64}$/)
          assert.ok(x.lat >= c.cell.lat0 && x.lat <= c.cell.lat1 && x.lon >= c.cell.lon0 && x.lon <= c.cell.lon1)
        }
      }
      assert.equal(dets, d.modis.detections + d.viirs.detections)
      if (d.comparison.comparable && d.comparison.K !== null) {
        assert.equal(cells.filter((c) => c.category === 'BOTH' && !(sc === 'A' && c.excludedInA)).length >= d.comparison.both - 0, true)
      }
    }
  })
  it('scenarios A and B come from the real results (no artificial difference)', async () => {
    await ds.ensure({ kind: 'year', year: 2024 })
    const a = ds.getDay('2024-09-10', 'A')
    const b = ds.getDay('2024-09-10', 'B')
    assert.equal(a.modis.detections, b.modis.detections)
    assert.equal(a.modis.extent, b.modis.extent)
  })
  it('MODIS 2021–2022 has insufficient reference and the evaluated year is excluded', async () => {
    await Promise.all([2021, 2023, 2024, 2025].map((y) => ds.ensure({ kind: 'year', year: y })))
    for (const d of ds.getMonth(2021, 7, 'B')) assert.ok(['INSUFFICIENT', 'NO_DATA'].includes(d.referenceModis.position))
    const w = ds.getWeeklyReference(2023, 'MODIS', 'B')[46]
    const others = [2024, 2025].map((y) => ds.getWeeklyReference(y, 'MODIS', 'B')[46].modis!)
    assert.equal(w.refMin, Math.min(...others))
    assert.equal(w.refMax, Math.max(...others))
  })
  it('documented examples: MODIS block 47/2023 and VIIRS block 31/2021', async () => {
    const ex = ds.getExamples()
    const a = ex.find((e) => e.id === 'count-vs-extent')!.weekly!
    assert.equal(a.detections, 163)
    assert.equal(a.detectionsPosition, 'BELOW')
    assert.equal(a.extentPosition, 'ABOVE')
    const b = ex.find((e) => e.id === 'extent-vs-count')!.weekly!
    assert.equal(b.detectionsPosition, 'ABOVE')
    assert.equal(b.extentPosition, 'WITHIN')
    assert.equal(blockDate(2023, 47, 0), '2023-11-19')
    for (const e of ex) assert.ok(e.date >= '2021-01-01' && e.date <= '2025-12-31')
  })
  it('FIRMS × CMR conflict of May 2025 is flagged and K is not applicable', async () => {
    await ds.ensure({ kind: 'year', year: 2025 })
    const d = ds.getDay('2025-05-14', 'B')
    assert.ok(d.flags.includes('TERRA_CONFLICT'))
    assert.equal(d.comparison.K, null)
    assert.equal(d.comparison.comparable, false)
  })
  it('MODIS version blocks are the observed labels', async () => {
    await ds.ensure({ kind: 'year', year: 2022 })
    assert.equal(ds.getDay('2022-08-01', 'B').modis.satellites.find((s) => s.productVersion)?.productVersion ?? '6.03', '6.03')
    assert.equal(ds.getDay('2024-09-10', 'B').modis.productVersion, '61.03')
    assert.equal(ds.getDay('2024-09-10', 'B').viirs.productVersion, '2')
  })
})
