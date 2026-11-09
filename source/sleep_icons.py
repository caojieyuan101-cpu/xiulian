"""Icons for the sleep app in sleep/: a crescent moon and a few stars over a still night horizon,
drawn in the same manner as the 日语修行 icon. Run: python3 source/sleep_icons.py (needs Pillow)."""
import os
from PIL import Image, ImageDraw, ImageFilter

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'sleep')
K = 2
S = 1024 * K
hz = 690 * K


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


img = Image.new('RGB', (S, S))
d = ImageDraw.Draw(img)
for y in range(S):  # sky above, water below
    t = y / S
    c = lerp((20, 19, 30), (38, 34, 58), t / .674) if y < hz else lerp((22, 20, 32), (15, 14, 20), (y - hz) / (S - hz))
    d.line([(0, y), (S, y)], fill=c)

cx, cy, r = 512 * K, 430 * K, 190 * K
glow = Image.new('RGBA', (S, S), (0, 0, 0, 0))
ImageDraw.Draw(glow).ellipse([cx - 300 * K, cy - 300 * K, cx + 300 * K, cy + 300 * K], fill=(242, 207, 126, 70))
glow = glow.filter(ImageFilter.GaussianBlur(120 * K))
img = Image.alpha_composite(img.convert('RGBA'), glow)

# crescent = disc minus an offset disc
moon = Image.new('L', (S, S), 0)
md = ImageDraw.Draw(moon)
md.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
ox, oy = cx + 95 * K, cy - 70 * K
md.ellipse([ox - r * .92, oy - r * .92, ox + r * .92, oy + r * .92], fill=0)
layer = Image.new('RGBA', (S, S), (242, 207, 126, 255))
img.paste(layer, (0, 0), moon)

top = Image.new('RGBA', (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(top)
for x, y, s, a in [(250, 250, 14, 230), (760, 230, 10, 200), (820, 470, 12, 220), (190, 520, 8, 160), (640, 160, 7, 150)]:
    x, y, s = x * K, y * K, s * K
    d.ellipse([x - s, y - s, x + s, y + s], fill=(236, 235, 244, a))

# horizon and reflection of the moon in the water
d.rounded_rectangle([150 * K, hz - 4 * K, 874 * K, hz + 6 * K], radius=5 * K, fill=(236, 235, 244, 220))
for y, w, a in [(770, 150, 90), (830, 100, 60), (885, 60, 36)]:
    d.rounded_rectangle([cx - 40 * K - w * K, y * K, cx - 40 * K + w * K, y * K + 9 * K], radius=4 * K, fill=(242, 207, 126, a))

img = Image.alpha_composite(img, top)
big = img.convert('RGB').resize((1024, 1024), Image.LANCZOS)
for s in (180, 192, 512):
    big.resize((s, s), Image.LANCZOS).save(os.path.join(OUT, 'icon-%d.png' % s), optimize=True)
print('icons written to', OUT)
