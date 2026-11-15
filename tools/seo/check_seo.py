"""Read-only SEO check of the Firewatch public pages (raw HTTP, no JavaScript).

Usage:  python -I tools/seo/check_seo.py http://127.0.0.1:5180            (a local server of web/dist)
        python -I tools/seo/check_seo.py https://firewatch.ikarusaurora.tech   (production, GET only)
Checks status/content type, canonical, hreflang, h1, noindex, duplicate titles, internal links and anchors, robots.txt,
sitemap.xml (every listed URL serves its own canonical) and that a missing data file is a real 404. Exit code 1 on a problem.
The informational lines show how unknown paths behave (the static server falls back to the application shell).
"""
import re, sys, urllib.request, urllib.error, hashlib
from html.parser import HTMLParser

BASE = sys.argv[1].rstrip('/')           # e.g. http://127.0.0.1:5180   or   https://firewatch.ikarusaurora.tech
SITE = 'https://firewatch.ikarusaurora.tech'
PATHS = ['/', '/en.html', '/sobre.html', '/about.html', '/metodologia.html', '/methodology.html']


def get(path, method='GET'):
    req = urllib.request.Request(BASE + path, method=method, headers={'User-Agent': 'seo-check'})
    try:
        r = urllib.request.urlopen(req, timeout=20)
        return r.status, r.headers.get('content-type', ''), r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('content-type', ''), ''


class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1 = 0
        self.links = []
        self.canon = []
        self.title = ''
        self._t = False
        self.scripts = []
        self.robots = []
        self.lang = None
        self.hreflang = {}
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.add(a['id'])
        if tag == 'html':
            self.lang = a.get('lang')
        if tag == 'h1':
            self.h1 += 1
        if tag == 'a' and 'href' in a:
            self.links.append(a['href'])
        if tag == 'link' and a.get('rel') == 'canonical':
            self.canon.append(a['href'])
        if tag == 'link' and a.get('rel') == 'alternate' and 'hreflang' in a:
            self.hreflang[a['hreflang']] = a['href']
        if tag == 'meta' and a.get('name') == 'robots':
            self.robots.append(a.get('content'))
        if tag == 'script':
            self.scripts.append(a.get('src') or ('inline:' + a.get('type', 'js')))
        if tag == 'title':
            self._t = True

    def handle_endtag(self, tag):
        if tag == 'title':
            self._t = False

    def handle_data(self, d):
        if self._t:
            self.title += d


problems = []
titles, internal = {}, set()
for path in PATHS:
    st, ct, html = get(path)
    p = P()
    p.feed(html)
    ok = st == 200 and 'text/html' in ct
    want = SITE + path
    print(f'{path:18} {st} {ct.split(";")[0]:10} lang={p.lang:6} h1={p.h1} canon={p.canon} title={p.title[:48]!r} scripts={len(p.scripts)}')
    if not ok: problems.append(f'{path}: status/type')
    if p.canon != [want]: problems.append(f'{path}: canonical {p.canon}')
    if p.h1 < 1: problems.append(f'{path}: no h1 in raw HTML')
    if p.robots: problems.append(f'{path}: robots meta {p.robots}')
    if p.title in titles: problems.append(f'{path}: duplicate title with {titles[p.title]}')
    titles[p.title] = path
    if 'x-default' not in p.hreflang or want not in p.hreflang.values(): problems.append(f'{path}: hreflang {p.hreflang}')
    for l in p.links:
        if l.startswith('http') or l.startswith('/#/'):
            continue
        if l.startswith('#'):
            if l[1:] not in p.ids: problems.append(f'{path}: broken anchor {l}')
        else:
            internal.add(l)

print('internal links:', sorted(internal))
for l in sorted(internal):
    st, ct, _ = get(l)
    if st != 200: problems.append(f'internal link {l} -> {st}')

# indexing files
st, ct, robots = get('/robots.txt')
print('robots.txt', st, ct)
if st != 200 or 'text/plain' not in ct or 'Sitemap: ' + SITE + '/sitemap.xml' not in robots or 'Disallow' in robots: problems.append('robots.txt')
st, ct, sm = get('/sitemap.xml')
locs = re.findall(r'<loc>([^<]+)</loc>', sm)
print('sitemap.xml', st, ct, len(locs), 'urls')
if st != 200 or 'xml' not in ct or locs != [SITE + p for p in PATHS]: problems.append('sitemap.xml')
for loc in locs:
    path = loc[len(SITE):]
    st, ct, html = get(path)
    if st != 200 or f'<link rel="canonical" href="{loc}">' not in html: problems.append(f'sitemap url {loc} does not serve its own canonical')

# soft-404 behaviour (informational): unknown paths serve the application shell with the HOME canonical
for path in ['/nao-existe/', '/sobre/', '/en/', '/og.png']:
    st, ct, html = get(path)
    c = re.findall(r'<link rel="canonical" href="([^"]+)"', html)
    print(f'[info] {path:14} {st} {ct.split(";")[0]} canonical={c}')

# scientific resources untouched
st, ct, m = get('/data/real/MANIFEST.json')
print('MANIFEST', st, hashlib.sha256(m.encode('utf-8')).hexdigest()[:16])
st, _, _ = get('/data/real/det/1999-01.json')
print('missing data file ->', st)
if st != 404: problems.append('missing data file is not 404')

print('\nPROBLEMS:', problems if problems else 'none')
sys.exit(1 if problems else 0)
