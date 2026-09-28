"""Render the data-driven figures that the profile README embeds.

    GITHUB_TOKEN=... python scripts/build_live.py --login sa-aris --out dist
    python scripts/build_live.py --demo --out /tmp/preview      # offline preview

Replaces the third-party stats/pin cards (github-readme-stats), whose public
deployment went offline, with figures rendered from the GitHub GraphQL API:

* activity-{theme}.svg  — the contribution calendar read as a spike train:
                          PSTH, raster, Fano factor, ISI variability, streaks
* spectrum-{theme}.svg  — language mix drawn as an emission spectrum, plus a
                          table of observables
* card-{repo}-{theme}.svg — project cards for the pinned repositories

Any API failure exits non-zero *before* files are written, so the workflow
never publishes a half-rendered set and the previous figures stay online.
"""

from __future__ import annotations

import argparse
import colorsys
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from svgkit import MONO, PALETTES, SANS, SERIF, Rng, document, esc, fmt, points_to_path, text_width, wrap

PINNED = ["aithena", "Context-Bridge", "idiolect", "cpp-rpg-inventory-system"]

QUERY = """
query($login: String!) {
  user(login: $login) {
    login
    followers { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes {
        name
        description
        stargazerCount
        forkCount
        primaryLanguage { name color }
        licenseInfo { spdxId }
        repositoryTopics(first: 6) { nodes { topic { name } } }
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount weekday } }
      }
    }
  }
}
"""

WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
REDUCED_MOTION = "@media (prefers-reduced-motion: reduce){*{animation:none!important}}"


# --------------------------------------------------------------------------- #
# data
# --------------------------------------------------------------------------- #

def fetch(login: str, token: str) -> dict:
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": f"{login}-profile-figures",
        },
    )
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.load(response)
            break
        except (urllib.error.URLError, TimeoutError) as error:
            status = getattr(error, "code", None)
            if attempt == 3 or (status is not None and status < 500):
                raise SystemExit(f"GitHub API request failed: {error}")
            time.sleep(2 ** (attempt + 1))
    if payload.get("errors") or not (payload.get("data") or {}).get("user"):
        raise SystemExit(f"GitHub API returned errors: {payload.get('errors')}")
    return payload["data"]["user"]


