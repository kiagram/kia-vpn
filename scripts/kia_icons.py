"""Generate the Kia VPN icon set (shield with a 'K' cut-out on a deep-blue/teal gradient).

Run from the repo root:  python scripts/kia_icons.py
Requires Pillow. Everything is drawn from the polygons below, so the PNG/ICO/WEBP
raster icons, the Android vector drawables and the SVGs all share one geometry.
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C1 = (11, 46, 111)   # deep blue  #0B2E6F
C2 = (15, 163, 163)  # teal       #0FA3A3
MID = "#0B5C8A"


def _quad(p0, p1, p2, n=24):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1])
            for t in (i / n for i in range(1, n + 1))]


def shield_points():
    """Shield outline in a 64x64 unit box."""
    pts = [(10, 13)]
    pts += _quad((10, 13), (21, 11), (32, 5))
    pts += _quad((32, 5), (43, 11), (54, 13))
    pts += [(54, 30)]
    pts += _quad((54, 30), (53, 50), (32, 60))
    pts += _quad((32, 60), (11, 50), (10, 30))
    return pts


K = [(22, 18), (28, 18), (28, 29), (38, 18), (45, 18), (33, 31.5), (45.5, 46), (38, 46),
     (29.5, 35.5), (28, 37.2), (28, 46), (22, 46)]
K_POINTS = [(x - 1.7, y) for x, y in K]
SHIELD = shield_points()


def path_d(points, scale=1.0, dx=0.0, dy=0.0):
    p = [f"{x * scale + dx:.2f},{y * scale + dy:.2f}" for x, y in points]
    return "M" + p[0] + " L" + " L".join(p[1:]) + " Z"


def glyph_d(scale=1.0, dx=0.0, dy=0.0):
    return path_d(SHIELD, scale, dx, dy) + " " + path_d(K_POINTS, scale, dx, dy)


# ---------------------------------------------------------------- raster helpers
def gradient(size):
    w, h = size
    g = Image.new("RGBA", size)
    px = g.load()
    for y in range(h):
        for x in range(w):
            t = (x / max(w - 1, 1) + y / max(h - 1, 1)) / 2
            px[x, y] = tuple(int(C1[i] + (C2[i] - C1[i]) * t) for i in range(3)) + (255,)
    return g


def glyph_mask(px, box_units=64, scale_frac=0.8, offset=(0, 0)):
    """Mask (L) of the shield with K hole, glyph occupying scale_frac of px."""
    ss = 4
    S = px * ss
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    k = S * scale_frac / box_units
    o = (S - box_units * k) / 2
    ox, oy = o + offset[0] * ss, o + offset[1] * ss
    d.polygon([(x * k + ox, y * k + oy) for x, y in SHIELD], fill=255)
    d.polygon([(x * k + ox, y * k + oy) for x, y in K_POINTS], fill=0)
    return m.resize((px, px), Image.LANCZOS)


def rounded_mask(px, radius_frac=0.22, circle=False):
    ss = 4
    m = Image.new("L", (px * ss, px * ss), 0)
    d = ImageDraw.Draw(m)
    if circle:
        d.ellipse([0, 0, px * ss - 1, px * ss - 1], fill=255)
    else:
        d.rounded_rectangle([0, 0, px * ss - 1, px * ss - 1], radius=int(px * ss * radius_frac), fill=255)
    return m.resize((px, px), Image.LANCZOS)


def app_icon(px, circle=False, glyph=0.66, colors=None):
    global C1, C2
    if colors:
        saved = (C1, C2)
        C1, C2 = colors
    bg = gradient((px, px))
    if colors:
        C1, C2 = saved
    bg.putalpha(rounded_mask(px, circle=circle))
    white = Image.new("RGBA", (px, px), (255, 255, 255, 255))
    out = bg.copy()
    out.paste(white, (0, 0), glyph_mask(px, scale_frac=glyph))
    return out


def white_glyph(px, frac=0.95):
    im = Image.new("RGBA", (px, px), (255, 255, 255, 0))
    im.putalpha(glyph_mask(px, scale_frac=frac))
    return im


def save_ico(img_fn, path, sizes):
    big = img_fn(256)
    big.save(path, format="ICO", sizes=[(s, s) for s in sizes])


def p(*parts):
    return os.path.join(ROOT, *parts)


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def main():
    # master
    app_icon(1024).save(p("assets", "images", "source", "kia_vpn_icon_1024.png"))

    # Windows
    save_ico(lambda s: app_icon(s), p("windows", "runner", "resources", "app_icon.ico"),
             [16, 24, 32, 48, 64, 128, 256])

    # tray icons (default / dark / connected / disconnected)
    tray = {
        "tray_icon": None,
        "tray_icon_dark": None,
        "tray_icon_connected": ((10, 90, 50), (40, 190, 110)),
        "tray_icon_disconnected": ((80, 86, 96), (150, 156, 166)),
    }
    for name, cols in tray.items():
        fn = (lambda s, c=cols: app_icon(s, glyph=0.78, colors=c))
        fn(128).save(p("assets", "images", name + ".png"))
        save_ico(fn, p("assets", "images", name + ".ico"), [16, 32, 48, 64, 128])

    # Android legacy launcher icons
    res = p("android", "app", "src", "main", "res")
    for d, s in {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}.items():
        app_icon(s).save(os.path.join(res, f"mipmap-{d}", "ic_launcher.webp"), "WEBP", lossless=True)
        app_icon(s, circle=True).save(os.path.join(res, f"mipmap-{d}", "ic_launcher_round.webp"), "WEBP", lossless=True)
    # notification icons (white silhouette)
    white_glyph(24).save(os.path.join(res, "drawable-mdpi", "ic_stat_logo.png"))
    white_glyph(36).save(os.path.join(res, "drawable-hdpi", "ic_stat_logo.png"))
    # pre-Android-12 splash
    app_icon(324, glyph=0.62).save(os.path.join(res, "drawable-xxxhdpi", "splash.png"))
    # Android TV banner
    ban = gradient((320, 180))
    ban.paste(Image.new("RGBA", (120, 120), (255, 255, 255, 255)), (18, 30), glyph_mask(120, scale_frac=0.9))
    d = ImageDraw.Draw(ban)
    try:
        font = ImageFont.truetype("arialbd.ttf", 44)
    except OSError:
        font = ImageFont.load_default()
    d.text((146, 64), "Kia VPN", fill=(255, 255, 255, 255), font=font)
    ban.save(os.path.join(res, "mipmap-xhdpi", "ic_banner.png"))

    # Android adaptive foreground (vector): glyph in the 66dp safe zone of a 108dp canvas
    scale = 56 / 64
    off = (108 - 64 * scale) / 2
    write(os.path.join(res, "drawable", "ic_launcher_foreground.xml"), f'''<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path
        android:fillColor="#FFFFFFFF"
        android:fillType="evenOdd"
        android:pathData="{glyph_d(scale, off, off)}" />
</vector>
''')
    # Android 12 splash icon: blue disc with white glyph
    scale = 40 / 64
    off = (108 - 64 * scale) / 2
    write(os.path.join(res, "drawable", "android12splash.xml"), f'''<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path
        android:fillColor="{MID}"
        android:pathData="M54,18 A36,36 0 1,1 53.99,18 Z" />
    <path
        android:fillColor="#FFFFFFFF"
        android:fillType="evenOdd"
        android:pathData="{glyph_d(scale, off, off)}" />
</vector>
''')

    # macOS Icon Composer layer (white glyph; colours come from icon.json)
    write(p("macos", "Runner", "AppIcon.icon", "Assets", "logo.svg"),
          f'<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">\n'
          f'<path fill-rule="evenodd" clip-rule="evenodd" fill="#FFFFFF" d="{glyph_d()}"/>\n</svg>\n')

    # Standalone SVG of the full app icon (for docs / README)
    write(p("assets", "images", "source", "kia_vpn_icon.svg"),
          '<svg width="512" height="512" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">\n'
          '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
          '<stop offset="0" stop-color="#0B2E6F"/><stop offset="1" stop-color="#0FA3A3"/></linearGradient></defs>\n'
          '<rect width="64" height="64" rx="14" fill="url(#g)"/>\n'
          f'<path fill-rule="evenodd" fill="#FFFFFF" d="{glyph_d(0.66, 64 * 0.17, 64 * 0.17)}"/>\n</svg>\n')


if __name__ == "__main__":
    main()
