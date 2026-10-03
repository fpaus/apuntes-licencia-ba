#!/usr/bin/env python3
"""Generate content/img/notes/malas-practicas.svg: 3x3 grid of bad driving habits.

Each icon is drawn inside its own box (ICON_W x ICON_H around the cell's icon centre), clear of the
number badge and the ✗ mark. Arrowheads are computed from the direction of motion, never hand-placed.
"""
import math
from pathlib import Path

INK, MUTED, LINE, RED, RED_SOFT, AMBER, GREEN, GREEN_SOFT, ROAD = (
    "#1d2420", "#5d6a62", "#d9e0d9", "#c0392b", "#fbe7e4", "#c98a00", "#2f8a4f", "#e2f1e6", "#4a4f4c")
FONT = "system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
CW, CH, GAP, X0, Y0 = 180, 250, 15, 15, 58

CELLS = [
    ("pedal_rest", ["Descansar el pie", "en el embrague"], ["Desgasta el embrague", "sin necesidad."]),
    ("light_clutch", ["Pisar el embrague", "en los semáforos"], ["Desgaste y fatiga", "del sistema."]),
    ("tacho_high", ["Arrancar", "muy fuerte"], ["Más consumo", "y más desgaste."]),
    ("hill", ["Sostener el auto en", "subida con el embrague"], ["Desgasta el embrague", "y causa fallas."]),
    ("shift_clutch", ["Cambiar sin pisar el", "embrague a fondo"], ["Dificulta el cambio y", "daña la transmisión."]),
    ("force_lever", ["Forzar la", "palanca"], ["Puede dañar la", "caja de cambios."]),
    ("tacho_low", ["Circular a bajas", "revoluciones"], ["El motor trabaja", "forzado."]),
    ("curve", ["Entrar rápido", "en las curvas"], ["Riesgo de perder el", "control."]),
    ("bite_point", ["Ignorar el punto", "de fricción"], ["Tirones, desgaste y", "pérdida de control."]),
]


def arrow(x1, y1, x2, y2, color, w=4, head=11):
    """Straight arrow from (x1,y1) to (x2,y2); the head follows the segment direction."""
    a = math.atan2(y2 - y1, x2 - x1)
    p1 = (x2 - head * math.cos(a - 0.5), y2 - head * math.sin(a - 0.5))
    p2 = (x2 - head * math.cos(a + 0.5), y2 - head * math.sin(a + 0.5))
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{w}" stroke-linecap="round"/>'
            f'<path d="M{p1[0]:.1f},{p1[1]:.1f} L{x2:.1f},{y2:.1f} L{p2[0]:.1f},{p2[1]:.1f}" fill="none" stroke="{color}" '
            f'stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')


def pedal(cx, cy, press=0.0, color=MUTED):
    """Side view of a pedal: pivot at the top, pad at the bottom; press in 0..1 swings it toward the floor."""
    ang = math.radians(15 + 40 * press)
    px, py = cx + 30 * math.sin(ang), cy - 22 + 44 * math.cos(ang)
    return (f'<circle cx="{cx}" cy="{cy - 22}" r="4" fill="{color}"/>'
            f'<line x1="{cx}" y1="{cy - 22}" x2="{px:.1f}" y2="{py:.1f}" stroke="{color}" stroke-width="6" stroke-linecap="round"/>'
            f'<line x1="{px - 9:.1f}" y1="{py - 7:.1f}" x2="{px + 9:.1f}" y2="{py + 7:.1f}" stroke="{color}" stroke-width="8" stroke-linecap="round"/>')


def shoe(x, y, rot):
    """Shoe whose sole (local y = 0) lies on the point (x, y), tilted by rot degrees."""
    return (f'<g transform="translate({x:.1f},{y:.1f}) rotate({rot})"><path d="M-22,-5 Q-22,-16 -6,-16 L14,-12 Q24,-10 24,-3 '
            f'L24,0 L-22,0 Z" fill="{INK}"/></g>')


def pad(cx, cy, press):
    ang = math.radians(15 + 40 * press)
    return cx + 30 * math.sin(ang), cy - 22 + 44 * math.cos(ang)


