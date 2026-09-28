"""Render the hand-designed, animated figures that live in assets/.

    python scripts/build_static.py            # writes assets/*-{dark,light}.svg

The shapes are computed, not drawn: the header trace is an actual leaky
integrate-and-fire simulation, the spike cascades propagate through a small
random graph with refractoriness, and the nematode's body follows a travelling
sine wave. Output is deterministic so re-running only changes files when the
code changes.
"""

from __future__ import annotations

import math
from pathlib import Path

from svgkit import MONO, PALETTES, SANS, SERIF, Rng, document, esc, fmt, points_to_path

ASSETS = Path(__file__).resolve().parent.parent / "assets"

REDUCED_MOTION = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"


# --------------------------------------------------------------------------- #
# Fig. 0 — header: spiking network + membrane potential sweep
# --------------------------------------------------------------------------- #

def lif_trace(duration_ms: int, seed: int) -> tuple[list[float], list[int]]:
    """Leaky integrate-and-fire neuron driven by Ornstein–Uhlenbeck noise."""
    rng = Rng(seed)
    tau_m, v_rest, v_reset, theta = 20.0, -70.0, -74.0, -52.0
    v, drive, trace, spikes = v_rest, 0.0, [], []
    refractory = 0
    for t in range(duration_ms):
        drive += (-drive / 12.0) + 2.4 * rng.gauss() / math.sqrt(12.0)
        mu = 19.5 + 4.0 * math.sin(2 * math.pi * t / 420.0)
        if refractory:
            refractory -= 1
            v = v_reset
        else:
            v += (-(v - v_rest) + mu + 6.0 * drive) / tau_m
        if v >= theta:
            spikes.append(t)
            trace.append(30.0)
            v, refractory = v_reset, 3
            continue
        trace.append(v)
    return trace, spikes


def spike_network(width: float, height: float, x0: float, y0: float, seed: int):
    rng = Rng(seed)
    nodes: list[tuple[float, float]] = []
    while len(nodes) < 22:
        p = (x0 + rng.uniform(0, width), y0 + rng.uniform(0, height))
        if all(math.dist(p, q) > 38 for q in nodes):
            nodes.append(p)
    edges: set[tuple[int, int]] = set()
    for i, p in enumerate(nodes):
        nearest = sorted(range(len(nodes)), key=lambda j: math.dist(p, nodes[j]))[1:4]
        for j in nearest[: 2 + (rng.random() < 0.45)]:
            edges.add((min(i, j), max(i, j)))
    adjacency: dict[int, list[int]] = {i: [] for i in range(len(nodes))}
    for i, j in edges:
        adjacency[i].append(j)
        adjacency[j].append(i)
    return nodes, sorted(edges), adjacency


def cascade(nodes, adjacency, cycle: float, seeds, seed: int):
    """Event-driven spike propagation with conduction delay + refractoriness."""
    rng = Rng(seed)
    fires: dict[int, list[float]] = {i: [] for i in range(len(nodes))}
    travels: list[tuple[int, int, float, float]] = []
    queue = sorted(seeds)
    while queue:
        t, node, sender = queue.pop(0)
        if t > cycle - 0.45 or any(abs(t - f) < 1.6 for f in fires[node]):
            continue
        fires[node].append(t)
        for nxt in adjacency[node]:
            if nxt == sender or rng.random() > 0.72:
                continue
            delay = math.dist(nodes[node], nodes[nxt]) / 150.0
            travels.append((node, nxt, t + 0.04, t + 0.04 + delay))
            queue.append((t + 0.06 + delay, nxt, node))
        queue.sort()
    return fires, travels


