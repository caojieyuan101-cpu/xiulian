import base64, glob, io, json, math, os, re, shutil, hashlib
from fontTools.ttLib import TTFont
from fontTools import subset
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = ROOT
DIST = os.path.dirname(ROOT)  # site files live at the repo root
FONTDIR = os.environ.get('FONTDIR', '/home/claude/fontsrc/package/files')  # npm pack @fontsource/noto-serif-sc@5.1.1
os.makedirs(DIST, exist_ok=True)

poems = json.load(open(os.path.join(SRC, 'poems.json'), encoding='utf-8'))
tpl = open(os.path.join(SRC, 'app.html'), encoding='utf-8').read()

# characters drawn in the serif face: poems, authors, titles, realm names
realms = re.findall(r"\[\d+,'([^']+)'", tpl)
chars = set()
for t, a, ti in poems:
    chars |= set(t + a + ti)
for r in realms:
    chars |= set(r)
chars |= set('《》·')
chars = {c for c in chars if not c.isspace()}

faces = []
covered = set()
for path in sorted(glob.glob(os.path.join(FONTDIR, 'noto-serif-sc-*-400-normal.woff2'))):
    f = TTFont(path)
    cmap = f.getBestCmap()
    need = {c for c in chars if ord(c) in cmap and c not in covered}
    if not need:
        continue
    opts = subset.Options()
    opts.flavor = 'woff2'
    opts.layout_features = ['vert', 'vrt2', 'kern', 'palt', 'vpal']
    opts.name_IDs = []
    opts.notdef_outline = False
    sub = subset.Subsetter(opts)
    sub.populate(text=''.join(sorted(need)))
    sub.subset(f)
    buf = io.BytesIO()
    f.flavor = 'woff2'
    f.save(buf)
    covered |= need
    b64 = base64.b64encode(buf.getvalue()).decode()
    rng = ','.join('U+%X' % ord(c) for c in sorted(need))
    faces.append("@font-face{font-family:'XiuSerif';font-style:normal;font-weight:400;font-display:swap;src:url(data:font/woff2;base64,%s) format('woff2');unicode-range:%s}" % (b64, rng))

missing = chars - covered
print('serif chars', len(chars), 'covered', len(covered), 'missing', ''.join(sorted(missing)))

html = tpl.replace('/*FONTFACE*/', '\n'.join(faces))
html = html.replace('/*POEMS*/[]', json.dumps(poems, ensure_ascii=False))
open(os.path.join(DIST, 'index.html'), 'w', encoding='utf-8').write(html)
print('index.html', round(len(html.encode()) / 1024), 'KB')

# icons: a radar triangle on deep indigo
def icon(size):
    S = 1024
    img = Image.new('RGB', (S, S))
    px = img.load()
    top, bot = (64, 56, 140), (22, 18, 48)
    for y in range(S):
        t = y / S
        c = tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3))
        for x in range(S):
            px[x, y] = c
    d = ImageDraw.Draw(img, 'RGBA')
    cx, cy, R = 512, 560, 330
    pts = lambda r: [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in (-90, 30, 150)]
    for r in (R * 0.4, R * 0.7):
        d.polygon(pts(r), outline=(255, 255, 255, 70), width=6)
    d.polygon(pts(R), outline=(255, 255, 255, 235), width=14)
    vals = [0.78, 0.62, 0.5]
    inner = [(cx + R * v * math.cos(math.radians(a)), cy + R * v * math.sin(math.radians(a))) for v, a in zip(vals, (-90, 30, 150))]
    d.polygon(inner, fill=(255, 120, 150, 150), outline=(255, 255, 255, 255), width=8)
    for (x, y), col in zip(inner, [(125, 122, 255), (255, 159, 10), (255, 55, 95)]):
        d.ellipse([x - 26, y - 26, x + 26, y + 26], fill=col + (255,), outline=(255, 255, 255, 255), width=8)
    return img.resize((size, size), Image.LANCZOS)

big = icon(1024)
for s in (180, 192, 512):
    big.resize((s, s), Image.LANCZOS).save(os.path.join(DIST, 'icon-%d.png' % s), optimize=True)

manifest = {
    'name': '日语修行', 'short_name': '修行', 'lang': 'zh-CN',
    'start_url': './', 'scope': './', 'display': 'standalone',
    'background_color': '#f2f2f7', 'theme_color': '#f2f2f7',
    'icons': [
        {'src': 'icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
        {'src': 'icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any maskable'},
    ],
}
json.dump(manifest, open(os.path.join(DIST, 'manifest.webmanifest'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

ver = hashlib.sha1(html.encode()).hexdigest()[:10]
sw = open(os.path.join(SRC, 'sw.js'), encoding='utf-8').read().replace('__VERSION__', ver)
open(os.path.join(DIST, 'sw.js'), 'w', encoding='utf-8').write(sw)
open(os.path.join(DIST, '.nojekyll'), 'w').write('')
print('version', ver)
