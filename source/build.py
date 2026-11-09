import json, math, os, re, hashlib
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = ROOT
DIST = os.path.dirname(ROOT)  # site files live at the repo root

poems = json.load(open(os.path.join(SRC, 'poems.json'), encoding='utf-8'))
tpl = open(os.path.join(SRC, 'app.html'), encoding='utf-8').read()

html = tpl.replace('/*FONTFACE*/\n', '')
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

# icons: the radar triangle in white on a graphite tile
def icon(size):
    S = 1024
    img = Image.new('RGB', (S, S))
    px = img.load()
    top, bot = (58, 58, 60), (22, 22, 24)
    for y in range(S):
        t = y / S
        c = tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3))
        for x in range(S):
            px[x, y] = c
    d = ImageDraw.Draw(img, 'RGBA')
    cx, cy, R = 512, 560, 330
    pts = lambda r: [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))) for a in (-90, 30, 150)]
    for r in (R * 0.4, R * 0.7):
        d.polygon(pts(r), outline=(255, 255, 255, 60), width=6)
    d.polygon(pts(R), outline=(255, 255, 255, 230), width=14)
    vals = [0.78, 0.62, 0.5]
    inner = [(cx + R * v * math.cos(math.radians(a)), cy + R * v * math.sin(math.radians(a))) for v, a in zip(vals, (-90, 30, 150))]
    d.polygon(inner, fill=(255, 255, 255, 46), outline=(255, 255, 255, 255), width=8)
    for x, y in inner:
        d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=(255, 255, 255, 255))
    return img.resize((size, size), Image.LANCZOS)

big = icon(1024)
for s in (180, 192, 512):
    big.resize((s, s), Image.LANCZOS).save(os.path.join(DIST, 'icon-%d.png' % s), optimize=True)

manifest = {
    'name': '日语修行', 'short_name': '修行', 'lang': 'zh-CN',
    'start_url': './', 'scope': './', 'display': 'standalone',
    'background_color': '#f5f5f7', 'theme_color': '#f5f5f7',
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
