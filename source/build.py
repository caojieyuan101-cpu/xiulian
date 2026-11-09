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

# icons: "three rings at sunset" - half a coral sun on the horizon inside two halos (gold, mauve),
# which are also the listening / reading / speaking rings; a faint reflection below.
# Drawn at 2x the 1024 design grid and scaled down for smooth edges.
def icon(size):
    from PIL import ImageFilter
    K = 2
    S = 1024 * K
    hz = 640 * K                      # horizon
    img = Image.new('RGB', (S, S))
    d = ImageDraw.Draw(img)
    def lerp(a, b, t):
        return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
    for y in range(S):                # sky above the horizon, water below
        t = y / S
        c = lerp((35, 28, 32), (46, 34, 38), t / .62) if t < .625 else lerp((24, 19, 26), (18, 14, 16), (t - .625) / .375)
        d.line([(0, y), (S, y)], fill=c)
    glow = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse([512 * K - 380 * K, hz - 260 * K, 512 * K + 380 * K, hz + 260 * K], fill=(255, 138, 98, 120))
    glow = glow.filter(ImageFilter.GaussianBlur(150 * K))
    img = Image.alpha_composite(img.convert('RGBA'), glow)
    layer = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, w = 512 * K, 64 * K
    def halo(r, col):                 # top half ring with round ends
        r *= K
        d.arc([cx - r - w / 2, hz - r - w / 2, cx + r + w / 2, hz + r + w / 2], 180, 360, fill=col, width=w)
        for x in (cx - r, cx + r):
            d.ellipse([x - w / 2, hz - w / 2, x + w / 2, hz + w / 2], fill=col)
    halo(330, (169, 134, 173, 255))   # mauve
    halo(232, (233, 172, 60, 255))    # gold
    r = 150 * K
    d.pieslice([cx - r, hz - r, cx + r, hz + r], 180, 360, fill=(230, 90, 62, 255))         # the sun
    ry = r * .55                      # its reflection, flattened by the water
    d.pieslice([cx - r, hz + 14 * K - ry, cx + r, hz + 14 * K + ry], 0, 180, fill=(230, 90, 62, 30))
    d.rounded_rectangle([150 * K, hz - 4 * K, 874 * K, hz + 6 * K], radius=5 * K, fill=(244, 233, 230, 230))
    d.rounded_rectangle([300 * K, 720 * K, 724 * K, 728 * K], radius=4 * K, fill=(244, 233, 230, 64))
    d.rounded_rectangle([390 * K, 790 * K, 634 * K, 798 * K], radius=4 * K, fill=(244, 233, 230, 36))
    img = Image.alpha_composite(img, layer).convert('RGB')
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
# icons count too, so a new icon alone still refreshes the offline copy
icons = b''.join(open(os.path.join(DIST, 'icon-%d.png' % n), 'rb').read() for n in (180, 192, 512))
ver = hashlib.sha1(html.encode() + bg + icons).hexdigest()[:10]
sw = open(os.path.join(SRC, 'sw.js'), encoding='utf-8').read().replace('__VERSION__', ver)
open(os.path.join(DIST, 'sw.js'), 'w', encoding='utf-8').write(sw)
open(os.path.join(DIST, '.nojekyll'), 'w').write('')
print('version', ver)