def tacho(cx, cy, value, red_zone=True):
    """Rev counter: a 240° dial from 0 (lower left) to 8 (lower right); value in 0..8."""
    r = 30
    out = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#ffffff" stroke="{INK}" stroke-width="3"/>']
    if red_zone:  # 6..8 in red
        a1, a2 = math.radians(210 - 240 * 6 / 8), math.radians(210 - 240)
        out.append(f'<path d="M{cx + (r - 4) * math.cos(a1):.1f},{cy - (r - 4) * math.sin(a1):.1f} A{r - 4},{r - 4} 0 0,1 '
                   f'{cx + (r - 4) * math.cos(a2):.1f},{cy - (r - 4) * math.sin(a2):.1f}" fill="none" stroke="{RED}" stroke-width="5"/>')
    a = math.radians(210 - 240 * value / 8)
    out.append(f'<line x1="{cx}" y1="{cy}" x2="{cx + (r - 8) * math.cos(a):.1f}" y2="{cy - (r - 8) * math.sin(a):.1f}" '
               f'stroke="{RED if value > 5 else INK}" stroke-width="4" stroke-linecap="round"/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="4" fill="{INK}"/>')
    out.append(f'<text x="{cx}" y="{cy + r + 16}" text-anchor="middle" font-size="12" fill="{MUTED}">RPM</text>')
    return "".join(out)


def lever(cx, cy):
    return (f'<rect x="{cx - 22}" y="{cy + 22}" width="44" height="8" rx="3" fill="{MUTED}"/>'
            f'<line x1="{cx}" y1="{cy + 22}" x2="{cx}" y2="{cy - 12}" stroke="{MUTED}" stroke-width="7" stroke-linecap="round"/>'
            f'<circle cx="{cx}" cy="{cy - 18}" r="11" fill="{INK}"/>')


def icon(kind, cx, cy):
    if kind == "pedal_rest":  # shoe resting on the clutch pedal pad
        px, py = pad(cx, cy, 0.15)
        return pedal(cx, cy, 0.15) + shoe(px - 4, py - 6, 38)  # sole along the pad (pad tilt is atan(7/9) = 38°)
    if kind == "light_clutch":  # red light + pedal held down
        return (f'<rect x="{cx - 52}" y="{cy - 30}" width="22" height="58" rx="6" fill="{INK}"/>'
                f'<circle cx="{cx - 41}" cy="{cy - 17}" r="7" fill="{RED}"/><circle cx="{cx - 41}" cy="{cy}" r="7" fill="{MUTED}"/>'
                f'<circle cx="{cx - 41}" cy="{cy + 17}" r="7" fill="{MUTED}"/>'
                + pedal(cx + 12, cy + 6, 1.0) + arrow(cx + 40, cy - 30, cx + 40, cy + 2, RED, 3, 9))
    if kind == "tacho_high":
        return tacho(cx, cy - 4, 7.3)
    if kind == "hill":  # car on an uphill slope, nose up the hill
        ang = 20
        x1, y1, x2, y2 = cx - 55, cy + 26, cx + 50, cy + 26 - 105 * math.tan(math.radians(ang))
        mx, my = cx - 5, cy + 26 - 50 * math.tan(math.radians(ang))
        return (f'<path d="M{x1},{y1} L{x2:.1f},{y2:.1f} L{x2:.1f},{y1} Z" fill="{LINE}"/>'
                f'<g transform="translate({mx:.1f},{my:.1f}) rotate({-ang})"><rect x="-22" y="-16" width="44" height="14" rx="5" fill="{RED}"/>'
                f'<circle cx="-12" cy="-2" r="5" fill="{INK}"/><circle cx="12" cy="-2" r="5" fill="{INK}"/></g>')
    if kind == "shift_clutch":  # H-pattern 1-3-5 / 2-4-R + half-pressed pedal
        gx, gy, out = cx - 40, cy - 16, []
        for i in range(3):
            out.append(f'<line x1="{gx + i * 20}" y1="{gy}" x2="{gx + i * 20}" y2="{gy + 36}" stroke="{MUTED}" stroke-width="3"/>')
        out.append(f'<line x1="{gx}" y1="{gy + 18}" x2="{gx + 40}" y2="{gy + 18}" stroke="{MUTED}" stroke-width="3"/>')
        for i, (t, b) in enumerate((("1", "2"), ("3", "4"), ("5", "R"))):
            out.append(f'<text x="{gx + i * 20}" y="{gy - 4}" text-anchor="middle" font-size="11" fill="{INK}">{t}</text>')
            out.append(f'<text x="{gx + i * 20}" y="{gy + 50}" text-anchor="middle" font-size="11" fill="{INK}">{b}</text>')
        return "".join(out) + pedal(cx + 36, cy + 4, 0.45, RED)
    if kind == "force_lever":  # lever pushed hard sideways: arrow points into the lever
        return lever(cx + 12, cy + 2) + arrow(cx - 50, cy - 16, cx - 6, cy - 16, RED, 6, 12)
    if kind == "tacho_low":
        return tacho(cx, cy - 4, 1.0, red_zone=False)
    if kind == "curve":  # road bending right; car arrow follows the tangent at the end
        p0, c, p1 = (cx - 52, cy + 28), (cx - 40, cy - 30), (cx + 40, cy - 30)
        t0 = (p1[0] - c[0], p1[1] - c[1])  # end tangent of the quadratic
        end = (p1[0] + 10 * t0[0] / math.hypot(*t0), p1[1] + 10 * t0[1] / math.hypot(*t0))
        return (f'<path d="M{p0[0]},{p0[1]} Q{c[0]},{c[1]} {p1[0]},{p1[1]}" fill="none" stroke="{ROAD}" stroke-width="18" stroke-linecap="round"/>'
                f'<path d="M{p0[0]},{p0[1]} Q{c[0]},{c[1]} {p1[0]},{p1[1]}" fill="none" stroke="#f2c200" stroke-width="2" stroke-dasharray="6 5"/>'
                + arrow(p1[0] - 8, p1[1], end[0] + 8, end[1], RED, 4, 10)
                + f'<text x="{cx + 2}" y="{cy + 24}" font-size="13" font-weight="bold" fill="{RED}">rápido</text>')
    if kind == "bite_point":  # pedal travel bar with the friction point marked and skipped
        x, top, bot = cx - 6, cy - 32, cy + 30
        mid = (top + bot) / 2
        return (f'<line x1="{x}" y1="{top}" x2="{x}" y2="{bot}" stroke="{LINE}" stroke-width="10" stroke-linecap="round"/>'
                f'<line x1="{x - 12}" y1="{mid}" x2="{x + 12}" y2="{mid}" stroke="{AMBER}" stroke-width="4"/>'
                f'<text x="{x + 18}" y="{mid + 5}" font-size="12" fill="{AMBER}">fricción</text>'
                f'<text x="{x - 16}" y="{top + 6}" text-anchor="end" font-size="11" fill="{MUTED}">suelto</text>'
                f'<text x="{x - 16}" y="{bot + 4}" text-anchor="end" font-size="11" fill="{MUTED}">a fondo</text>'
                + arrow(x - 26, bot - 8, x - 26, top + 14, RED, 3, 9))
    raise ValueError(kind)


