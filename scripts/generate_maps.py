#!/usr/bin/env python3
"""Génère les cartes SVG statiques du Passeport de l'Explorateur du Québec :
- src/assets/maps/carte-globale.svg   : carte du trajet complet, façon carte au trésor,
  avec les 6 étapes cliquables (data-stop="<id>") reliées par un chemin en pointillés.
- src/assets/maps/carte-etape-N-*.svg : mini-carte "Tu es ici !" par étape, recadrée
  (même espace de coordonnées que la carte globale, juste un autre viewBox) avec un pin
  animé sur l'étape courante et les étapes précédente/suivante en plus petit.

Aucune dépendance externe, aucun réseau : tout est calculé et écrit en SVG texte.
Usage: python3 scripts/generate_maps.py
"""
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "src", "data")
OUT_DIR = os.path.join(ROOT, "src", "assets", "maps")

STOP_FILES = [
    "etape-1-montreal.json",
    "etape-2-mauricie.json",
    "etape-3-lac-saint-jean.json",
    "etape-4-fjord-saguenay.json",
    "etape-5-tadoussac.json",
    "etape-6-quebec.json",
]

SHORT_LABEL = {
    "etape-1-montreal": "Montréal",
    "etape-2-mauricie": "Mauricie",
    "etape-3-lac-saint-jean": "Lac-Saint-Jean",
    "etape-4-fjord-saguenay": "Anse-Saint-Jean",
    "etape-5-tadoussac": "Tadoussac",
    "etape-6-quebec": "Québec",
}

FONT_DISPLAY = "ui-rounded, 'SF Pro Rounded', 'Segoe UI Rounded', system-ui, sans-serif"
INK = "#2B2118"
INK_SOFT = "#5A4A3A"
PAPER = "#FFF8EC"
PAPER_ALT = "#FFF1D6"
LINE = "#E7D6B8"
TRAIL = "#9C7A4A"
RIVER = "#BFE0EA"

CANVAS_W, CANVAS_H = 640, 960
DRAW_X0, DRAW_W = 70, 500
DRAW_Y0, DRAW_H = 120, 680


def load_stops():
    stops = []
    for f in STOP_FILES:
        with open(os.path.join(DATA_DIR, f), encoding="utf-8") as fh:
            stops.append(json.load(fh))
    stops.sort(key=lambda s: s["ordre"])
    return stops


def project(lat, lon, lat_min, lat_max, lon_min, lon_max):
    x_norm = (lon - lon_min) / (lon_max - lon_min)
    y_norm = (lat_max - lat) / (lat_max - lat_min)
    return (DRAW_X0 + x_norm * DRAW_W, DRAW_Y0 + y_norm * DRAW_H)


def declutter(pts, min_dist=118, iterations=40):
    """Écarte légèrement les points trop proches (ex. Anse-Saint-Jean / Tadoussac)
    pour que badges et étiquettes restent lisibles, en gardant leur position relative."""
    for _ in range(iterations):
        moved = False
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                dx = pts[j]["x"] - pts[i]["x"]
                dy = pts[j]["y"] - pts[i]["y"]
                dist = math.hypot(dx, dy) or 0.001
                if dist < min_dist:
                    push = (min_dist - dist) / 2
                    ux, uy = dx / dist, dy / dist
                    pts[i]["x"] -= ux * push
                    pts[i]["y"] -= uy * push
                    pts[j]["x"] += ux * push
                    pts[j]["y"] += uy * push
                    moved = True
        if not moved:
            break
    return pts


def build_stop_points(stops):
    lats = [s["position"]["lat"] for s in stops]
    lons = [s["position"]["lon"] for s in stops]
    lat_min, lat_max = min(lats), max(lats)
    lon_min, lon_max = min(lons), max(lons)
    pts = []
    for s in stops:
        x, y = project(s["position"]["lat"], s["position"]["lon"], lat_min, lat_max, lon_min, lon_max)
        pts.append({
            "id": s["id"], "ordre": s["ordre"], "ville": SHORT_LABEL[s["id"]],
            "couleur": s["badge"]["couleur"], "emoji": s["badge"]["emoji"],
            "x": round(x, 1), "y": round(y, 1),
        })
    return declutter(pts)


# ---------- geometry helpers ----------