def demo_user(login: str) -> dict:
    """Synthetic, clearly fake data for offline previews of the layout."""
    rng = Rng(2026)
    today = datetime.now(timezone.utc).date()
    start = today - timedelta(days=today.weekday() + 1 + 52 * 7)
    weeks, day, rate = [], start, 1.0
    while day <= today:
        week = []
        for _ in range(7):
            if day > today:
                break
            rate = max(0.05, rate + rng.uniform(-0.35, 0.35))
            burst = rng.random() < 0.08
            count = 0 if rng.random() < 0.35 else int(rate * rng.uniform(0, 4) + (9 if burst else 0))
            week.append({"date": day.isoformat(), "contributionCount": count, "weekday": (day.weekday() + 1) % 7})
            day += timedelta(days=1)
        weeks.append({"contributionDays": week})
    langs = [("C++", "#f34b7d", 610_000), ("Python", "#3572A5", 420_000), ("TypeScript", "#3178c6", 120_000),
             ("CMake", "#DA3434", 24_000), ("Lua", "#000080", 18_000), ("Shell", "#89e051", 9_000),
             ("HTML", "#e34c26", 7_000)]
    repo = lambda name, desc, lang, stars, topics: {  # noqa: E731
        "name": name, "description": desc, "stargazerCount": stars, "forkCount": 0,
        "primaryLanguage": {"name": lang[0], "color": lang[1]}, "licenseInfo": {"spdxId": "MIT"},
        "repositoryTopics": {"nodes": [{"topic": {"name": t}} for t in topics]},
        "languages": {"edges": [{"size": s // 4, "node": {"name": n, "color": c}} for n, c, s in langs]},
    }
    total = sum(d["contributionCount"] for w in weeks for d in w["contributionDays"])
    return {
        "login": login,
        "followers": {"totalCount": 12},
        "repositories": {
            "totalCount": 4,
            "nodes": [
                repo("aithena", "Demo card — a long-ish description that wraps across two or three lines "
                     "to check the text layout of the card renderer.", langs[0], 3, ["npc", "game-ai", "cpp17"]),
                repo("Context-Bridge", "Demo card for Context-Bridge.", langs[1], 0, ["llm", "memory"]),
                repo("idiolect", "Demo card for idiolect.", langs[1], 0, ["nlp", "stylometry"]),
                repo("cpp-rpg-inventory-system", "Demo card for the inventory system.", langs[0], 0, []),
            ],
        },
        "contributionsCollection": {
            "totalCommitContributions": int(total * 0.7),
            "totalPullRequestContributions": 31,
            "totalIssueContributions": 9,
            "totalPullRequestReviewContributions": 4,
            "restrictedContributionsCount": 0,
            "contributionCalendar": {"totalContributions": total, "weeks": weeks},
        },
    }


# --------------------------------------------------------------------------- #
# spike-train statistics of the contribution calendar
# --------------------------------------------------------------------------- #

def spike_stats(days: list[tuple[date, int]]) -> dict:
    counts = [c for _, c in days]
    n = len(counts)
    mean = sum(counts) / n if n else 0.0
    var = sum((c - mean) ** 2 for c in counts) / (n - 1) if n > 1 else 0.0
    active = [i for i, c in enumerate(counts) if c > 0]
    isi = [b - a for a, b in zip(active, active[1:])]
    if len(isi) > 1:
        m = sum(isi) / len(isi)
        sd = math.sqrt(sum((x - m) ** 2 for x in isi) / (len(isi) - 1))
        cv = sd / m if m else None
    else:
        cv = None
    longest = run = 0
    for c in counts:
        run = run + 1 if c else 0
        longest = max(longest, run)
    current = 0
    tail = counts[:-1] if counts and counts[-1] == 0 else counts  # today may still be empty
    for c in reversed(tail):
        if not c:
            break
        current += 1
    by_weekday = [0] * 7
    for d, c in days:
        by_weekday[(d.weekday() + 1) % 7] += c
    return {
        "total": sum(counts),
        "rate": mean,
        "fano": var / mean if mean else None,
        "cv": cv,
        "longest": longest,
        "current": current,
        "peak_day": WEEKDAYS[by_weekday.index(max(by_weekday))] if any(by_weekday) else "—",
        "active_days": len(active),
    }


def fano_note(fano: float | None) -> str:
    if fano is None:
        return "no activity yet"
    if fano > 1.3:
        return "bursty · super-Poisson"
    if fano < 0.8:
        return "regular · sub-Poisson"
    return "≈ Poisson"


def panel(c: dict, w: int, h: int) -> str:
    return f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="{c["panel"]}" stroke="{c["border"]}"/>'


def panel_label(x: float, y: float, letter: str, caption: str, c: dict) -> str:
    return (
        f'<text x="{x}" y="{y}" font-family="{SANS}" font-size="14" font-weight="700" fill="{c["text"]}">{letter}</text>'
        f'<text x="{x + 16}" y="{y}" font-family="{MONO}" font-size="11" fill="{c["muted"]}">{esc(caption)}</text>'
    )


def activity(user: dict, theme: str) -> str:
    c = PALETTES[theme]
    w, h = 900, 300
    weeks = user["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = [
        (date.fromisoformat(d["date"]), d["contributionCount"], d["weekday"])
        for wk in weeks for d in wk["contributionDays"]
    ]
    stats = spike_stats([(d, n) for d, n, _ in days])

    x0, x1 = 62, 648
    n_weeks = max(len(weeks), 1)
    col = (x1 - x0) / n_weeks
    out = [panel(c, w, h), panel_label(24, 30, "a", "contributions as a spike train · last 12 months", c)]

    # PSTH: weekly totals + Gaussian-smoothed rate
    ps_top, ps_bot = 48, 104
    totals = [sum(d["contributionCount"] for d in wk["contributionDays"]) for wk in weeks]
    peak = max(totals + [1])
    bars = []
    for i, t in enumerate(totals):
        bh = (ps_bot - ps_top) * t / peak
        if bh > 0:
            bars.append(f'<rect x="{fmt(x0 + i * col + 1)}" y="{fmt(ps_bot - bh)}" width="{fmt(col - 2)}" height="{fmt(bh)}" rx="1"/>')
    out.append(f'<g fill="{c["blue"]}" fill-opacity=".35">{"".join(bars)}</g>')
    sigma = 1.6
    smooth = []
    for i in range(len(totals)):
        weights = [math.exp(-((i - j) ** 2) / (2 * sigma**2)) for j in range(len(totals))]
        smooth.append(sum(wt * t for wt, t in zip(weights, totals)) / sum(weights))
    if len(smooth) > 1:
        pts = [(x0 + (i + 0.5) * col, ps_bot - (ps_bot - ps_top) * s / peak) for i, s in enumerate(smooth)]
        out.append(f'<path d="{points_to_path(pts)}" fill="none" stroke="{c["pink"]}" stroke-width="1.8" stroke-linejoin="round"/>')
    out.append(
        f'<path d="M{x0} {ps_bot}H{x1}" stroke="{c["faint"]}"/>'
        f'<text x="{x0 - 8}" y="{ps_top + 8}" text-anchor="end" font-family="{MONO}" font-size="10" fill="{c["muted"]}">{peak}</text>'
        f'<text x="{x0 - 8}" y="{ps_bot}" text-anchor="end" font-family="{MONO}" font-size="10" fill="{c["muted"]}">0</text>'
        f'<text x="{x1}" y="{ps_top - 4}" text-anchor="end" font-family="{MONO}" font-size="10" fill="{c["pink"]}">'
        f"— smoothed rate (σ = {sigma} wk)</text>"
    )

    # raster: one row per weekday, one tick per contribution (capped per day)
    r_top, row = 120, 18
    out.append(
        "".join(
            f'<text x="{x0 - 8}" y="{r_top + k * row + 12}" text-anchor="end" font-family="{MONO}" font-size="10" '
            f'fill="{c["muted"]}">{WEEKDAYS[k]}</text>'
            for k in range(7)
        )
    )
    out.append(
        f'<rect x="{x0}" y="{r_top}" width="{x1 - x0}" height="{7 * row}" fill="{c["panel2"]}" '
        f'stroke="{c["grid"]}" rx="3"/>'
    )
    week_index = {}
    for i, wk in enumerate(weeks):
        for d in wk["contributionDays"]:
            week_index[d["date"]] = i
    ticks, sweep = [], 11.0
    for d, n, wd in days:
        if not n:
            continue
        rng = Rng(d.toordinal() * 7919)
        i = week_index[d.isoformat()]
        colour = c["amber"] if n >= 10 else c["cyan"]
        for _ in range(min(n, 5)):
            x = x0 + i * col + 1.5 + rng.random() * (col - 3)
            y = r_top + wd * row + 3
            delay = (x - x0) / (x1 - x0) * sweep
            ticks.append(
                f'<path class="sp" style="animation-delay:{delay:.2f}s" d="M{fmt(x)} {fmt(y)}v12" stroke="{colour}"/>'
            )
    out.append(f'<g stroke-width="1.4" stroke-linecap="round">{"".join(ticks)}</g>')

    # month ticks along the time axis
    months, seen = [], set()
    for i, wk in enumerate(weeks):
        first = date.fromisoformat(wk["contributionDays"][0]["date"])
        key = (first.year, first.month)
        if key in seen or i == 0:
            seen.add(key)
            continue
        seen.add(key)
        if first.day <= 7:
            months.append(
                f'<text x="{fmt(x0 + i * col)}" y="{r_top + 7 * row + 16}" font-family="{MONO}" font-size="10" '
                f'fill="{c["muted"]}">{MONTHS[first.month - 1]}</text>'
            )
    out.append("".join(months))

    # oscilloscope sweep across PSTH + raster
    out.append(
        f'<g class="cursor"><path d="M{x0} {ps_top - 6}V{r_top + 7 * row + 2}" stroke="{c["green"]}" '
        f'stroke-width="1.2" opacity=".75"/><circle cx="{x0}" cy="{ps_top - 6}" r="2.6" fill="{c["green"]}"/></g>'
    )

    # statistics panel
    sx, sy = 676, 30
    out.append(panel_label(sx, sy, "b", "spike-train statistics", c))
    rows = [
        ("N", "contributions · 365 d", f"{stats['total']:,}", ""),
        ("λ", "mean rate", f"{stats['rate']:.2f} d⁻¹", ""),
        ("F", "Fano factor σ²/μ", "—" if stats["fano"] is None else f"{stats['fano']:.2f}", fano_note(stats["fano"])),
        ("CV", "inter-spike interval", "—" if stats["cv"] is None else f"{stats['cv']:.2f}", "1 ≈ Poisson process"),
        ("L", "longest streak", f"{stats['longest']} d", ""),
        ("S", "current streak", f"{stats['current']} d", ""),
        ("θ", "peak weekday", stats["peak_day"], ""),
    ]
    for k, (sym, label, value, note) in enumerate(rows):
        y = sy + 34 + k * 34
        out.append(
            f'<text x="{sx}" y="{y}" font-family="{SERIF}" font-style="italic" font-size="16" fill="{c["amber"]}">{esc(sym)}</text>'
            f'<text x="{sx + 30}" y="{y - 1}" font-family="{SANS}" font-size="11.5" fill="{c["muted"]}">{esc(label)}</text>'
            f'<text x="{w - 24}" y="{y}" text-anchor="end" font-family="{MONO}" font-size="14" font-weight="700" '
            f'fill="{c["text"]}">{esc(value)}</text>'
            + (
                f'<text x="{sx + 30}" y="{y + 13}" font-family="{MONO}" font-size="9.5" fill="{c["faint"] if theme == "dark" else c["muted"]}">{esc(note)}</text>'
                if note else ""
            )
            + f'<path d="M{sx} {y + 19}H{w - 24}" stroke="{c["grid"]}"/>'
        )

    style = (
        f".sp{{opacity:.7;animation:sp {sweep}s linear infinite}}"
        "@keyframes sp{0%{opacity:1;stroke-width:2.6}6%{opacity:.7;stroke-width:1.4}100%{opacity:.7}}"
        f".cursor{{animation:cursor {sweep}s linear infinite}}"
        f"@keyframes cursor{{from{{transform:translateX(0)}}to{{transform:translateX({x1 - x0}px)}}}}"
        + REDUCED_MOTION
    )
    return document(
        w, h, "".join(out),
        title="Contribution activity as a spike train",
        desc=f"Weekly contribution histogram and a raster of daily contributions over the last year. "
        f"{stats['total']} contributions, mean rate {stats['rate']:.2f} per day, longest streak "
        f"{stats['longest']} days, current streak {stats['current']} days.",
        style=style,
    )


# --------------------------------------------------------------------------- #
# language emission spectrum + observables
# --------------------------------------------------------------------------- #

def wavelength_rgb(nm: float) -> str:
    """Approximate visible-spectrum colour (after Dan Bruton's classic mapping)."""
    if nm < 440:
        r, g, b = -(nm - 440) / 60, 0.0, 1.0
    elif nm < 490:
        r, g, b = 0.0, (nm - 440) / 50, 1.0
    elif nm < 510:
        r, g, b = 0.0, 1.0, -(nm - 510) / 20
    elif nm < 580:
        r, g, b = (nm - 510) / 70, 1.0, 0.0
    elif nm < 645:
        r, g, b = 1.0, -(nm - 645) / 65, 0.0
    else:
        r, g, b = 1.0, 0.0, 0.0
    fall = 0.3 + 0.7 * (nm - 380) / 40 if nm < 420 else 0.3 + 0.7 * (720 - nm) / 70 if nm > 650 else 1.0
    return "#" + "".join(f"{int(255 * (max(0.0, v) * fall) ** 0.8):02x}" for v in (r, g, b))


def colour_to_nm(hex_colour: str | None) -> float:
    """Place a language on the spectrum at the wavelength matching its hue."""
    if not hex_colour:
        return 555.0
    rgb = [int(hex_colour.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    hue, _, sat = colorsys.rgb_to_hls(*rgb)
    if sat < 0.12:
        return 555.0
    h = hue * 360
    if h > 290:  # magentas are extra-spectral: park them past the red end
        h -= 360
    return max(388.0, min(712.0, 700 - h * (300 / 270)))


def languages(user: dict, exclude: str) -> list[tuple[str, str, float]]:
    sizes: dict[str, int] = {}
    colours: dict[str, str] = {}
    for repo in user["repositories"]["nodes"]:
        if repo["name"].lower() == exclude.lower():
            continue
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            sizes[name] = sizes.get(name, 0) + edge["size"]
            colours[name] = edge["node"]["color"] or "#8b949e"
    total = sum(sizes.values()) or 1
    ranked = sorted(sizes.items(), key=lambda kv: -kv[1])
    return [(name, colours[name], size / total) for name, size in ranked[:8]]


def spectrum(user: dict, theme: str) -> str:
    c = PALETTES[theme]
    w, h = 900, 270
    out = [panel(c, w, h), panel_label(24, 30, "a", "language emission spectrum · public repositories", c)]
    langs = languages(user, exclude=user["login"])

    sx0, sx1, st, sb = 40, 574, 92, 188
    nm0, nm1 = 380, 720

    def x_of(nm: float) -> float:
        return sx0 + (nm - nm0) / (nm1 - nm0) * (sx1 - sx0)

    stops = "".join(
        f'<stop offset="{(nm - nm0) / (nm1 - nm0):.3f}" stop-color="{wavelength_rgb(nm)}"/>' for nm in range(nm0, nm1 + 1, 10)
    )
    out.append(
        f'<defs><linearGradient id="vis">{stops}</linearGradient>'
        '<filter id="bloom" x="-50%" y="-10%" width="200%" height="120%"><feGaussianBlur stdDeviation="2.4"/></filter></defs>'
        f'<rect x="{sx0}" y="{st}" width="{sx1 - sx0}" height="{sb - st}" rx="4" fill="#05070b"/>'
        f'<rect x="{sx0}" y="{st}" width="{sx1 - sx0}" height="{sb - st}" rx="4" fill="url(#vis)" opacity=".13"/>'
    )

    # lines, with labels staggered on up to three levels to avoid collisions
    placed: list[tuple[float, float, int]] = []
    lines, labels = [], []
    positions = []
    for name, colour, share in langs:
        x = x_of(colour_to_nm(colour))
        while any(abs(x - px) < 5 for px in positions):
            x += 5
        positions.append(x)
        height = (sb - st - 6) * max(0.28, share ** 0.55)
        lines.append((x, height, colour, name, share))
    for k, (x, height, colour, name, share) in enumerate(sorted(lines, key=lambda l: -l[4])):
        top = sb - height
        delay = k * 0.7
        out.append(
            f'<g class="line" style="animation-delay:-{delay:.1f}s">'
            f'<path d="M{fmt(x)} {fmt(top)}V{sb}" stroke="{colour}" stroke-width="7" opacity=".55" filter="url(#bloom)"/>'
            f'<path d="M{fmt(x)} {fmt(top)}V{sb}" stroke="{colour}" stroke-width="2.2"/>'
            f'<path d="M{fmt(x)} {fmt(top)}V{sb}" stroke="#ffffff" stroke-width=".6" opacity=".6"/></g>'
        )
        label = f"{name} {share * 100:.1f}%"
        lw = text_width(label, 10.5) + 6
        level = 0
        while any(lvl == level and abs(x - px) < (lw + pw) / 2 for px, pw, lvl in placed) and level < 3:
            level += 1
        placed.append((x, lw, level))
        ly = st - 8 - level * 14
        anchor = "middle"
        if x - lw / 2 < sx0:
            anchor = "start"
        elif x + lw / 2 > sx1:
            anchor = "end"
        labels.append(
            f'<path d="M{fmt(x)} {ly + 3}V{st}" stroke="{colour}" stroke-width=".8" stroke-dasharray="1 2" opacity=".7"/>'
            f'<text x="{fmt(x)}" y="{ly}" text-anchor="{anchor}" font-family="{SANS}" font-size="10.5" fill="{c["text"]}">'
            f'{esc(name)} <tspan fill="{c["muted"]}">{share * 100:.1f}%</tspan></text>'
        )
    out.extend(labels)
    if not langs:
        out.append(
            f'<text x="{(sx0 + sx1) / 2}" y="{(st + sb) / 2}" text-anchor="middle" font-family="{MONO}" '
            f'font-size="12" fill="{c["muted"]}">no public code yet</text>'
        )

    axis = [f'<path d="M{sx0} {sb + 6}H{sx1}" stroke="{c["faint"]}"/>']
    for nm in range(400, 701, 50):
        x = x_of(nm)
        axis.append(
            f'<path d="M{fmt(x)} {sb + 6}v5" stroke="{c["faint"]}"/>'
            f'<text x="{fmt(x)}" y="{sb + 24}" text-anchor="middle" font-family="{MONO}" font-size="10" '
            f'fill="{c["muted"]}">{nm}</text>'
        )
    axis.append(
        f'<text x="{sx1}" y="{sb + 44}" text-anchor="end" font-family="{MONO}" font-size="10" fill="{c["muted"]}">'
        "λ / nm — each language sits at the wavelength of its GitHub colour</text>"
    )
    out.extend(axis)

    # observables table
    cc = user["contributionsCollection"]
    repos = user["repositories"]["nodes"]
    rows = [
        ("N", "repo", "public repositories", user["repositories"]["totalCount"]),
        ("N", "★", "stars earned", sum(r["stargazerCount"] for r in repos)),
        ("N", "f", "followers", user["followers"]["totalCount"]),
        ("N", "c", "commits · 1 y", cc["totalCommitContributions"]),
        ("N", "pr", "pull requests · 1 y", cc["totalPullRequestContributions"]),
        ("N", "i", "issues · 1 y", cc["totalIssueContributions"]),
        ("N", "rev", "code reviews · 1 y", cc["totalPullRequestReviewContributions"]),
    ]
    tx = 606
    out.append(panel_label(tx, 30, "b", "observables", c))
    for k, (sym, sub, label, value) in enumerate(rows):
        y = 62 + k * 26
        out.append(
            f'<text x="{tx}" y="{y}" font-family="{SERIF}" font-style="italic" font-size="15" fill="{c["amber"]}">'
            f'{sym}<tspan font-size="10" dy="3">{esc(sub)}</tspan></text>'
            f'<text x="{tx + 44}" y="{y - 1}" font-family="{SANS}" font-size="11.5" fill="{c["muted"]}">{esc(label)}</text>'
            f'<text x="{w - 24}" y="{y}" text-anchor="end" font-family="{MONO}" font-size="14" font-weight="700" '
            f'fill="{c["text"]}">{value:,}</text>'
            f'<path d="M{tx} {y + 9}H{w - 24}" stroke="{c["grid"]}"/>'
        )
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    out.append(
        f'<text x="{w - 24}" y="{h - 18}" text-anchor="end" font-family="{MONO}" font-size="9.5" fill="{c["muted"]}">'
        f"measured {stamp}</text>"
    )

    style = (
        ".line{animation:flicker 5s ease-in-out infinite}"
        "@keyframes flicker{0%,100%{opacity:1}50%{opacity:.72}}" + REDUCED_MOTION
    )
    summary = ", ".join(f"{n} {s * 100:.1f}%" for n, _, s in langs) or "none"
    return document(
        w, h, "".join(out),
        title="Language spectrum and observables",
        desc=f"Language mix across public repositories drawn as spectral lines: {summary}.",
        style=style,
    )


# --------------------------------------------------------------------------- #
# project cards
# --------------------------------------------------------------------------- #

def card(repo: dict | None, name: str, index: int, theme: str) -> str:
    c = PALETTES[theme]
    w, h = 440, 176
    out = [panel(c, w, h)]
    out.append(
        f'<g transform="translate(22 20)" fill="none" stroke="{c["muted"]}" stroke-width="1.3">'
        '<rect x=".5" y=".5" width="12" height="15" rx="2"/><path d="M3.5 .5v15M6.5 5h3.5M6.5 8h3.5"/></g>'
        f'<text x="44" y="34" font-family="{SANS}" font-size="16" font-weight="700" fill="{c["blue"]}">{esc(name)}</text>'
        f'<text x="{w - 20}" y="33" text-anchor="end" font-family="{MONO}" font-size="12" fill="{c["muted"]}">[{index}]</text>'
    )
    if repo is None:
        out.append(
            f'<text x="22" y="66" font-family="{SANS}" font-size="12.5" fill="{c["muted"]}">'
            "Repository details are unavailable right now.</text>"
        )
        return document(w, h, "".join(out), title=name, desc="Project card")

    description = repo.get("description") or "No description yet."
    for k, line in enumerate(wrap(description, 12.5, w - 44, 3)):
        out.append(
            f'<text x="22" y="{62 + k * 18}" font-family="{SANS}" font-size="12.5" fill="{c["text"]}" '
            f'fill-opacity=".86">{esc(line)}</text>'
        )

    tx = 22
    for node in repo["repositoryTopics"]["nodes"][:4]:
        topic = node["topic"]["name"]
        tw = text_width(topic, 10.5, mono=True) + 16
        if tx + tw > w - 22:
            break
        out.append(
            f'<rect x="{fmt(tx)}" y="{h - 60}" width="{fmt(tw)}" height="19" rx="9.5" fill="{c["blue"]}" '
            f'fill-opacity=".10"/><text x="{fmt(tx + tw / 2)}" y="{h - 46.5}" text-anchor="middle" '
            f'font-family="{MONO}" font-size="10.5" fill="{c["blue"]}">{esc(topic)}</text>'
        )
        tx += tw + 6

    meta, mx = [], 22
    language = repo.get("primaryLanguage")
    if language:
        meta.append(
            f'<circle cx="{mx + 6}" cy="{h - 22}" r="6" fill="{language["color"] or c["muted"]}"/>'
            f'<text x="{mx + 18}" y="{h - 18}" font-family="{SANS}" font-size="12" fill="{c["muted"]}">{esc(language["name"])}</text>'
        )
        mx += 30 + text_width(language["name"], 12)
    for glyph, value in (("★", repo["stargazerCount"]), ("⑂", repo["forkCount"])):
        meta.append(
            f'<text x="{fmt(mx)}" y="{h - 18}" font-family="{SANS}" font-size="12" fill="{c["muted"]}">{glyph} {value}</text>'
        )
        mx += 22 + text_width(f"{glyph} {value}", 12)
    licence = (repo.get("licenseInfo") or {}).get("spdxId")
    if licence and licence != "NOASSERTION":
        meta.append(
            f'<text x="{fmt(mx)}" y="{h - 18}" font-family="{MONO}" font-size="11" fill="{c["muted"]}">{esc(licence)}</text>'
        )
    out.extend(meta)
    return document(w, h, "".join(out), title=name, desc=description)


# --------------------------------------------------------------------------- #

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--login", default=os.environ.get("GITHUB_REPOSITORY_OWNER", "sa-aris"))
    parser.add_argument("--out", type=Path, default=Path("dist"))
    parser.add_argument("--demo", action="store_true", help="render synthetic data without calling the API")
    args = parser.parse_args()

    if args.demo:
        user = demo_user(args.login)
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            sys.exit("GITHUB_TOKEN is required (or pass --demo)")
        user = fetch(args.login, token)

    by_name = {r["name"].lower(): r for r in user["repositories"]["nodes"]}
    figures: dict[str, str] = {}
    for theme in PALETTES:
        figures[f"activity-{theme}.svg"] = activity(user, theme)
        figures[f"spectrum-{theme}.svg"] = spectrum(user, theme)
        for index, name in enumerate(PINNED, start=1):
            figures[f"card-{name.lower()}-{theme}.svg"] = card(by_name.get(name.lower()), name, index, theme)

    args.out.mkdir(parents=True, exist_ok=True)
    for filename, svg in figures.items():
        (args.out / filename).write_text(svg, encoding="utf-8")
    print(f"wrote {len(figures)} figures to {args.out}")


if __name__ == "__main__":
    main()