def cell(i, kind, title, cons):
    x, y = X0 + (i % 3) * (CW + GAP), Y0 + (i // 3) * (CH + GAP)
    cx, cy = x + CW / 2, y + 92
    out = [f'<rect x="{x}" y="{y}" width="{CW}" height="{CH}" rx="14" fill="{RED_SOFT}"/>',
           f'<circle cx="{x + 24}" cy="{y + 24}" r="14" fill="{RED}"/>',
           f'<text x="{x + 24}" y="{y + 29}" text-anchor="middle" font-size="15" font-weight="bold" fill="#ffffff">{i + 1}</text>',
           f'<circle cx="{x + CW - 24}" cy="{y + 24}" r="13" fill="none" stroke="{RED}" stroke-width="3"/>',
           f'<path d="M{x + CW - 31},{y + 17} L{x + CW - 17},{y + 31} M{x + CW - 17},{y + 17} L{x + CW - 31},{y + 31}" stroke="{RED}" stroke-width="3" stroke-linecap="round"/>',
           icon(kind, cx, cy)]
    for k, t in enumerate(title):
        out.append(f'<text x="{cx}" y="{y + 162 + k * 20}" text-anchor="middle" font-size="16" font-weight="bold" fill="{INK}">{t}</text>')
    for k, t in enumerate(cons):
        out.append(f'<text x="{cx}" y="{y + 212 + k * 19}" text-anchor="middle" font-size="15" fill="{MUTED}">{t}</text>')
    return "\n".join(out)


H = Y0 + 3 * CH + 2 * GAP + 70
svg = [f'<svg viewBox="0 0 600 {H}" xmlns="http://www.w3.org/2000/svg" font-family="{FONT}">',
       f'<rect x="0" y="0" width="600" height="{H}" rx="24" fill="#ffffff"/>',
       f'<text x="300" y="38" text-anchor="middle" font-size="27" font-weight="bold" fill="{INK}">Malas prácticas al manejar</text>',
       *[cell(i, *c) for i, c in enumerate(CELLS)],
       f'<rect x="{X0}" y="{H - 58}" width="{600 - 2 * X0}" height="40" rx="12" fill="{GREEN_SOFT}"/>',
       f'<text x="300" y="{H - 32}" text-anchor="middle" font-size="16" font-weight="bold" fill="{GREEN}">Buenos hábitos = más seguridad + menos gastos</text>',
       "</svg>"]
Path(__file__).resolve().parent.parent.joinpath("content/img/notes/malas-practicas.svg").write_text("\n".join(svg) + "\n")
print("ok")
