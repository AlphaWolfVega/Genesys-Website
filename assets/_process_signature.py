"""
Convert handwritten signature PNG into clean RGBA gold version.
Source is already RGBA (transparent background, black/dark ink).
"""
from PIL import Image, ImageOps
import os

SRC = os.path.join(os.path.dirname(__file__), "signature-alpha-source.png")
OUT = os.path.join(os.path.dirname(__file__), "signature-alpha-gold.png")

GOLD = (240, 214, 144)  # #F0D690

img = Image.open(SRC)
print(f"Source mode: {img.mode}, size: {img.size}")

if img.mode != "RGBA":
    img = img.convert("RGBA")

# Build a "darkness" channel: how dark is the ink?
# darkness = (255 - avg(R,G,B)) * (alpha/255)
r, g, b, a = img.split()
# avg luminance
gray = Image.merge("RGB", (r, g, b)).convert("L")
darkness_lum = ImageOps.invert(gray)  # dark pixels -> high values

# Multiply by source alpha (so transparent pixels stay transparent)
import numpy as np
darkness = np.array(darkness_lum, dtype=np.float32)
src_alpha = np.array(a, dtype=np.float32) / 255.0
darkness = darkness * src_alpha  # 0..255

# Stretch: ink core opaque, edges retain anti-aliasing
# Anything with darkness >= 100 -> alpha 255 (full ink)
# Anything with darkness <= 5   -> alpha 0   (background)
# In between: linear ramp
new_alpha = np.clip((darkness - 5) * (255 / (100 - 5)), 0, 255).astype(np.uint8)

print(f"Alpha stats: min={new_alpha.min()}, max={new_alpha.max()}")
print(f"alpha=0   pixels: {(new_alpha == 0).sum()}")
print(f"alpha=255 pixels: {(new_alpha == 255).sum()}")

# Auto-crop based on new_alpha bbox
alpha_img = Image.fromarray(new_alpha, "L")
bbox = alpha_img.getbbox()
print(f"BBox: {bbox}")
if bbox:
    pad = 25
    left = max(bbox[0] - pad, 0)
    top = max(bbox[1] - pad, 0)
    right = min(bbox[2] + pad, img.width)
    bottom = min(bbox[3] + pad, img.height)
    alpha_img = alpha_img.crop((left, top, right, bottom))
    new_alpha = np.array(alpha_img)

w, h = alpha_img.size
print(f"Cropped size: {w}x{h}")

# Build RGBA from gold + alpha
r2 = Image.new("L", (w, h), GOLD[0])
g2 = Image.new("L", (w, h), GOLD[1])
b2 = Image.new("L", (w, h), GOLD[2])
rgba = Image.merge("RGBA", (r2, g2, b2, alpha_img))

rgba.save(OUT, "PNG", optimize=True)
print(f"Saved: {OUT}")