def hero(theme: str) -> str:
    c = PALETTES[theme]
    w, h, cycle = 900, 290, 7.0
    out: list[str] = []

    out.append(
        "<defs>"
        f'<linearGradient id="name" x1="0" x2="1"><stop offset="0" stop-color="{c["blue"]}"/>'
        f'<stop offset="1" stop-color="{c["violet"]}"/></linearGradient>'
        f'<radialGradient id="glow"><stop offset="0" stop-color="{c["cyan"]}" stop-opacity=".55"/>'
        f'<stop offset="1" stop-color="{c["cyan"]}" stop-opacity="0"/></radialGradient>'
        f'<clipPath id="panel"><rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="14"/></clipPath>'
        "</defs>"
    )
    out.append(f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="{c["panel"]}" stroke="{c["border"]}"/>')

    grid = "".join(f"M{x} 0V{h}" for x in range(30, w, 30)) + "".join(f"M0 {y}H{w}" for y in range(20, h, 30))
    out.append(f'<g clip-path="url(#panel)"><path d="{grid}" stroke="{c["grid"]}" stroke-width="1"/></g>')

    # corner metadata, oscilloscope style
    out.append(
        f'<g font-family="{MONO}" font-size="11" fill="{c["muted"]}">'
        f'<text x="24" y="28">sa-aris / fig. 0</text>'
        f'<text x="{w - 24}" y="28" text-anchor="end">spiking network · LIF neuron · simulated</text></g>'
    )

    # name + tagline
    out.append(
        f'<text x="46" y="112" font-family="{SANS}" font-size="72" font-weight="800" '
        f'letter-spacing="-2" fill="url(#name)">Aris</text>'
        f'<text x="48" y="146" font-family="{SANS}" font-size="20" fill="{c["text"]}">'
        "Software engineer who simulates brains.</text>"
        f'<text x="48" y="172" font-family="{MONO}" font-size="12.5" fill="{c["muted"]}">'
        "full-stack · mobile · data · connectomics · spiking networks</text>"
    )
    out.append(
        f'<g font-family="{MONO}" font-size="12.5"><text x="48" y="202" fill="{c["green"]}">&gt;'
        f'<tspan fill="{c["text"]}" dx="8">simulating a fly brain, one spike at a time</tspan>'
        f'<tspan class="caret" fill="{c["green"]}">▍</tspan></text></g>'
    )

    # network
    nodes, edges, adjacency = spike_network(330, 150, 530, 48, seed=7)
    seeds = [(0.15, 3, -1), (2.45, 17, -1), (4.7, 9, -1)]
    fires, travels = cascade(nodes, adjacency, cycle, seeds, seed=11)
    edge_path = "".join(f"M{fmt(nodes[i][0])} {fmt(nodes[i][1])}L{fmt(nodes[j][0])} {fmt(nodes[j][1])}" for i, j in edges)
    out.append(f'<path d="{edge_path}" stroke="{c["faint"]}" stroke-width="1" opacity=".75"/>')

    anim = f'dur="{cycle}s" repeatCount="indefinite"'
    for a, b, start, end in travels:
        (ax, ay), (bx, by) = nodes[a], nodes[b]
        s, e = start / cycle, min(end / cycle, 0.999)
        out.append(
            f'<circle r="2.4" fill="{c["cyan"]}" opacity="0">'
            f'<animateMotion {anim} calcMode="linear" path="M{fmt(ax)} {fmt(ay)}L{fmt(bx)} {fmt(by)}" '
            f'keyPoints="0;0;1;1" keyTimes="0;{s:.4f};{e:.4f};1"/>'
            f'<animate attributeName="opacity" {anim} calcMode="discrete" values="0;1;0" keyTimes="0;{s:.4f};{e:.4f}"/>'
            "</circle>"
        )
    for i, (x, y) in enumerate(nodes):
        frames = [(0.0, 0.0)]
        for f in sorted(fires[i]):
            frames += [(f / cycle, 0.0), (f / cycle + 0.006, 1.0), (min(f / cycle + 0.09, 0.999), 0.0)]
        frames.append((1.0, 0.0))
        times = ";".join(f"{t:.4f}" for t, _ in frames)
        values = ";".join(fmt(v) for _, v in frames)
        halo = (
            f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="13" fill="url(#glow)" opacity="0">'
            f'<animate attributeName="opacity" {anim} values="{values}" keyTimes="{times}"/></circle>'
            if fires[i] else ""
        )
        out.append(
            halo
            + f'<circle cx="{fmt(x)}" cy="{fmt(y)}" r="3.3" fill="{c["panel"]}" stroke="{c["blue"]}" stroke-width="1.4"/>'
        )

    # membrane potential sweep along the bottom
    trace, _ = lif_trace(806, seed=5)
    top, bottom, x_start = 214, 272, 30

    def vy(v: float) -> float:
        return bottom - (v + 78.0) / (30.0 + 78.0) * (bottom - top)

    pts = [(x_start + i, vy(v)) for i, v in enumerate(trace)]
    d = points_to_path(pts)
    out.append(
        f'<path d="M{x_start} {fmt(vy(-52))}H{x_start + len(trace)}" stroke="{c["amber"]}" '
        f'stroke-width="1" stroke-dasharray="3 5" opacity=".7"/>'
        f'<text x="{x_start + len(trace) + 6}" y="{fmt(vy(-52) + 4)}" font-family="{SERIF}" '
        f'font-style="italic" font-size="13" fill="{c["amber"]}">θ</text>'
        f'<text x="{x_start + len(trace) + 6}" y="{fmt(vy(-72) + 4)}" font-family="{SERIF}" '
        f'font-style="italic" font-size="13" fill="{c["muted"]}">V(t)</text>'
        f'<path d="{d}" fill="none" stroke="{c["green"]}" stroke-width="1.2" opacity=".16"/>'
        f'<path class="sweep" d="{d}" pathLength="1000" fill="none" stroke="{c["green"]}" stroke-width="1.6" '
        'stroke-linejoin="round"/>'
        f'<circle r="3.2" fill="{c["green"]}"><animateMotion dur="7s" repeatCount="indefinite" '
        f'path="{d}" keyPoints="0;1;1" keyTimes="0;.78;1" calcMode="linear"/>'
        '<animate attributeName="opacity" dur="7s" repeatCount="indefinite" values="1;1;0;0" '
        'keyTimes="0;.9;.97;1"/></circle>'
    )

    style = (
        ".sweep{stroke-dasharray:1000;animation:sweep 7s linear infinite}"
        "@keyframes sweep{0%{stroke-dashoffset:1000;opacity:1}78%{stroke-dashoffset:0;opacity:1}"
        "90%{opacity:1}97%,100%{stroke-dashoffset:0;opacity:0}}"
        ".caret{animation:blink 1.1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
        + REDUCED_MOTION
    )
    return document(
        w, h, "".join(out),
        title="Aris — software engineer who simulates brains",
        desc="Animated header: a small spiking network propagates activity cascades while the "
        "membrane potential of a simulated leaky integrate-and-fire neuron sweeps across the bottom.",
        style=style,
    )


# --------------------------------------------------------------------------- #
# Fig. 1 — Elegans: crawling nematode + closed sensorimotor loop
# --------------------------------------------------------------------------- #

def worm_frame(phase: float, length: float = 176.0, n: int = 44):
    """Centreline and outline of a nematode with a posteriorly travelling wave."""
    wavelength, amplitude, radius = length * 0.62, 10.5, 6.8
    k = 2 * math.pi / wavelength
    centre = []
    for i in range(n + 1):
        s = length * i / n
        u = s / length
        envelope = 0.75 + 0.35 * u
        centre.append((s, amplitude * envelope * math.sin(k * s + phase)))
    outline_l, outline_r = [], []
    for i, (x, y) in enumerate(centre):
        u = i / n
        if u > 0.9:
            r = radius * math.sqrt(max(0.0, 1 - ((u - 0.9) / 0.1) ** 2))
        else:
            r = radius * min(1.0, (u / 0.28)) ** 0.75
        x0, y0 = centre[max(0, i - 1)]
        x1, y1 = centre[min(n, i + 1)]
        dx, dy = x1 - x0, y1 - y0
        norm = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / norm, dx / norm
        outline_l.append((x + nx * r, y + ny * r))
        outline_r.append((x - nx * r, y - ny * r))
    return centre, outline_l + outline_r[::-1]


def elegans(theme: str) -> str:
    c = PALETTES[theme]
    w, h = 900, 380
    out: list[str] = []
    plate_c, plate_r = (222, 212), 128
    odor = (298, 146)

    out.append(
        "<defs>"
        f'<radialGradient id="agar" cx=".45" cy=".4"><stop offset="0" stop-color="{c["panel2"]}"/>'
        f'<stop offset="1" stop-color="{c["panel"]}"/></radialGradient>'
        f'<radialGradient id="odor"><stop offset="0" stop-color="{c["amber"]}" stop-opacity=".55"/>'
        f'<stop offset="1" stop-color="{c["amber"]}" stop-opacity="0"/></radialGradient>'
        f'<linearGradient id="body" x1="0" x2="1"><stop offset="0" stop-color="{c["cyan"]}" stop-opacity=".10"/>'
        f'<stop offset="1" stop-color="{c["cyan"]}" stop-opacity=".30"/></linearGradient>'
        f'<clipPath id="plate"><circle cx="{plate_c[0]}" cy="{plate_c[1]}" r="{plate_r}"/></clipPath>'
        f'<marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
        f'<path d="M0 1L8 5L0 9" fill="none" stroke="{c["muted"]}" stroke-width="1.6"/></marker>'
        "</defs>"
    )
    out.append(f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="{c["panel"]}" stroke="{c["border"]}"/>')

    # header
    out.append(
        f'<text x="30" y="46" font-family="{MONO}" font-size="21" font-weight="700" letter-spacing="5" '
        f'fill="{c["text"]}">ELEGANS</text>'
        f'<text x="170" y="45" font-family="{SANS}" font-size="15" fill="{c["muted"]}">'
        "connectome-constrained brain simulation</text>"
        f'<g font-family="{MONO}" font-size="10.5" letter-spacing="1.2">'
        f'<rect x="{w - 262}" y="27" width="232" height="24" rx="12" fill="none" stroke="{c["amber"]}"/>'
        f'<circle class="blink" cx="{w - 245}" cy="39" r="3.5" fill="{c["amber"]}"/>'
        f'<text x="{w - 233}" y="43" fill="{c["amber"]}">PRIVATE · ACTIVE RESEARCH</text></g>'
    )

    # agar plate with odorant gradient and iso-concentration contours
    cx, cy = plate_c
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{plate_r}" fill="url(#agar)" stroke="{c["border"]}" stroke-width="1.5"/>')
    rings = "".join(
        f'<circle cx="{odor[0]}" cy="{odor[1]}" r="{r}" fill="none" stroke="{c["amber"]}" '
        f'stroke-opacity="{0.34 - r / 520:.2f}" stroke-dasharray="2 5"/>'
        for r in (28, 58, 92, 130)
    )
    out.append(
        f'<g clip-path="url(#plate)"><circle class="breathe" cx="{odor[0]}" cy="{odor[1]}" r="82" fill="url(#odor)"/>'
        f"{rings}</g>"
        f'<circle cx="{odor[0]}" cy="{odor[1]}" r="3" fill="{c["amber"]}"/>'
        f'<text x="{odor[0] + 8}" y="{odor[1] - 8}" font-family="{MONO}" font-size="10" fill="{c["amber"]}">odorant</text>'
    )

    # the worm: 12 keyframes of a posteriorly travelling body wave
    angle = -32.0
    origin = (138, 262)
    frames = [worm_frame(2 * math.pi * f / 12) for f in range(12)] + [worm_frame(2 * math.pi)]
    body_values = ";".join(points_to_path(outline, closed=True) for _, outline in frames)
    gut_values = ";".join(points_to_path(centre[4:-3]) for centre, _ in frames)

    # faint track left in the agar: the same wave continued behind the tail
    track = []
    for i in range(0, 61):
        s = -150 + 150 * i / 60
        track.append((s, 10.5 * 0.75 * math.sin(2 * math.pi / (176 * 0.62) * s)))
    out.append(
        f'<g clip-path="url(#plate)"><g transform="translate({origin[0]} {origin[1]}) rotate({angle})">'
        f'<path d="{points_to_path(track)}" fill="none" stroke="{c["muted"]}" stroke-width="5" stroke-opacity=".12" '
        'stroke-linecap="round"/></g></g>'
    )

    worm = [f'<g transform="translate({origin[0]} {origin[1]}) rotate({angle})">']
    worm.append(
        f'<path d="{points_to_path(frames[0][1], closed=True)}" fill="url(#body)" stroke="{c["cyan"]}" '
        'stroke-width="1.3" stroke-linejoin="round">'
        f'<animate attributeName="d" dur="1.5s" repeatCount="indefinite" values="{body_values}"/></path>'
        f'<path d="{points_to_path(frames[0][0][4:-3])}" fill="none" stroke="{c["cyan"]}" stroke-opacity=".35" '
        'stroke-width="1.2" stroke-dasharray="1 3">'
        f'<animate attributeName="d" dur="1.5s" repeatCount="indefinite" values="{gut_values}"/></path>'
    )
    # neurons: nerve ring near the head + ventral cord motor neurons
    rng = Rng(3)
    idx_offsets = [(i, rng.uniform(-3.2, 3.2)) for i in (37, 37, 38, 38, 38, 39, 39, 36)]
    idx_offsets += [(i, 2.4) for i in range(8, 35, 3)]
    for k, (i, off) in enumerate(idx_offsets):
        xs = ";".join(fmt(centre[i][0]) for centre, _ in frames)
        ys = ";".join(fmt(centre[i][1] + off) for centre, _ in frames)
        colour = c["amber"] if k < 8 else c["violet"]
        delay = (1 - i / 44) * 1.5
        worm.append(
            f'<circle class="fire" style="animation-delay:-{delay:.2f}s" cx="{fmt(frames[0][0][i][0])}" '
            f'cy="{fmt(frames[0][0][i][1] + off)}" r="1.9" fill="{colour}">'
            f'<animate attributeName="cx" dur="1.5s" repeatCount="indefinite" values="{xs}"/>'
            f'<animate attributeName="cy" dur="1.5s" repeatCount="indefinite" values="{ys}"/></circle>'
        )
    worm.append("</g>")
    out.append("".join(worm))

    out.append(
        f'<text x="{cx}" y="{cy + plate_r + 24}" text-anchor="middle" font-family="{MONO}" font-size="11" '
        f'fill="{c["muted"]}">C. elegans · 302 neurons · chemotaxis prototype</text>'
    )

    # closed sensorimotor loop
    ex, ey, rx, ry = 668, 214, 150, 102
    loop_nodes = [
        (-90, "Connectome", "synapse-resolution wiring", c["blue"]),
        (-18, "Spiking dynamics", "integrate-and-fire neurons", c["cyan"]),
        (54, "Behaviour", "multi-species ecology", c["green"]),
        (126, "Neuromodulation", "reward · valence · arousal", c["amber"]),
        (198, "Plasticity", "STDP · eligibility traces", c["violet"]),
    ]
    ellipse = f"M{ex + rx} {ey}A{rx} {ry} 0 1 1 {ex - rx} {ey}A{rx} {ry} 0 1 1 {ex + rx} {ey}Z"
    out.append(f'<path d="{ellipse}" fill="none" stroke="{c["faint"]}" stroke-width="1.2" stroke-dasharray="4 5"/>')
    for k in range(4):
        out.append(
            f'<circle r="3" fill="{c["text"]}" opacity=".85"><animateMotion dur="9s" repeatCount="indefinite" '
            f'begin="-{k * 2.25}s" path="{ellipse}"/></circle>'
        )
    # chevrons mid-way between nodes show the direction of the loop
    for a0, *_ in loop_nodes:
        a = math.radians(a0 + 36)
        px, py = ex + rx * math.cos(a), ey + ry * math.sin(a)
        tx, ty = -rx * math.sin(a), ry * math.cos(a)
        ang = math.degrees(math.atan2(ty, tx))
        out.append(
            f'<path d="M-4 -4L2 0L-4 4" fill="none" stroke="{c["muted"]}" stroke-width="1.6" '
            f'transform="translate({fmt(px)} {fmt(py)}) rotate({fmt(ang)})"/>'
        )

    # Φ observer in the middle of the loop
    sx, sy = ex + rx * math.cos(math.radians(-18)), ey + ry * math.sin(math.radians(-18))
    out.append(
        f'<path d="M{ex + 26} {ey - 8}L{fmt(sx - 62)} {fmt(sy + 16)}" stroke="{c["pink"]}" stroke-width="1.2" '
        'stroke-dasharray="3 4" marker-end="url(#arrow)"/>'
        f'<circle class="breathe" cx="{ex}" cy="{ey}" r="30" fill="{c["pink"]}" fill-opacity=".08" stroke="{c["pink"]}"/>'
        f'<text x="{ex}" y="{ey + 10}" text-anchor="middle" font-family="{SERIF}" font-size="30" '
        f'font-style="italic" fill="{c["pink"]}">Φ</text>'
        f'<text x="{ex}" y="{ey + 48}" text-anchor="middle" font-family="{SANS}" font-size="11" fill="{c["muted"]}">'
        "integrated information</text>"
    )

    for a0, label, sub, colour in loop_nodes:
        a = math.radians(a0)
        nx, ny = ex + rx * math.cos(a), ey + ry * math.sin(a)
        bw, bh = 146, 44
        out.append(
            f'<g transform="translate({fmt(nx - bw / 2)} {fmt(ny - bh / 2)})">'
            f'<rect width="{bw}" height="{bh}" rx="10" fill="{c["panel2"]}" stroke="{colour}" stroke-width="1.3"/>'
            f'<text x="{bw / 2}" y="19" text-anchor="middle" font-family="{SANS}" font-size="13" '
            f'font-weight="600" fill="{c["text"]}">{esc(label)}</text>'
            f'<text x="{bw / 2}" y="34" text-anchor="middle" font-family="{SANS}" font-size="10.5" '
            f'fill="{c["muted"]}">{esc(sub)}</text></g>'
        )

    out.append(
        f'<text x="{ex}" y="{h - 22}" text-anchor="middle" font-family="{MONO}" font-size="11" fill="{c["muted"]}">'
        "D. melanogaster hemibrain · ~22.7k neurons · ~3.4M connections</text>"
    )

    style = (
        ".blink{animation:blink 1.6s ease-in-out infinite}@keyframes blink{50%{opacity:.15}}"
        ".breathe{animation:breathe 4s ease-in-out infinite;transform-box:fill-box;transform-origin:center}"
        "@keyframes breathe{50%{transform:scale(1.08);opacity:.75}}"
        ".fire{animation:fire 1.5s linear infinite}@keyframes fire{0%,100%{opacity:.35}12%{opacity:1}}"
        + REDUCED_MOTION
    )
    return document(
        w, h, "".join(out),
        title="Elegans — connectome-constrained brain simulation",
        desc="Left: an animated C. elegans nematode crawling up an odorant gradient on an agar plate. "
        "Right: the closed loop the project studies — connectome, spiking dynamics, behaviour, "
        "neuromodulation and plasticity — with integrated information (Φ) measured on the dynamics.",
        style=style,
    )


# --------------------------------------------------------------------------- #
# Fig. 3 — periodic table of research interests
# --------------------------------------------------------------------------- #

GROUPS = {
    "neuro": ("Neuroscience", "violet"),
    "complex": ("Complex systems", "cyan"),
    "lang": ("Language & AI", "amber"),
    "eng": ("Engineering", "blue"),
}

ELEMENTS = [
    # (row, col, symbol, name, group)
    (0, 0, "Cn", "Connectomics", "neuro"),
    (1, 0, "Sn", "Spiking Nets", "neuro"),
    (1, 1, "Pl", "Plasticity", "neuro"),
    (2, 0, "Nm", "Neuromodulation", "neuro"),
    (2, 1, "Φ", "Integrated Info", "neuro"),
    (2, 2, "Vi", "Insect Vision", "neuro"),
    (1, 4, "Ev", "Neuroevolution", "complex"),
    (1, 5, "Al", "Artificial Life", "complex"),
    (1, 6, "Ma", "Multi-Agent", "complex"),
    (2, 3, "Sy", "Stylometry", "lang"),
    (2, 4, "Lm", "LLM Memory", "lang"),
    (2, 5, "Ga", "Game AI", "lang"),
    (0, 7, "Sc", "Sci-Computing", "eng"),
    (1, 7, "Fs", "Full-Stack", "eng"),
    (2, 6, "Mo", "Mobile", "eng"),
    (2, 7, "Dx", "Dev Tooling", "eng"),
]


def interests(theme: str) -> str:
    c = PALETTES[theme]
    tw, th, gap, x0, y0 = 98, 86, 8, 30, 26
    w, h = 900, y0 + 3 * th + 2 * gap + 26
    out = [f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="{c["panel"]}" stroke="{c["border"]}"/>']

    out.append(
        f'<text x="{x0 + tw + gap + 14}" y="{y0 + 36}" font-family="{SERIF}" font-size="25" fill="{c["text"]}">'
        "Periodic Table of Interests</text>"
        f'<text x="{x0 + tw + gap + 15}" y="{y0 + 60}" font-family="{MONO}" font-size="11.5" fill="{c["muted"]}">'
        "ordered by curiosity, not by atomic number</text>"
    )
    lx, ly = x0 + 2 * (tw + gap) + 12, y0 + th + gap + 16
    for k, (label, colour) in enumerate(GROUPS.values()):
        yy = ly + k * 18
        out.append(
            f'<rect x="{lx}" y="{yy - 9}" width="10" height="10" rx="2" fill="{c[colour]}" fill-opacity=".25" '
            f'stroke="{c[colour]}"/><text x="{lx + 18}" y="{yy}" font-family="{SANS}" font-size="12" '
            f'fill="{c["muted"]}">{esc(label)}</text>'
        )

    for number, (row, col, symbol, name, group) in enumerate(ELEMENTS, start=1):
        colour = c[GROUPS[group][1]]
        x, y = x0 + col * (tw + gap), y0 + row * (th + gap)
        out.append(
            f'<g transform="translate({x} {y})">'
            f'<rect width="{tw}" height="{th}" rx="8" fill="{colour}" fill-opacity=".08" stroke="{colour}" '
            'stroke-opacity=".45"/>'
            f'<rect class="ex" style="animation-delay:{(number - 1) * 0.45:.2f}s" x="-1.5" y="-1.5" '
            f'width="{tw + 3}" height="{th + 3}" rx="9" fill="{colour}" fill-opacity=".10" stroke="{colour}" '
            'stroke-width="2"/>'
            f'<text x="8" y="16" font-family="{MONO}" font-size="10" fill="{c["muted"]}">{number}</text>'
            f'<text x="{tw / 2}" y="{th / 2 + 10}" text-anchor="middle" font-family="{SERIF}" font-size="30" '
            f'font-weight="700" fill="{colour}">{esc(symbol)}</text>'
            f'<text x="{tw / 2}" y="{th - 10}" text-anchor="middle" font-family="{SANS}" font-size="10.5" '
            f'fill="{c["text"]}">{esc(name)}</text></g>'
        )

    style = (
        ".ex{opacity:0;animation:ex 7.2s ease-in-out infinite}"
        "@keyframes ex{0%,14%,100%{opacity:0}5%{opacity:1}}" + REDUCED_MOTION
    )
    return document(
        w, h, "".join(out),
        title="Periodic table of research interests",
        desc="Sixteen interests laid out like the periodic table: neuroscience (connectomics, spiking "
        "networks, plasticity, neuromodulation, integrated information, insect vision), complex systems "
        "(neuroevolution, artificial life, multi-agent systems), language and AI (stylometry, LLM memory, "
        "game AI) and engineering (scientific computing, full-stack, mobile, developer tooling).",
        style=style,
    )


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    for theme in PALETTES:
        for name, render in (("hero", hero), ("elegans", elegans), ("interests", interests)):
            (ASSETS / f"{name}-{theme}.svg").write_text(render(theme), encoding="utf-8")
    print(f"wrote {len(PALETTES) * 3} figures to {ASSETS}")


if __name__ == "__main__":
    main()
