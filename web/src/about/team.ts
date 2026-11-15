/**
 * Team members and their testimonials for the About page.
 *
 * The Portuguese testimonials are the ORIGINAL texts written by each member: they are stored here verbatim (paragraph by
 * paragraph, emoji included) and must never be summarised, reworded or corrected. The English versions are faithful
 * translations prepared for this page. `tests/about.test.ts` pins the Portuguese text word for word.
 * They live outside the i18n dictionaries on purpose: the dictionaries are checked for "same key, translated text", and a
 * personal text must not be treated as interface copy.
 */
import type { Lang } from '../i18n'

export interface Member {
  id: 'junior' | 'tony' | 'david'
  /** Full name as listed on the NASA Space Apps team page. */
  name: string
  /** How the member is called (shown beside the full name when given by the member). */
  alias?: string
  instagramHandle: string
  instagramUrl: string
  /** Paragraphs of the testimonial, by language. `pt-BR` is the original. */
  quote: Record<Lang, string[]>
}

export const GITHUB_URL = 'https://github.com/OtalicioAmerico/firewatch-nasa-space-apps-2026'
export const CONTRIBUTING_URL = `${GITHUB_URL}/blob/main/CONTRIBUTING.md`
export const REGIONS_GUIDE_URL = `${GITHUB_URL}/blob/main/docs/EXTENDING_TO_NEW_REGIONS.md`

export const MEMBERS: Member[] = [
  {
    id: 'junior',
    name: 'Otalicio Américo de Melo Junior',
    alias: 'Júnior Américo',
    instagramHandle: '@junior_americo74',
    instagramUrl: 'https://www.instagram.com/junior_americo74/',
    quote: {
      'pt-BR': [
        'Participar do NASA Space Apps Challenge representou, para mim, muito mais do que desenvolver uma aplicação.',
        'Foi a oportunidade de desafiar meus próprios limites, entrar em um universo de conhecimento que parecia distante e descobrir que ainda tenho muito a aprender, construir e compartilhar.',
        'Não cheguei com todas as respostas. Encontrei dificuldades, questionei minhas capacidades e precisei aprender a confiar no processo, nas pessoas e nas ferramentas que estavam ao meu alcance.',
        'O Firewatch nasceu dessa experiência. Não como uma demonstração de que sei tudo, mas como uma prova de que não preciso saber tudo para começar.',
        'Quero que outras pessoas possam estudar, questionar, melhorar e levar esse projeto além de onde conseguimos chegar.',
        'Se alguma coisa dessa jornada puder incentivar alguém a tentar aquilo que parecia impossível, então o Firewatch já terá alcançado um propósito muito especial para mim.',
      ],
      'en-US': [
        'Taking part in the NASA Space Apps Challenge meant much more to me than building an application.',
        'It was a chance to challenge my own limits, step into a universe of knowledge that once seemed distant, and discover that I still have a lot to learn, build and share.',
        'I did not arrive with all the answers. I ran into difficulties, questioned my own abilities, and had to learn to trust the process, the people, and the tools within my reach.',
        'Firewatch was born from that experience. Not as a demonstration that I know everything, but as proof that I do not need to know everything to begin.',
        'I want other people to be able to study, question, improve and take this project further than we managed to take it.',
        'If any part of this journey can encourage someone to try what once seemed impossible, then Firewatch will already have achieved a very special purpose for me.',
      ],
    },
  },
  {
    id: 'tony',
    name: 'Anthonionny Silva dos Santos',
    alias: 'Tony',
    instagramHandle: '@thonny.sto',
    instagramUrl: 'https://www.instagram.com/thonny.sto/',
    quote: {
      'pt-BR': [
        'Participar do NASA Space Apps Challenge 2026 me ensinou que, antes de buscar soluções, é preciso ter calma, observar e compreender o problema. A inovação começa quando aprendemos a entender antes de tentar resolver. 🚀',
      ],
      'en-US': [
        'Taking part in the NASA Space Apps Challenge 2026 taught me that, before looking for solutions, you need to stay calm, observe and understand the problem. Innovation begins when we learn to understand before trying to solve. 🚀',
      ],
    },
  },
  {
    id: 'david',
    name: 'David Vieira de Moraes',
    instagramHandle: '@davidv_moraes',
    instagramUrl: 'https://www.instagram.com/davidv_moraes/',
    quote: {
      'pt-BR': [
        'Participar do NASA Space Apps Challenge 2026 foi uma oportunidade de conhecer novas pessoas, trocar experiências e fortalecer o trabalho em equipe. Aprendi que cada pessoa tem algo a ensinar e que, juntos, podemos aprender, crescer e ir ainda mais longe. 🚀',
      ],
      'en-US': [
        'Taking part in the NASA Space Apps Challenge 2026 was a chance to meet new people, share experiences and strengthen teamwork. I learned that everyone has something to teach and that, together, we can learn, grow and go even further. 🚀',
      ],
    },
  },
]

/** Initials for the avatar: first letter of the first and of the last word of the full name (no photographs are used). */
export function initials(name: string): string {
  const w = name.trim().split(/\s+/)
  return (w[0][0] + (w.length > 1 ? w[w.length - 1][0] : '')).toUpperCase()
}
