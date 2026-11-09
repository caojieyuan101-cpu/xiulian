import base64, glob, io, json, math, os, re, shutil, hashlib
from fontTools.ttLib import TTFont
from fontTools import subset
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = ROOT
DIST = os.path.dirname(ROOT)  # site files live at the repo root
# npm pack @fontsource/noto-serif-sc@5.1.1, unpack, and point FONTDIR at package/files
FONTDIR = os.environ.get('FONTDIR', os.path.join(ROOT, 'fontsrc', 'package', 'files'))
if not glob.glob(os.path.join(FONTDIR, 'noto-serif-sc-*-400-normal.woff2')):
    raise SystemExit('找不到字体：%s\n先运行 npm pack @fontsource/noto-serif-sc@5.1.1 并解压，再用 FONTDIR 指定 package/files 目录' % FONTDIR)
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
# titles, the seal and the big numbers are set in the serif too
chars |= set('今天专注修为记录分钟小时天个0123456789./:%')
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

# the same app as a Claude Artifact page: records sync through its data.json.
# The Artifact tool wraps the page in its own document, so emit only the
# title, the styles and the body; data.json is published once, with the first version.
ART = os.path.join(SRC, 'artifact')
os.makedirs(ART, exist_ok=True)
title = re.search(r'<title>.*?</title>', html, re.S).group(0)
style = re.search(r'<style>.*?</style>', html, re.S).group(0)
body = re.search(r'<body>(.*)</body>', html, re.S).group(1)
body = body.replace("/*TARGET*/'pwa'", "'artifact'")
# the page frame already pads for the phone's safe areas at the top
style = style.replace('</style>', 'main{padding-top:8px}\n</style>')
open(os.path.join(ART, 'index.html'), 'w', encoding='utf-8').write(title + '\n' + style + '\n' + body.strip() + '\n')
if not os.path.exists(os.path.join(ART, 'data.json')):
    open(os.path.join(ART, 'data.json'), 'w', encoding='utf-8').write('{"v":1}')
print('artifact/index.html', round(os.path.getsize(os.path.join(ART, 'index.html')) / 1024), 'KB')

# icons: the radar triangle over a sunset sky, a city wall in silhouette
def icon(size):
    S = 1024
    img = Image.new('RGB', (S, S))
    px = img.load()
    stops = [(0, (95, 86, 108)), (.38, (155, 122, 133)), (.62, (217, 100, 74)), (.8, (236, 138, 74)), (1, (241, 178, 74))]
    for y in range(S):
        t = y / S
        for (a, ca), (b, cb) in zip(stops, stops[1:]):
            if a <= t <= b:
                u = (t - a) / (b - a)
                c = tuple(int(ca[i] * (1 - u) + cb[i] * u) for i in range(3))
                break
        for x in range(S):
            px[x, y] = c
    d = ImageDraw.Draw(img, 'RGBA')
    wall = 800
    d.rectangle([0, wall + 34, S, S], fill=(28, 23, 24, 255))
    for x in range(20, S, 104):
        d.rectangle([x, wall, x + 52, wall + 40], fill=(28, 23, 24, 255))
    cx, cy, R = 512, 470, 290
    pts = lambda r: [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in (-90, 30, 150)]
    for r in (R * 0.4, R * 0.7):
        d.polygon(pts(r), outline=(255, 255, 255, 80), width=6)
    d.polygon(pts(R), outline=(255, 255, 255, 240), width=14)
    vals = [0.78, 0.62, 0.5]
    inner = [(cx + R * v * math.cos(math.radians(a)), cy + R * v * math.sin(math.radians(a))) for v, a in zip(vals, (-90, 30, 150))]
    d.polygon(inner, fill=(255, 226, 160, 110), outline=(255, 255, 255, 255), width=8)
    for (x, y), col in zip(inner, [(231, 212, 240), (255, 210, 122), (255, 138, 98)]):
        d.ellipse([x - 24, y - 24, x + 24, y + 24], fill=col + (255,), outline=(255, 255, 255, 255), width=7)
    return img.resize((size, size), Image.LANCZOS)

big = icon(1024)
for s in (180, 192, 512):
    big.resize((s, s), Image.LANCZOS).save(os.path.join(DIST, 'icon-%d.png' % s), optimize=True)

manifest = {
    'name': '日语修行', 'short_name': '修行', 'lang': 'zh-CN',
    'start_url': './', 'scope': './', 'display': 'standalone',
    'background_color': '#1b1719', 'theme_color': '#1b1719',
    'icons': [
        {'src': 'icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
        {'src': 'icon-512.png', 'sizes': '512x512', 'type': 'image/png', 'purpose': 'any maskable'},
    ],
}
json.dump(manifest, open(os.path.join(DIST, 'manifest.webmanifest'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

# the background photos ship beside the page, for the site and the Claude page alike
bg = b''
for name in ('bg-dusk.jpg', 'bg-street.jpg'):
    data = open(os.path.join(SRC, name), 'rb').read()
    bg += data
    for d in (DIST, ART):
        open(os.path.join(d, name), 'wb').write(data)
ver = hashlib.sha1(html.encode() + bg).hexdigest()[:10]
sw = open(os.path.join(SRC, 'sw.js'), encoding='utf-8').read().replace('__VERSION__', ver)
open(os.path.join(DIST, 'sw.js'), 'w', encoding='utf-8').write(sw)
open(os.path.join(DIST, '.nojekyll'), 'w').write('')
print('version', ver)
