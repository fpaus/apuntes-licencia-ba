#!/usr/bin/env python3
"""Generate content/img/notes/arranque-subida.svg: uphill start in 5 steps.

Every step shows the same three pedals in the same order and colours as pedales-cambios.svg
(embrague red, freno amber, acelerador green). Pedal state: "down" (pressed, ↓), "up" (released, ↑),
"half" (friction point), None (resting). Arrow directions come from the state, never hand-placed.
"""
import math
from pathlib import Path

INK, MUTED, LINE, RED, AMBER, GREEN, GREEN_SOFT = "#1d2420", "#5d6a62", "#d9e0d9", "#c0392b", "#c98a00", "#2f8a4f", "#e2f1e6"
FONT = "system-ui, -apple-system, Segoe UI, Roboto, sans-serif"
PEDALS = (("E", RED), ("F", AMBER), ("A", GREEN))
STEPS = [  # (embrague, freno, acelerador), text lines, gear badge
    ((None, "down", None), ["Pisá el freno", "y mantenelo"], None),
    (("down", "down", None), ["Pisá el embrague", "y poné primera"], "1ª"),
    (("half", "down", None), ["Soltá el embrague", "hasta el punto", "de fricción"], "1ª"),
    (("half", "up", "down"), ["Soltá el freno", "mientras acelerás", "suave"], "1ª"),
    (("up", None, "down"), ["Cuando el auto", "avanza, soltá del", "todo el embrague"], "1ª"),
]
CW, CH = 180, 220


def arrow(x, y1, y2, color):
    d = 1 if y2 > y1 else -1
    return (f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="{color}" stroke-width="3" stroke-linecap="round"/>'
            f'<path d="M{x - 6},{y2 - 8 * d} L{x},{y2} L{x + 6},{y2 - 8 * d}" fill="none" stroke="{color}" stroke-width="3" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def pedals(cx, top, states):
    out = []
    for i, ((label, color), st) in enumerate(zip(PEDALS, states)):
        x = cx - 50 + i * 50
        drop = {"down": 14, "half": 7}.get(st, 0)  # pressed pedals sit lower
        fill = color if st else LINE
        out.append(f'<rect x="{x - 13}" y="{top + 18 + drop}" width="26" height="40" rx="6" fill="{fill}"/>')
        out.append(f'<text x="{x}" y="{top + 82}" text-anchor="middle" font-size="12" font-weight="bold" fill="{MUTED}">{label}</text>')
        if st == "down":
            out.append(arrow(x, top - 2, top + 14, INK))
        elif st == "up":
            out.append(arrow(x, top + 14, top - 2, INK))
        elif st == "half":
            out.append(f'<line x1="{x - 18}" y1="{top + 38}" x2="{x + 18}" y2="{top + 38}" stroke="{INK}" stroke-width="2" stroke-dasharray="4 3"/>')
    return "".join(out)


def step(i, states, text, gear):
    col, row = (i % 3, i // 3) if i < 3 else (i - 3, 1)
    x = 15 + col * (CW + 15) + (97 if row == 1 else 0)  # second row (2 cards) centred
    y = 300 + row * (CH + 15)
    cx = x + CW / 2
    out = [f'<rect x="{x}" y="{y}" width="{CW}" height="{CH}" rx="14" fill="#f4f6f3" stroke="{LINE}" stroke-width="2"/>',
           f'<circle cx="{x + 24}" cy="{y + 24}" r="14" fill="{GREEN}"/>',
           f'<text x="{x + 24}" y="{y + 29}" text-anchor="middle" font-size="15" font-weight="bold" fill="#ffffff">{i + 1}</text>',
           pedals(cx, y + 52, states)]
    if gear:
        out.append(f'<rect x="{x + CW - 46}" y="{y + 12}" width="34" height="24" rx="6" fill="{INK}"/>'
                   f'<text x="{x + CW - 29}" y="{y + 29}" text-anchor="middle" font-size="14" font-weight="bold" fill="#ffffff">{gear}</text>')
    for k, t in enumerate(text):
        out.append(f'<text x="{cx}" y="{y + 156 + k * 20}" text-anchor="middle" font-size="16" fill="{INK}">{t}</text>')
    return "\n".join(out)


def hill():
    ang = 18
    x1, y1, x2 = 150, 260, 450
    y2 = y1 - (x2 - x1) * math.tan(math.radians(ang))
    cx = 290
    cy = y1 - (cx - x1) * math.tan(math.radians(ang))
    car = (f'<g transform="translate({cx},{cy:.1f}) rotate({-ang})">'  # local x axis runs up the slope
           f'<path d="M-46,-12 L-46,-30 L-22,-30 L-10,-48 L22,-48 L34,-30 L46,-30 L46,-12 Z" fill="{GREEN}"/>'
           f'<path d="M-6,-44 L18,-44 L28,-31 L-14,-31 Z" fill="{GREEN_SOFT}"/>'  # windscreen toward the front (uphill)
           f'<circle cx="-26" cy="-10" r="10" fill="{INK}"/><circle cx="26" cy="-10" r="10" fill="{INK}"/></g>')
    up = (f'<g transform="translate({cx + 80},{cy - 70:.1f}) rotate({-ang})"><line x1="0" y1="0" x2="50" y2="0" stroke="{MUTED}" stroke-width="3"/>'
          f'<path d="M42,-6 L50,0 L42,6" fill="none" stroke="{MUTED}" stroke-width="3"/></g>')
    return (f'<path d="M{x1},{y1} L{x2},{y2:.1f} L{x2},{y1} Z" fill="{LINE}"/>' + car + up
            + f'<text x="{x1}" y="{y1 + 26}" font-size="14" fill="{MUTED}">E = embrague · F = freno · A = acelerador</text>')


H = 300 + 2 * CH + 15 + 20
svg = [f'<svg viewBox="0 0 600 {H}" xmlns="http://www.w3.org/2000/svg" font-family="{FONT}">',
       f'<rect x="0" y="0" width="600" height="{H}" rx="24" fill="#ffffff"/>',
       f'<text x="300" y="40" text-anchor="middle" font-size="27" font-weight="bold" fill="{INK}">Cómo arrancar en subida</text>',
       hill(), *[step(i, *s) for i, s in enumerate(STEPS)], "</svg>"]
Path(__file__).resolve().parent.parent.joinpath("content/img/notes/arranque-subida.svg").write_text("\n".join(svg) + "\n")
print("ok")
