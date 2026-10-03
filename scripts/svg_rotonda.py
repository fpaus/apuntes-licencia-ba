#!/usr/bin/env python3
"""Generate content/img/notes/rotonda.svg: two-lane roundabout, right-hand traffic.

Angles use the math convention (y up): point(θ, r) = (CX + r cosθ, CY - r sinθ), so increasing θ is
counter-clockwise on screen — the circulation direction. Paths are sampled from (θ, r) and arrowheads
follow their last segment. Roads: you drive on the right half of each arm (relative to your direction).
"""
import math
from pathlib import Path

INK, MUTED, LINE, RED, GREEN, GREEN_SOFT, ROAD, YELLOW = (
    "#1d2420", "#5d6a62", "#d9e0d9", "#c0392b", "#2f8a4f", "#e2f1e6", "#4a4f4c", "#f2c200")
FONT = "system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
CX, CY = 300, 340
R_OUT, R_DIV, R_ISL = 150, 108, 66          # outer edge, lane divider, island
R_INNER, R_OUTER = 87, 129                  # centre of inner and outer lane
HALF = 44                                   # half width of each road arm; lanes at ±22 from its centre
LANE = 22


def pt(theta, r):
    t = math.radians(theta)
    return CX + r * math.cos(t), CY - r * math.sin(t)


def poly(points, color, width=5, dash=None):
    d = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    (x1, y1), (x2, y2) = points[-2], points[-1]
    a = math.atan2(y2 - y1, x2 - x1)
    head = [(x2 - 16 * math.cos(a - 0.45), y2 - 16 * math.sin(a - 0.45)), (x2, y2), (x2 - 16 * math.cos(a + 0.45), y2 - 16 * math.sin(a + 0.45))]
    h = " ".join(f"{x:.1f},{y:.1f}" for x, y in head)
    return (f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"{extra}/>'
            f'<polyline points="{h}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>')


def arc_points(t0, t1, r0, r1, n=40):
    """Sample from (t0, r0) to (t1, r1); the radius changes linearly (a spiral) for lane changes."""
    return [pt(t0 + (t1 - t0) * i / n, r0 + (r1 - r0) * i / n) for i in range(n + 1)]


def cross(x, y):
    return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="17" fill="#ffffff" stroke="{RED}" stroke-width="3"/>'
            f'<path d="M{x - 9:.1f},{y - 9:.1f} L{x + 9:.1f},{y + 9:.1f} M{x + 9:.1f},{y - 9:.1f} L{x - 9:.1f},{y + 9:.1f}" stroke="{RED}" stroke-width="3" stroke-linecap="round"/>')


