import { existsSync } from 'node:fs'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { dirname, join } from 'node:path'

export async function resolve(specifier, context, next) {
  if ((specifier.startsWith('./') || specifier.startsWith('../')) && !/\.[a-z]+$/.test(specifier) && context.parentURL) {
    const base = dirname(fileURLToPath(context.parentURL))
    for (const cand of [specifier + '.ts', specifier + '.tsx', join(specifier, 'index.ts')]) {
      const p = join(base, cand)
      if (existsSync(p)) return next(pathToFileURL(p).href, context)
    }
  }
  return next(specifier, context)
}
