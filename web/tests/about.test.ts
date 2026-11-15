import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { describe, it } from 'node:test'
import { DICTS } from '../src/i18n/index.ts'
import { BASE, parseHash, toHash } from '../src/state/model.ts'
import { CONTRIBUTING_URL, GITHUB_URL, MEMBERS, REGIONS_GUIDE_URL, initials } from '../src/about/team.ts'

const pt = DICTS['pt-BR']
const en = DICTS['en-US']

// The ORIGINAL testimonials, word for word, as written by the members. Do not edit, summarise or "correct" them.
const ORIGINAL: Record<string, string[]> = {
  junior: [
    'Participar do NASA Space Apps Challenge representou, para mim, muito mais do que desenvolver uma aplicação.',
    'Foi a oportunidade de desafiar meus próprios limites, entrar em um universo de conhecimento que parecia distante e descobrir que ainda tenho muito a aprender, construir e compartilhar.',
    'Não cheguei com todas as respostas. Encontrei dificuldades, questionei minhas capacidades e precisei aprender a confiar no processo, nas pessoas e nas ferramentas que estavam ao meu alcance.',
    'O Firewatch nasceu dessa experiência. Não como uma demonstração de que sei tudo, mas como uma prova de que não preciso saber tudo para começar.',
    'Quero que outras pessoas possam estudar, questionar, melhorar e levar esse projeto além de onde conseguimos chegar.',
    'Se alguma coisa dessa jornada puder incentivar alguém a tentar aquilo que parecia impossível, então o Firewatch já terá alcançado um propósito muito especial para mim.',
  ],
  tony: [
    'Participar do NASA Space Apps Challenge 2026 me ensinou que, antes de buscar soluções, é preciso ter calma, observar e compreender o problema. A inovação começa quando aprendemos a entender antes de tentar resolver. 🚀',
  ],
  david: [
    'Participar do NASA Space Apps Challenge 2026 foi uma oportunidade de conhecer novas pessoas, trocar experiências e fortalecer o trabalho em equipe. Aprendi que cada pessoa tem algo a ensinar e que, juntos, podemos aprender, crescer e ir ainda mais longe. 🚀',
  ],
}

describe('About page: team', () => {
  it('lists the three members with full names, aliases and Instagram profiles', () => {
    assert.deepEqual(MEMBERS.map((m) => m.name), ['Otalicio Américo de Melo Junior', 'Anthonionny Silva dos Santos', 'David Vieira de Moraes'])
    assert.deepEqual(MEMBERS.map((m) => m.alias), ['Júnior Américo', 'Tony', undefined])
    assert.deepEqual(MEMBERS.map((m) => m.instagramHandle), ['@junior_americo74', '@thonny.sto', '@davidv_moraes'])
    assert.deepEqual(MEMBERS.map((m) => m.instagramUrl), [
      'https://www.instagram.com/junior_americo74/',
      'https://www.instagram.com/thonny.sto/',
      'https://www.instagram.com/davidv_moraes/',
    ])
    for (const m of MEMBERS) assert.equal(m.instagramUrl, `https://www.instagram.com/${m.instagramHandle.slice(1)}/`)
  })
  it('keeps the Portuguese testimonials exactly as written (nothing summarised, reworded or added)', () => {
    for (const m of MEMBERS) assert.deepEqual(m.quote['pt-BR'], ORIGINAL[m.id], m.id)
  })
  it('has a complete English translation of every paragraph, never the Portuguese text', () => {
    for (const m of MEMBERS) {
      assert.equal(m.quote['en-US'].length, m.quote['pt-BR'].length, m.id)
      m.quote['en-US'].forEach((p, i) => {
        assert.ok(p.length > 20, `${m.id}:${i}`)
        assert.notEqual(p, m.quote['pt-BR'][i], `${m.id}:${i}`)
      })
    }
    assert.ok(MEMBERS[1].quote['en-US'][0].endsWith('🚀') && MEMBERS[2].quote['en-US'][0].endsWith('🚀'))
  })
  it('avatars are initials, no photographs', () => {
    assert.deepEqual(MEMBERS.map((m) => initials(m.name)), ['OJ', 'AS', 'DM'])
    assert.equal(initials('Maria'), 'M')
  })
})

