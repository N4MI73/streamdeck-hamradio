"""Stream Deck icons for the IC-7610 Radio / Modes folders (N4MI). 144x144 PNG, dark theme.

Run:  python make_icons.py   (needs Pillow: pip install pillow)
Writes the PNGs to an out/ folder next to this script, plus _sheet.png for a quick review.
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)
S = 144
BG = (16, 22, 34)
FG = (236, 240, 245)
DIM = (140, 152, 170)
TEAL, AMBER, VIOLET, RED, GREEN = (40, 190, 200), (245, 170, 40), (160, 120, 240), (225, 60, 55), (80, 200, 110)
# Fonts: DejaVu (Linux) first, then Windows' Arial Bold / Arial Narrow Bold.
def _first(*paths):
    for p in paths:
        if os.path.exists(p):
            return p
    raise SystemExit("No bold font found - edit B / BC in make_icons.py")
B = _first("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/arialbd.ttf")
BC = _first("/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf", "C:/Windows/Fonts/arialnb.ttf", B)


def font(path, size): return ImageFont.truetype(path, size)


def base(accent):
    im = Image.new("RGB", (S, S), BG)
    d = ImageDraw.Draw(im)
    d.rectangle([0, S - 12, S, S], fill=accent)          # accent bar along the bottom
    return im, d


def ctext(d, y, text, f, fill=FG):
    w = d.textlength(text, font=f)
    d.text(((S - w) / 2, y), text, font=f, fill=fill)


def fit(d, text, path, start, maxw):
    size = start
    while size > 10 and d.textlength(text, font=font(path, size)) > maxw:
        size -= 2
    return font(path, size)


def save(im, name): im.save(os.path.join(OUT, name + ".png"))


# --- band buttons ---
for band in ["160", "80", "40", "30", "20", "17", "15", "12", "10", "6"]:
    im, d = base(TEAL)
    f = fit(d, band, B, 64, 112)
    ctext(d, 22, band, f)
    ctext(d, 96, "METERS", font(B, 17), DIM)
    save(im, f"band_{band}m")

# --- mode buttons: label + small filter tag ---
for name, label, fil in [("mode_ssb", "SSB", "FIL2"), ("mode_cw", "CW", "FIL3"), ("mode_usbd1", "USB-D1", "FIL1")]:
    im, d = base(AMBER)
    f = fit(d, label, B, 46, 124)
    ctext(d, 30 + (46 - f.size) // 2, label, f)
    ctext(d, 92, fil, font(B, 18), AMBER)
    if label == "SSB":
        ctext(d, 112, "LSB/USB AUTO", font(BC, 11), DIM)
    save(im, name)

# --- filter cycle: three nested passband shapes ---
im, d = base(AMBER)
for i, w in enumerate([92, 64, 36]):
    x0 = (S - w) / 2
    d.rounded_rectangle([x0, 22 + i * 14, x0 + w, 76], radius=6, outline=[FG, AMBER, DIM][i], width=4)
ctext(d, 88, "FILTER", font(B, 22))
save(im, "filter_cycle")

# --- +/- 100 kHz ---
for name, up in [("step_up_100k", True), ("step_down_100k", False)]:
    im, d = base(VIOLET)
    cx = S / 2
    if up:
        d.polygon([(cx, 14), (cx - 30, 52), (cx + 30, 52)], fill=VIOLET)
        ctext(d, 58, "+100", font(B, 30))
    else:
        d.polygon([(cx, 52), (cx - 30, 14), (cx + 30, 14)], fill=VIOLET)
        ctext(d, 58, "−100", font(B, 30))
    ctext(d, 96, "kHz", font(B, 17), DIM)
    save(im, name)

# --- stop helper ---
im, d = base(RED)
pts = []
import math
for k in range(8):
    a = math.radians(22.5 + 45 * k)
    pts.append((S / 2 + 40 * math.cos(a), 56 + 40 * math.sin(a)))
d.polygon(pts, fill=RED)
ctext(d, 44, "STOP", font(B, 24))
ctext(d, 104, "RIG LINK", font(BC, 14), DIM)
save(im, "rig_stop")

# --- Radio folder: simple transceiver front panel ---
im, d = base(GREEN)
d.rounded_rectangle([18, 22, 126, 82], radius=8, outline=FG, width=4)
d.rectangle([28, 32, 78, 56], fill=(30, 60, 70), outline=TEAL, width=2)      # display
d.text((32, 35), "7610", font=font(BC, 16), fill=TEAL)
d.ellipse([88, 32, 116, 60], outline=FG, width=4)                           # VFO knob
d.ellipse([99, 43, 105, 49], fill=FG)
for x in (30, 44, 58, 72):
    d.rectangle([x, 64, x + 9, 72], fill=DIM)                                # keys
ctext(d, 94, "RADIO", font(B, 22))
save(im, "folder_radio")

# --- Modes folder: waveform ---
im, d = base(AMBER)
pts = [(16 + i * 2, 50 - 22 * math.sin(i / 7.0) * math.exp(-((i - 28) / 26.0) ** 2)) for i in range(57)]
d.line(pts, fill=AMBER, width=4)
ctext(d, 86, "MODES", font(B, 22))
ctext(d, 112, "FILTER · ±100k", font(BC, 11), DIM)
save(im, "folder_modes")

# --- phase 2 (2026-10-27): split, preamp, NR, NB, power ---
CYAN, PINK = (60, 170, 255), (235, 90, 170)
for name, top, sub in [("split_ssb", "UP 5", "SSB"), ("split_cw", "UP 1", "CW")]:
    im, d = base(CYAN)
    ctext(d, 12, "SPLIT", font(B, 22), CYAN)
    ctext(d, 44, top, font(B, 38))
    ctext(d, 96, sub, font(B, 18), DIM)
    save(im, name)
im, d = base(CYAN)
ctext(d, 22, "SPLIT", font(B, 28))
ctext(d, 66, "OFF", font(B, 30), CYAN)
save(im, "split_off")

im, d = base(PINK)
for i, h in enumerate([16, 30, 46]):                      # three rising bars = steps
    x = 38 + i * 26
    d.rectangle([x, 70 - h, x + 16, 70], fill=[DIM, FG, PINK][i])
ctext(d, 82, "PREAMP", font(B, 20))
ctext(d, 108, "OFF·1·2", font(BC, 12), DIM)
save(im, "preamp_cycle")
for name, label, sub in [("nr_toggle", "NR", "NOISE RED."), ("nb_toggle", "NB", "BLANKER")]:
    im, d = base(PINK)
    ctext(d, 22, label, font(B, 50))
    ctext(d, 86, sub, font(BC, 15), DIM)
    ctext(d, 106, "ON / OFF", font(BC, 12), PINK)
    save(im, name)

for name, label, col in [("power_off", "OFF", RED)]:
    im, d = base(col)
    cx, cy, r = S / 2, 50, 30                                # power symbol
    d.arc([cx - r, cy - r, cx + r, cy + r], start=-60, end=240, fill=col, width=7)
    d.line([cx, cy - r - 6, cx, cy + 2], fill=col, width=7)
    ctext(d, 92, "RADIO " + label, font(B, 18))
    save(im, name)

# --- contact sheet for review ---
names = sorted(os.listdir(OUT))
names = [n for n in names if n.endswith(".png") and n != "_sheet.png"]
cols = 5
sheet = Image.new("RGB", (cols * (S + 10) + 10, ((len(names) + cols - 1) // cols) * (S + 10) + 10), (60, 60, 60))
for i, n in enumerate(names):
    sheet.paste(Image.open(os.path.join(OUT, n)), (10 + (i % cols) * (S + 10), 10 + (i // cols) * (S + 10)))
sheet.save(os.path.join(os.path.dirname(OUT), "_sheet.png"))
print(len(names), "icons")
