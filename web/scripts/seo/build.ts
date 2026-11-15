/**
 * Post-build step (runs after `vite build`): writes the public, crawlable pages and the indexing files into `dist/`.
 *   node --import ./tests/register.mjs scripts/seo/build.ts
 * It only ADDS files and rewrites the metadata of `dist/index.html`; the application bundle and `dist/data/**` are untouched.
 */
import { readFileSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { PAGES, jsonLd, metaTags, pageFor, robotsTxt, shellFallback, sitemapXml, staticPage, tr } from './site.ts'

const dist = process.argv[2] ?? 'dist'

function once(html: string, from: string | RegExp, to: string, what: string): string {
  const n = typeof from === 'string' ? html.split(from).length - 1 : (html.match(new RegExp(from.source, from.flags.replace('g', ''))) ?? []).length
  if (n !== 1) throw new Error(`dist/index.html: expected exactly one ${what}, found ${n}`)
  return html.replace(from, () => to)
}

const indexPath = join(dist, 'index.html')
let shell = readFileSync(indexPath, 'utf8')

// the hashed application stylesheet, so the static pages look like the application
const css = shell.match(/<link rel="stylesheet"[^>]*href="(\/assets\/[^"]+\.css)"/)
if (!css) throw new Error('application stylesheet not found in dist/index.html')

// 1. the application shell at "/" (Portuguese): real metadata and a no-JavaScript fallback with the same content as the landing page
const home = pageFor('home', 'pt-BR')
shell = once(shell, /<html lang="[^"]*"/, `<html lang="${home.lang}"`, '<html lang>')
shell = once(shell, /<meta name="description"[^>]*>\s*/, '', 'meta description')
shell = once(shell, /<title>[^<]*<\/title>/, `${metaTags(home)}\n<style>.js .seo-fallback{display:none}</style>\n<script>document.documentElement.classList.add('js')</script>`, '<title>')
shell = once(shell, '<div id="root"></div>', `<div id="root">\n${shellFallback(home)}\n</div>`, '#root')
writeFileSync(indexPath, shell)

// 2. static public pages (everything except "/" which is the shell above)
for (const p of PAGES) {
  if (p.path === '/') continue
  writeFileSync(join(dist, p.path), staticPage(p, css[1])) // p.path is a single root-level .html file
}

// 3. indexing files
writeFileSync(join(dist, 'robots.txt'), robotsTxt())
writeFileSync(join(dist, 'sitemap.xml'), sitemapXml())

// the JSON-LD must stay valid JSON; fail the build otherwise
JSON.parse(JSON.stringify(jsonLd('pt-BR')))
console.log(`seo: ${PAGES.length} public pages, robots.txt, sitemap.xml (home title: ${tr('pt-BR', 'seo.home.title')})`)