describe('About page: links', () => {
  it('points to the public repository and to guides that exist there', () => {
    assert.equal(GITHUB_URL, 'https://github.com/OtalicioAmerico/firewatch-nasa-space-apps-2026')
    assert.equal(CONTRIBUTING_URL, `${GITHUB_URL}/blob/main/CONTRIBUTING.md`)
    assert.equal(REGIONS_GUIDE_URL, `${GITHUB_URL}/blob/main/docs/EXTENDING_TO_NEW_REGIONS.md`)
  })
  it('opens every external link in a new tab without leaking the opener', () => {
    const src = readFileSync('src/pages/AboutPage.tsx', 'utf8')
    assert.match(src, /target="_blank"/)
    assert.match(src, /rel="noopener noreferrer"/)
    assert.equal((src.match(/<a /g) ?? []).length, 1, 'all anchors go through ExtLink')
  })
})

describe('About page: navigation and texts', () => {
  it('is a routable page named Sobre / About, placed after the methodology', () => {
    assert.equal(parseHash('#/about?lang=en-US', BASE).page, 'about')
    assert.equal(parseHash(toHash({ ...BASE, page: 'about' }), BASE).page, 'about')
    assert.equal(pt['nav.about'], 'Sobre')
    assert.equal(en['nav.about'], 'About')
    const shell = readFileSync('src/components/Shell.tsx', 'utf8')
    assert.ok(shell.indexOf("id: 'methodology'") < shell.indexOf("id: 'about'"))
    assert.match(readFileSync('src/App.tsx', 'utf8'), /state\.page === 'about'/)
  })
  it('has all the required sections and the central messages in both languages', () => {
    const fam = ['hero.eyebrow', 'hero.title', 'hero.highlight', 'hero.p1', 'hero.p2', 'hero.p3', 'hero.notice', 'story.title', 'story.p1', 'story.p2', 'story.p3', 'story.note', 'team.title', 'team.intro', 'team.instagram', 'team.newTab', 'team.original', 'join.title', 'join.lead', 'join.i1', 'join.i2', 'join.i3', 'join.i4', 'join.i5', 'join.i6', 'join.i7', 'join.pilot', 'join.quote', 'join.github', 'join.contributing', 'join.regions', 'join.methodology', 'join.note', 'close.quote', 'close.brand', 'close.last', 'close.note']
    for (const k of fam) assert.ok(`about.${k}` in pt && `about.${k}` in en, k)
    assert.equal(pt['about.hero.title'], 'Sobre o Firewatch')
    assert.equal(pt['about.hero.highlight'], 'Um novo olhar sobre a Terra.')
    assert.equal(pt['about.join.title'], 'Este projeto não precisa terminar aqui.')
    assert.equal(pt['about.join.quote'], 'O conhecimento cresce quando é compartilhado.')
    assert.equal(pt['about.join.github'], 'Explorar o projeto no GitHub')
    assert.equal(en['about.join.github'], 'Explore on GitHub')
    assert.equal(pt['about.close.quote'], 'O Firewatch começou com três pessoas e um desafio. Seu próximo capítulo pode ser escrito por você.')
    assert.equal(pt['about.close.brand'], 'Firewatch — Um novo olhar sobre a Terra.')
    assert.equal(pt['about.close.last'], 'O hackathon foi o começo, não o limite do Firewatch.')
    assert.equal(pt['about.close.note'], 'Projeto independente desenvolvido para o NASA Space Apps Challenge 2026. Não é um produto oficial da NASA. Suas análises são experimentais e não identificam, por si só, incêndios confirmados.')
    assert.equal(en['about.close.last'], 'The hackathon was the beginning, not the limit of Firewatch.')
  })
  it('never claims NASA endorsement, an award or confirmed fires', () => {
    for (const [lang, d] of [['pt', pt], ['en', en]] as const) {
      const text = Object.entries(d).filter(([k]) => k.startsWith('about.')).map(([, v]) => v).join(' ')
      assert.ok(!/(endossad|aprovad[oa] pela NASA|premiad|vencedor|certificad[oa] pela NASA|winner|award-winning|endorsed by|certified by)/i.test(text), lang)
    }
    assert.match(pt['about.story.note'], /não significa endosso, certificação, premiação nem validação científica oficial da NASA/)
    assert.match(en['about.story.note'], /does not mean endorsement, certification, an award or official scientific validation by NASA/)
    assert.match(pt['about.hero.notice'], /não\*\* é um detector de incêndios confirmados/)
  })
  it('never sends handles or URLs through the rich-text renderer (underscores would become italics)', () => {
    const src = readFileSync('src/pages/AboutPage.tsx', 'utf8')
    assert.ok(!/<T k=\{?[`'"]about\.team/.test(src))
  })
})
