import assert from 'node:assert/strict'
import { describe, it } from 'node:test'
import { MUNICIPALITIES } from '../src/geo/region.ts'

describe('municipality names (IBGE Malha Municipal 2025)', () => {
  const props = MUNICIPALITIES.features.map((f) => f.properties as { cd: string; nm: string })
  it('has the 139 municipalities of Tocantins, each with an IBGE code and a name', () => {
    assert.equal(props.length, 139)
    assert.equal(new Set(props.map((p) => p.cd)).size, 139)
    assert.ok(props.every((p) => /^17\d{5}$/.test(p.cd) && p.nm.length > 1))
  })
  it('names are correctly accented, not mojibake', () => {
    assert.ok(props.every((p) => !/[ÂÃ­�]/.test(p.nm)), 'broken characters in a municipality name')
    const by = new Map(props.map((p) => [p.cd, p.nm]))
    assert.equal(by.get('1721208'), 'Tocantinópolis')
    assert.equal(by.get('1702109'), 'Araguaína')
    assert.equal(by.get('1709302'), 'Guaraí')
    assert.equal(by.get('1716109'), 'Paraíso do Tocantins')
    assert.equal(by.get('1721109'), 'Tocantínia')
    assert.equal(by.get('1721000'), 'Palmas')
  })
})