out = []
o = out.append
H = 800
o(f'<rect x="0" y="0" width="600" height="{H}" rx="24" fill="#ffffff"/>')
o(f'<text x="300" y="40" text-anchor="middle" font-size="27" font-weight="bold" fill="{INK}">La rotonda: dos carriles</text>')
# road arms + ring
o(f'<rect x="{CX - HALF}" y="70" width="{2 * HALF}" height="{2 * (CY - 70)}" fill="{ROAD}"/>')
o(f'<rect x="20" y="{CY - HALF}" width="560" height="{2 * HALF}" fill="{ROAD}"/>')
o(f'<circle cx="{CX}" cy="{CY}" r="{R_OUT}" fill="{ROAD}"/>')
for x1, y1, x2, y2 in ((CX, 70, CX, CY - R_OUT), (CX, CY + R_OUT, CX, 2 * CY - 70), (20, CY, CX - R_OUT, CY), (CX + R_OUT, CY, 580, CY)):
    o(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{YELLOW}" stroke-width="3" stroke-dasharray="12 10"/>')
o(f'<circle cx="{CX}" cy="{CY}" r="{R_DIV}" fill="none" stroke="#ffffff" stroke-width="3" stroke-dasharray="12 10"/>')
o(f'<circle cx="{CX}" cy="{CY}" r="{R_ISL}" fill="{GREEN_SOFT}" stroke="#ffffff" stroke-width="3"/>')
# circulation chevrons on the outer lane, pointing counter-clockwise (tangent = θ + 90°)
for th in (45, 135, 225, 315):
    x, y = pt(th, R_OUTER)
    a = math.radians(th + 90)
    dx, dy = math.cos(a), -math.sin(a)
    px, py = -dy, dx
    o(f'<polyline points="{x - 13 * dx + 7 * px:.1f},{y - 13 * dy + 7 * py:.1f} {x:.1f},{y:.1f} {x - 13 * dx - 7 * px:.1f},{y - 13 * dy - 7 * py:.1f}" '
      f'fill="none" stroke="#ffffff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')

# GREEN: enter from the west (eastbound = lower half), merge into the inner lane, circulate, merge out, exit east.
# Cubic Béziers whose end tangents match the inner-lane circle, so the curve has no kinks.
def tangent(theta):  # counter-clockwise direction of travel on screen at angle theta
    t = math.radians(theta)
    return -math.sin(t), -math.cos(t)


y_in, K = CY + LANE, 60
p0, p3 = (CX - R_OUT - 6, y_in), (CX + R_OUT + 6, y_in)
a1, a2 = 235, 305
p1, p2 = pt(a1, R_INNER), pt(a2, R_INNER)
d1, d2 = tangent(a1), tangent(a2)
green = (f'M30,{y_in} L{p0[0]:.1f},{p0[1]:.1f} '
         f'C{p0[0] + K:.1f},{p0[1]:.1f} {p1[0] - K * d1[0]:.1f},{p1[1] - K * d1[1]:.1f} {p1[0]:.1f},{p1[1]:.1f} '
         f'A{R_INNER},{R_INNER} 0 0,0 {p2[0]:.1f},{p2[1]:.1f} '
         f'C{p2[0] + K * d2[0]:.1f},{p2[1] + K * d2[1]:.1f} {p3[0] - K:.1f},{p3[1]:.1f} {p3[0]:.1f},{p3[1]:.1f} L564,{y_in}')
o(f'<path d="{green}" fill="none" stroke="{GREEN}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>')
o(f'<polyline points="550,{y_in - 9} 566,{y_in} 550,{y_in + 9}" fill="none" stroke="{GREEN}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>')

# RED 1: in the inner lane, leaves straight to the west exit (westbound = upper half), cutting across the outer lane
r1 = arc_points(40, 120, R_INNER, R_INNER, 20) + [(CX - R_OUT - 4, CY - LANE), (40, CY - LANE)]
o(poly(r1, RED, 4, "10 7"))
(ax, ay), (bx, by) = r1[-3], r1[-2]  # straight leg from the inner lane to the west exit
f = next(i / 100 for i in range(101) if math.hypot(ax + (bx - ax) * i / 100 - CX, ay + (by - ay) * i / 100 - CY) >= R_DIV + 21)
mx, my = ax + (bx - ax) * f, ay + (by - ay) * f  # on the outer lane it cuts across
o(cross(mx, my))

# RED 2: straight through the island, south to north (northbound = right/east half)
x2 = CX + LANE
o(poly([(x2, 2 * CY - 80), (x2, 85)], RED, 4, "10 7"))
o(cross(x2, CY))

# labels
o(f'<rect x="28" y="70" width="190" height="62" rx="12" fill="{GREEN_SOFT}"/>')
o(f'<text x="123" y="96" text-anchor="middle" font-size="17" font-weight="bold" fill="{INK}">Prioridad:</text>')
o(f'<text x="123" y="118" text-anchor="middle" font-size="17" font-weight="bold" fill="{INK}">el que ya circula</text>')
o(f'<rect x="436" y="{CY + 60}" width="140" height="62" rx="12" fill="{GREEN_SOFT}"/>')
o(f'<text x="506" y="{CY + 86}" text-anchor="middle" font-size="17" font-weight="bold" fill="{INK}">Señalizá</text>')
o(f'<text x="506" y="{CY + 108}" text-anchor="middle" font-size="17" font-weight="bold" fill="{INK}">la salida</text>')
ly = 2 * CY - 30 + 40
for i, (color, a, b) in enumerate(((GREEN, "Circulá por el carril interno;", "pasá al externo para salir."),
                                   (RED, "Nunca salgas desde el interno", "ni cruces en línea recta."))):
    y = ly + i * 52
    o(f'<circle cx="44" cy="{y - 5}" r="8" fill="{color}"/>')
    o(f'<text x="62" y="{y}" font-size="16" fill="{INK}">{a}</text><text x="62" y="{y + 20}" font-size="16" fill="{INK}">{b}</text>')

svg = f'<svg viewBox="0 0 600 {H}" xmlns="http://www.w3.org/2000/svg" font-family="{FONT}">\n' + "\n".join(out) + "\n</svg>\n"
Path(__file__).resolve().parent.parent.joinpath("content/img/notes/rotonda.svg").write_text(svg)
print("ok")