def smooth_wavy_path(points, bulge=0.16):
    """Chemin lissé (quadratic bezier) passant par une suite de points, façon rivière."""
    if len(points) < 2:
        return ""
    d = f"M {points[0][0]:.1f} {points[0][1]:.1f} "
    sign = 1
    for i in range(1, len(points)):
        x0, y0 = points[i - 1]
        x1, y1 = points[i]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy) or 1
        # perpendicular offset
        px, py = -dy / length, dx / length
        offset = length * bulge * sign
        cx, cy = mx + px * offset, my + py * offset
        d += f"Q {cx:.1f} {cy:.1f} {x1:.1f} {y1:.1f} "
        sign *= -1
    return d.strip()


def dashed_route_path(points):
    d = f"M {points[0]['x']:.1f} {points[0]['y']:.1f} "
    for p in points[1:]:
        d += f"L {p['x']:.1f} {p['y']:.1f} "
    return d.strip()


def arrow_marker(x0, y0, x1, y1, color):
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    angle = math.degrees(math.atan2(y1 - y0, x1 - x0))
    return (
        f'<polygon points="9,0 -6,-6 -6,6" fill="{color}" '
        f'transform="translate({mx:.1f},{my:.1f}) rotate({angle:.1f})" opacity="0.85"/>'
    )


# ---------- SVG piece builders ----------

def svg_frame(inset=16, dashed_inset=30):
    return f'''
  <rect x="0" y="0" width="{CANVAS_W}" height="{CANVAS_H}" rx="28" fill="url(#paperGrad)"/>
  <rect x="{inset}" y="{inset}" width="{CANVAS_W - 2*inset}" height="{CANVAS_H - 2*inset}" rx="20"
        fill="none" stroke="{INK_SOFT}" stroke-width="3"/>
  <rect x="{dashed_inset}" y="{dashed_inset}" width="{CANVAS_W - 2*dashed_inset}" height="{CANVAS_H - 2*dashed_inset}" rx="14"
        fill="none" stroke="{TRAIL}" stroke-width="1.5" stroke-dasharray="6 7" opacity="0.6"/>'''


def svg_corner_dots(inset=16):
    corners = [(inset, inset), (CANVAS_W - inset, inset), (inset, CANVAS_H - inset), (CANVAS_W - inset, CANVAS_H - inset)]
    out = []
    for cx, cy in corners:
        out.append(f'<circle cx="{cx}" cy="{cy}" r="4" fill="{TRAIL}" opacity="0.5"/>')
    return "\n  ".join(out)


def svg_compass(cx, cy, r=42):
    dirs = [("N", 0), ("E", 90), ("S", 180), ("O", 270)]
    points = []
    for i in range(8):
        ang = math.radians(i * 45 - 90)
        rr = r if i % 2 == 0 else r * 0.42
        points.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    labels = []
    for letter, ang_deg in dirs:
        ang = math.radians(ang_deg - 90)
        lx, ly = cx + (r + 16) * math.cos(ang), cy + (r + 16) * math.sin(ang)
        labels.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" font-family="{FONT_DISPLAY}" font-size="13" '
            f'font-weight="800" fill="{INK_SOFT}" text-anchor="middle" dominant-baseline="middle">{letter}</text>'
        )
    return f'''
  <g opacity="0.85">
    <polygon points="{poly}" fill="{PAPER_ALT}" stroke="{INK_SOFT}" stroke-width="1.5"/>
    <circle cx="{cx}" cy="{cy}" r="5" fill="{TRAIL}"/>
    {''.join(labels)}
  </g>'''


def point_group(p, mode="normal", pulse=False):
    """mode: normal | context (prev/next, smaller+faded)"""
    if mode == "normal":
        r, emoji_size, label_size, flag_r, flag_font = 30, 28, 16, 13, 13
        opacity = 1
    else:
        r, emoji_size, label_size, flag_r, flag_font = 20, 19, 12, 10, 10
        opacity = 0.62

    pulse_ring = ""
    if pulse:
        pulse_ring = f'''
      <circle class="pulse-ring" cx="0" cy="0" r="{r}" fill="none" stroke="{p['couleur']}" stroke-width="4"/>'''

    label = ""
    if label_size:
        label = (
            f'<text x="0" y="{r + label_size + 6}" text-anchor="middle" font-family="{FONT_DISPLAY}" '
            f'font-size="{label_size}" font-weight="800" fill="{INK}">{p["ville"]}</text>'
        )

    return f'''
  <g class="map-point{" map-point-current" if pulse else ""}" data-stop="{p['id']}" transform="translate({p['x']},{p['y']})" opacity="{opacity}">
    {pulse_ring}
    <circle r="{r}" fill="{PAPER_ALT}" stroke="{p['couleur']}" stroke-width="4"/>
    <text x="0" y="1" text-anchor="middle" dominant-baseline="central" font-size="{emoji_size}">{p['emoji']}</text>
    <circle cx="{r*0.72:.1f}" cy="{-r*0.72:.1f}" r="{flag_r}" fill="{p['couleur']}" stroke="{PAPER}" stroke-width="2"/>
    <text x="{r*0.72:.1f}" y="{-r*0.72+1:.1f}" text-anchor="middle" dominant-baseline="central"
          font-family="{FONT_DISPLAY}" font-size="{flag_font}" font-weight="800" fill="#fff">{p['ordre']}</text>
    {label}
  </g>'''


