"""Generate JARVIS logo (arc reactor style) -> PNG + ICO."""
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import math, os

SIZE = 1024
img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

cx = cy = SIZE // 2

# Outer glow halo
halo = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
hd = ImageDraw.Draw(halo)
for r, a in [(500, 40), (470, 70), (440, 110)]:
    hd.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(80, 200, 255, a), width=8)
halo = halo.filter(ImageFilter.GaussianBlur(18))
img = Image.alpha_composite(img, halo)
d = ImageDraw.Draw(img)

# Dark base disc
d.ellipse((cx - 420, cy - 420, cx + 420, cy + 420), fill=(8, 16, 28, 255))

# Outer ring
d.ellipse((cx - 420, cy - 420, cx + 420, cy + 420), outline=(120, 220, 255, 255), width=14)
d.ellipse((cx - 380, cy - 380, cx + 380, cy + 380), outline=(60, 160, 220, 255), width=4)

# Hex/tri segments around mid ring
import random
random.seed(7)
for i in range(12):
    ang = i * (360 / 12)
    a1 = math.radians(ang - 12)
    a2 = math.radians(ang + 12)
    r_in, r_out = 300, 360
    pts = [
        (cx + r_in * math.cos(a1), cy + r_in * math.sin(a1)),
        (cx + r_out * math.cos(a1), cy + r_out * math.sin(a1)),
        (cx + r_out * math.cos(a2), cy + r_out * math.sin(a2)),
        (cx + r_in * math.cos(a2), cy + r_in * math.sin(a2)),
    ]
    d.polygon(pts, fill=(20, 80, 130, 255), outline=(100, 210, 255, 255))

# Inner ring
d.ellipse((cx - 260, cy - 260, cx + 260, cy + 260), outline=(140, 230, 255, 255), width=8)

# Core glow
core = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
cd = ImageDraw.Draw(core)
for r, a in [(220, 60), (180, 110), (140, 170), (100, 220), (60, 255)]:
    cd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(180, 240, 255, a))
core = core.filter(ImageFilter.GaussianBlur(8))
img = Image.alpha_composite(img, core)
d = ImageDraw.Draw(img)

# Letter J in center
try:
    font = ImageFont.truetype("arialbd.ttf", 360)
except Exception:
    font = ImageFont.load_default()
text = "J"
bbox = d.textbbox((0, 0), text, font=font)
tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
tx = cx - tw // 2 - bbox[0]
ty = cy - th // 2 - bbox[1] - 10
# shadow/glow
for off in [(0, 0)]:
    d.text((tx + off[0], ty + off[1]), text, font=font, fill=(255, 255, 255, 255))

# Final subtle outer rim highlight
d.ellipse((cx - 425, cy - 425, cx + 425, cy + 425), outline=(180, 240, 255, 90), width=2)

out_png = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
out_ico = os.path.join(os.path.dirname(__file__), "assets", "logo.ico")
os.makedirs(os.path.dirname(out_png), exist_ok=True)
img.save(out_png, "PNG")

# Multi-size ICO
sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
img.save(out_ico, sizes=sizes)
print("WROTE", out_png)
print("WROTE", out_ico)