def defs_block():
    return f'''
  <defs>
    <linearGradient id="paperGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{PAPER}"/>
      <stop offset="1" stop-color="{PAPER_ALT}"/>
    </linearGradient>
  </defs>'''


# ---------- full documents ----------

def build_global_svg(pts):
    river_stlaurent = smooth_wavy_path([
        (pts[0]["x"], pts[0]["y"]),   # Montréal
        (pts[5]["x"], pts[5]["y"]),   # Québec
        (pts[4]["x"], pts[4]["y"]),   # Tadoussac
    ], bulge=0.14)
    river_saguenay = smooth_wavy_path([
        (pts[2]["x"], pts[2]["y"]),   # Lac-Saint-Jean
        (pts[3]["x"], pts[3]["y"]),   # Fjord
        (pts[4]["x"], pts[4]["y"]),   # Tadoussac
    ], bulge=0.18)

    route_d = dashed_route_path(pts)
    arrows = "\n  ".join(
        arrow_marker(pts[i]["x"], pts[i]["y"], pts[i + 1]["x"], pts[i + 1]["y"], TRAIL)
        for i in range(len(pts) - 1)
    )
    points_svg = "\n".join(point_group(p, mode="normal") for p in pts)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_W} {CANVAS_H}" role="img"
     aria-label="Carte du trajet : les 6 étapes du passeport de l'explorateur du Québec">
  {defs_block()}
  {svg_frame()}
  {svg_corner_dots()}
  <text x="{CANVAS_W/2}" y="60" text-anchor="middle" font-family="{FONT_DISPLAY}" font-size="30" font-weight="800" fill="{INK}">🧭 Mon itinéraire</text>
  <text x="{CANVAS_W/2}" y="88" text-anchor="middle" font-family="{FONT_DISPLAY}" font-size="14" fill="{INK_SOFT}">Touche une étape pour l'ouvrir !</text>

  <path d="{river_stlaurent}" fill="none" stroke="{RIVER}" stroke-width="16" stroke-linecap="round" opacity="0.8"/>
  <path d="{river_saguenay}" fill="none" stroke="{RIVER}" stroke-width="13" stroke-linecap="round" opacity="0.8"/>
  <text x="{pts[5]['x']-70:.0f}" y="{pts[5]['y']+70:.0f}" font-family="{FONT_DISPLAY}" font-size="12" font-style="italic" fill="{INK_SOFT}" opacity="0.8">fleuve Saint-Laurent</text>
  <text x="{(pts[2]['x']+pts[3]['x'])/2-40:.0f}" y="{(pts[2]['y']+pts[3]['y'])/2-14:.0f}" font-family="{FONT_DISPLAY}" font-size="11" font-style="italic" fill="{INK_SOFT}" opacity="0.8">rivière Saguenay</text>

  <path d="{route_d}" fill="none" stroke="{TRAIL}" stroke-width="3.5" stroke-dasharray="2 10" stroke-linecap="round"/>
  {arrows}

  {points_svg}

  {svg_compass(CANVAS_W - 96, CANVAS_H - 96)}
  <text x="60" y="{CANVAS_H - 40}" font-family="{FONT_DISPLAY}" font-size="12" fill="{INK_SOFT}">13 → 28 août 2026</text>
</svg>'''


def clamp_window(cx0, cy0, cx1, cy1):
    # shift back inside canvas bounds without resizing (keeps each map's natural aspect ratio;
    # the app sizes the container to fit rather than forcing a fixed ratio)
    if cx0 < 0:
        cx1 -= cx0
        cx0 = 0
    if cy0 < 0:
        cy1 -= cy0
        cy0 = 0
    if cx1 > CANVAS_W:
        cx0 -= (cx1 - CANVAS_W)
        cx1 = CANVAS_W
    if cy1 > CANVAS_H:
        cy0 -= (cy1 - CANVAS_H)
        cy1 = CANVAS_H
    cx0, cy0 = max(0, cx0), max(0, cy0)
    return cx0, cy0, cx1, cy1


def build_mini_svg(pts, idx):
    current = pts[idx]
    prev_p = pts[idx - 1] if idx > 0 else None
    next_p = pts[idx + 1] if idx < len(pts) - 1 else None
    shown = [p for p in (prev_p, current, next_p) if p]

    pad = 130
    xs = [p["x"] for p in shown]
    ys = [p["y"] for p in shown]
    x0, x1 = min(xs) - pad, max(xs) + pad
    y0, y1 = min(ys) - pad, max(ys) + pad
    min_w, min_h = 320, 320
    if (x1 - x0) < min_w:
        c = (x0 + x1) / 2
        x0, x1 = c - min_w / 2, c + min_w / 2
    if (y1 - y0) < min_h:
        c = (y0 + y1) / 2
        y0, y1 = c - min_h / 2, c + min_h / 2
    x0, y0, x1, y1 = clamp_window(x0, y0, x1, y1)
    vb_w, vb_h = x1 - x0, y1 - y0

    river_stlaurent = smooth_wavy_path([
        (pts[0]["x"], pts[0]["y"]), (pts[5]["x"], pts[5]["y"]), (pts[4]["x"], pts[4]["y"]),
    ], bulge=0.14)
    river_saguenay = smooth_wavy_path([
        (pts[2]["x"], pts[2]["y"]), (pts[3]["x"], pts[3]["y"]), (pts[4]["x"], pts[4]["y"]),
    ], bulge=0.18)
    route_d = dashed_route_path(pts)

    segs = []
    if prev_p:
        segs.append(arrow_marker(prev_p["x"], prev_p["y"], current["x"], current["y"], TRAIL))
    if next_p:
        segs.append(arrow_marker(current["x"], current["y"], next_p["x"], next_p["y"], TRAIL))

    groups = []
    if prev_p:
        groups.append(point_group(prev_p, mode="context"))
    groups.append(point_group(current, mode="normal", pulse=True))
    if next_p:
        groups.append(point_group(next_p, mode="context"))

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.1f} {y0:.1f} {vb_w:.1f} {vb_h:.1f}" role="img"
     aria-label="Tu es ici : {current['ville']}">
  <style>
    .map-point-current .pulse-ring {{
      animation: mapPulse 2.2s ease-out infinite;
      transform-origin: 0 0;
    }}
    @keyframes mapPulse {{
      0%   {{ transform: scale(1);    opacity: 0.55; }}
      70%  {{ transform: scale(1.55); opacity: 0; }}
      100% {{ transform: scale(1.55); opacity: 0; }}
    }}
  </style>
  {defs_block()}
  <rect x="{x0-40:.0f}" y="{y0-40:.0f}" width="{vb_w+80:.0f}" height="{vb_h+80:.0f}" fill="url(#paperGrad)"/>

  <path d="{river_stlaurent}" fill="none" stroke="{RIVER}" stroke-width="16" stroke-linecap="round" opacity="0.75"/>
  <path d="{river_saguenay}" fill="none" stroke="{RIVER}" stroke-width="13" stroke-linecap="round" opacity="0.75"/>

  <path d="{route_d}" fill="none" stroke="{TRAIL}" stroke-width="3.5" stroke-dasharray="2 10" stroke-linecap="round" opacity="0.9"/>
  {''.join(segs)}

  {''.join(groups)}
</svg>'''


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    stops = load_stops()
    pts = build_stop_points(stops)

    global_path = os.path.join(OUT_DIR, "carte-globale.svg")
    with open(global_path, "w", encoding="utf-8") as f:
        f.write(build_global_svg(pts))
    print(f"Écrit : {global_path}")

    for i, s in enumerate(stops):
        fname = f"carte-{s['id']}.svg"
        path = os.path.join(OUT_DIR, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(build_mini_svg(pts, i))
        print(f"Écrit : {path}")


if __name__ == "__main__":
    main()
