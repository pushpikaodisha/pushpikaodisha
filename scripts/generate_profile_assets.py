"""Generate animated, theme-adaptive (Dark/Light, Desktop/Mobile) SVG assets for pushpikaodisha."""

from __future__ import annotations

import html
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone

USERNAME = os.getenv("GITHUB_REPOSITORY_OWNER", "pushpikaodisha")
TOKEN = os.getenv("GITHUB_TOKEN", "")
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

SANS_FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
MONO_FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

THEMES = {
    "dark": {
        "bg_start": "#07101D",
        "bg_end": "#0F1D32",
        "border": "#263B54",
        "surface": "#0B1525",
        "surface_bar": "#16253B",
        "surface_tab": "#132942",
        "glass_start": "#1D334D",
        "glass_end": "#102033",
        "glass_border": "#46698C",
        "text": "#F0F6FC",
        "subtext": "#C9D8E8",
        "muted": "#839BB5",
        "code_num": "#4B6584",
        "accent": "#38BDF8",
        "accent_2": "#818CF8",
        "accent_3": "#34D399",
        "kw": "#C084FC",
        "fn": "#60A5FA",
        "str": "#34D399",
        "wire": "#2D4F6C",
        "glow": "#0EA5E9",
        "dots": "#7DA2C8",
        "shadow_color": "#01060D",
        "bar_bg": "#1B2B40",
    },
    "light": {
        "bg_start": "#F8FAFC",
        "bg_end": "#EFF6FF",
        "border": "#CBD5E1",
        "surface": "#FFFFFF",
        "surface_bar": "#F1F5F9",
        "surface_tab": "#E0F2FE",
        "glass_start": "#FFFFFF",
        "glass_end": "#F1F5F9",
        "glass_border": "#94A3B8",
        "text": "#0F172A",
        "subtext": "#334155",
        "muted": "#64748B",
        "code_num": "#94A3B8",
        "accent": "#0284C7",
        "accent_2": "#4F46E5",
        "accent_3": "#059669",
        "kw": "#7C3AED",
        "fn": "#2563EB",
        "str": "#059669",
        "wire": "#94A3B8",
        "glow": "#38BDF8",
        "dots": "#64748B",
        "shadow_color": "#0F172A",
        "bar_bg": "#E2E8F0",
    },
}

LANG_COLORS = {
    "JavaScript": "#F1E05A",
    "TypeScript": "#3178C6",
    "PHP": "#4F5D95",
    "HTML": "#E34C26",
    "CSS": "#563D7C",
    "Python": "#3572A5",
    "SQL": "#E38C00",
    "Shell": "#89E051",
}


def gh_get(url: str) -> dict | list:
    """Perform a GitHub REST API GET request."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "pushpikaodisha-profile-builder",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_github_metrics() -> dict:
    """Fetch public profile, repository, star, and byte-weighted language stats."""
    user = gh_get(f"https://api.github.com/users/{USERNAME}")
    repos = gh_get(f"https://api.github.com/users/{USERNAME}/repos?per_page=100&type=owner")

    non_forks = [
        r for r in repos if not r.get("fork") and r.get("name", "").lower() != USERNAME.lower()
    ]
    stars = sum(int(r.get("stargazers_count", 0)) for r in repos)

    lang_bytes: dict[str, int] = {}
    for repo in non_forks:
        lang_url = repo.get("languages_url")
        if not lang_url:
            continue
        try:
            data = gh_get(lang_url)
            if isinstance(data, dict):
                for lang, byte_count in data.items():
                    lang_bytes[lang] = lang_bytes.get(lang, 0) + int(byte_count)
        except (urllib.error.URLError, TimeoutError):
            lang = repo.get("language")
            if lang:
                lang_bytes[lang] = lang_bytes.get(lang, 0) + 1

    if not lang_bytes:
        for repo in non_forks:
            lang = repo.get("language")
            if lang:
                lang_bytes[lang] = lang_bytes.get(lang, 0) + 1

    sorted_langs = sorted(lang_bytes.items(), key=lambda item: item[1], reverse=True)
    total_bytes = max(sum(v for _, v in sorted_langs), 1)
    top_langs = [
        (lang, round((val / total_bytes) * 100, 1))
        for lang, val in sorted_langs
        if round((val / total_bytes) * 100, 1) >= 0.1
    ][:5]

    top_repos = sorted(non_forks, key=lambda r: int(r.get("size", 0)), reverse=True)[:5]
    repo_sizes = [
        (r.get("name", "repo"), max(int(r.get("size", 1)), 1)) for r in top_repos
    ]

    return {
        "public_repos": int(user.get("public_repos", len(repos))),
        "lang_count": len(top_langs),
        "stars": stars,
        "followers": int(user.get("followers", 0)),
        "top_langs": top_langs,
        "repo_sizes": repo_sizes,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


def ide_scene(t: dict, tx: int, ty: int, scale: float = 1.0) -> str:
    """Render the animated IDE window + floating telemetry card + terminal toast."""
    c_wire = t["wire"]
    c_accent = t["accent"]
    c_accent_3 = t["accent_3"]
    c_surface = t["surface"]
    c_surface_bar = t["surface_bar"]
    c_surface_tab = t["surface_tab"]
    c_border = t["border"]
    c_glass_border = t["glass_border"]
    c_text = t["text"]
    c_muted = t["muted"]
    c_code_num = t["code_num"]
    c_kw = t["kw"]
    c_fn = t["fn"]
    c_str = t["str"]
    c_bar_bg = t["bar_bg"]

    return f"""  <g transform="translate({tx}, {ty}) scale({scale})">
    <!-- Signal Wire Connecting Telemetry to Terminal -->
    <g fill="none" stroke="{c_wire}" stroke-width="1.5">
      <path d="M 318 195 v 46 q 0 18 -18 18 h -38"/>
      <path class="flow" d="M 318 195 v 46 q 0 18 -18 18 h -38" stroke="{c_accent}"/>
    </g>

    <!-- Main IDE Window -->
    <g filter="url(#shadow)">
      <rect x="0" y="6" width="356" height="218" rx="13" fill="{c_surface}" stroke="{c_glass_border}" stroke-width="1.2"/>
      <path d="M 13 6 h 330 q 13 0 13 13 v 22 H 0 V 19 Q 0 6 13 6 Z" fill="{c_surface_bar}"/>
      <circle cx="18" cy="24" r="3.8" fill="#F87171"/>
      <circle cx="31" cy="24" r="3.8" fill="#FBBF24"/>
      <circle cx="44" cy="24" r="3.8" fill="#34D399"/>
      <text x="184" y="28" text-anchor="middle" fill="{c_muted}" font-family="{MONO_FONT}" font-size="10">workspace / core.mjs</text>
      <path d="M 0 41 H 356 M 56 41 V 224" stroke="{c_border}"/>

      <!-- Sidebar Tree Lines -->
      <g fill="{c_muted}" opacity="0.45">
        <rect x="14" y="60" width="26" height="4" rx="2"/>
        <rect x="20" y="76" width="22" height="4" rx="2"/>
        <rect x="20" y="92" width="17" height="4" rx="2"/>
        <rect x="20" y="108" width="24" height="4" rx="2"/>
        <rect x="14" y="136" width="26" height="4" rx="2"/>
        <rect x="20" y="152" width="19" height="4" rx="2"/>
      </g>

      <!-- Active Tab & Inactive Tab -->
      <rect x="56" y="41" width="98" height="28" fill="{c_surface_tab}"/>
      <rect x="56" y="41" width="98" height="2" fill="{c_accent}"/>
      <text x="69" y="59" fill="{c_accent}" font-family="{MONO_FONT}" font-size="10" font-weight="700">JS</text>
      <text x="89" y="59" fill="{c_text}" font-family="{MONO_FONT}" font-size="10">core.mjs</text>
      <text x="170" y="59" fill="{c_muted}" font-family="{MONO_FONT}" font-size="10">merkle.php</text>
      <circle cx="338" cy="55" r="3" fill="{c_accent_3}" class="status"/>

      <!-- Line Numbers -->
      <g font-family="{MONO_FONT}" font-size="10" fill="{c_code_num}">
        <text x="65" y="100">1</text>
        <text x="65" y="123">2</text>
        <text x="65" y="146">3</text>
        <text x="65" y="169">4</text>
        <text x="65" y="192">5</text>
      </g>

      <!-- Animated Typing Code -->
      <g font-family="{MONO_FONT}" font-size="11.2" fill="{c_text}">
        <text x="82" y="100" clip-path="url(#line1)"><tspan fill="{c_kw}">async function</tspan> <tspan fill="{c_fn}">boot</tspan>() {{</text>
        <text x="82" y="123" clip-path="url(#line2)">  <tspan fill="{c_kw}">const</tspan> sys = <tspan fill="{c_fn}">createVault</tspan>();</text>
        <text x="82" y="146" clip-path="url(#line3)">  <tspan fill="{c_kw}">await</tspan> sys.<tspan fill="{c_str}">verifyMerkle</tspan>();</text>
        <text x="82" y="169" clip-path="url(#line4)">  <tspan fill="{c_kw}">return</tspan> sys.<tspan fill="{c_str}">stream</tspan>();</text>
        <text x="82" y="192">}}</text>
      </g>
    </g>

    <!-- Floating Telemetry Glass Card -->
    <g class="preview">
      <g filter="url(#shadow)">
        <rect x="254" y="118" width="126" height="118" rx="12" fill="url(#glass)" stroke="{c_glass_border}" stroke-width="1.2"/>
        <path d="M 254 145 H 380" stroke="{c_border}"/>
        <circle cx="268" cy="132" r="3.2" fill="{c_accent_3}"/>
        <text x="278" y="136" fill="{c_text}" font-family="{SANS_FONT}" font-size="9" font-weight="600" letter-spacing="0.9">TELEMETRY</text>
        <rect x="267" y="156" width="52" height="5" rx="2.5" fill="{c_muted}" opacity="0.65"/>
        <rect x="267" y="167" width="34" height="3.5" rx="1.75" fill="{c_muted}" opacity="0.38"/>
        <g class="bars">
          <rect x="269" y="196" width="14" height="22" rx="3" fill="{c_accent}"/>
          <rect x="291" y="185" width="14" height="33" rx="3" fill="url(#accent)"/>
          <rect x="313" y="190" width="14" height="28" rx="3" fill="{c_accent_3}"/>
          <rect x="335" y="177" width="14" height="41" rx="3" fill="url(#accent)"/>
        </g>
      </g>
    </g>

    <!-- Floating Terminal Test Toast -->
    <g filter="url(#shadow)">
      <rect x="26" y="210" width="236" height="68" rx="11" fill="{c_surface}" stroke="{c_glass_border}" stroke-width="1.2"/>
      <text x="41" y="232" font-family="{MONO_FONT}" font-size="10.5" fill="{c_text}"><tspan fill="{c_accent}">$</tspan> node --test core.mjs</text>
      <rect x="41" y="242" width="206" height="4" rx="2" fill="{c_bar_bg}"/>
      <rect class="progress" x="41" y="242" width="206" height="4" rx="2" fill="url(#accent)"/>
      <text class="building" x="41" y="264" font-family="{MONO_FONT}" font-size="10" fill="{c_muted}">running zero-dep checks...</text>
      <text class="success" x="41" y="264" font-family="{MONO_FONT}" font-size="10" fill="{c_accent_3}">✓ zero-dep · all checks passed</text>
    </g>
  </g>"""


def render_hero(t: dict, mobile: bool = False) -> str:
    """Render desktop or mobile animated hero SVG."""
    w, h = (540, 560) if mobile else (960, 330)
    c_bg1 = t["bg_start"]
    c_bg2 = t["bg_end"]
    c_border = t["border"]
    c_accent = t["accent"]
    c_accent_2 = t["accent_2"]
    c_accent_3 = t["accent_3"]
    c_text = t["text"]
    c_subtext = t["subtext"]
    c_muted = t["muted"]
    c_glow = t["glow"]
    c_dots = t["dots"]
    c_shadow = t["shadow_color"]

    shared_defs = f"""  <defs>
    <linearGradient id="background" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{c_bg1}"/>
      <stop offset="100%" stop-color="{c_bg2}"/>
    </linearGradient>
    <linearGradient id="accent" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{c_accent_3}"/>
      <stop offset="55%" stop-color="{c_accent}"/>
      <stop offset="100%" stop-color="{c_accent_2}"/>
    </linearGradient>
    <linearGradient id="glass" x1="0%" y1="0%" x2="80%" y2="100%">
      <stop offset="0%" stop-color="{t['glass_start']}"/>
      <stop offset="100%" stop-color="{t['glass_end']}"/>
    </linearGradient>
    <radialGradient id="glow">
      <stop offset="0%" stop-color="{c_glow}" stop-opacity="0.22"/>
      <stop offset="100%" stop-color="{c_glow}" stop-opacity="0"/>
    </radialGradient>
    <pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse">
      <circle cx="1.5" cy="1.5" r="0.9" fill="{c_dots}" opacity="0.18"/>
    </pattern>
    <filter id="shadow" x="-25%" y="-30%" width="160%" height="180%">
      <feDropShadow dx="0" dy="10" stdDeviation="11" flood-color="{c_shadow}" flood-opacity="0.42"/>
    </filter>
    <clipPath id="line1"><rect class="reveal line1" x="80" y="86" width="250" height="18"/></clipPath>
    <clipPath id="line2"><rect class="reveal line2" x="80" y="109" width="250" height="18"/></clipPath>
    <clipPath id="line3"><rect class="reveal line3" x="80" y="132" width="250" height="18"/></clipPath>
    <clipPath id="line4"><rect class="reveal line4" x="80" y="155" width="250" height="18"/></clipPath>
  </defs>
  <style>
    .reveal{{animation-duration:12s;animation-iteration-count:infinite;animation-timing-function:steps(26,end)}}
    .line1{{animation-name:type1}}.line2{{animation-name:type2}}.line3{{animation-name:type3}}.line4{{animation-name:type4}}
    @keyframes type1{{0%,3%{{width:0}}18%,94%{{width:250px}}100%{{width:0}}}}
    @keyframes type2{{0%,15%{{width:0}}30%,94%{{width:250px}}100%{{width:0}}}}
    @keyframes type3{{0%,27%{{width:0}}42%,94%{{width:250px}}100%{{width:0}}}}
    @keyframes type4{{0%,39%{{width:0}}54%,94%{{width:250px}}100%{{width:0}}}}
    .progress{{animation:build 12s ease-in-out infinite}}
    @keyframes build{{0%,42%{{width:0}}68%,94%{{width:206px}}100%{{width:0}}}}
    .success{{animation:success 12s ease-in-out infinite}}
    @keyframes success{{0%,62%{{opacity:0;transform:translateY(4px)}}70%,94%{{opacity:1;transform:translateY(0)}}100%{{opacity:0}}}}
    .building{{opacity:0;animation:building 12s ease-in-out infinite}}
    @keyframes building{{0%,5%{{opacity:0}}10%,58%{{opacity:1}}65%,100%{{opacity:0}}}}
    .preview{{animation:float 6s ease-in-out infinite}}
    @keyframes float{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-5px)}}}}
    .bars{{animation:bars 12s ease-in-out infinite;transform-origin:308px 218px}}
    @keyframes bars{{0%,48%{{transform:scaleY(.2);opacity:.4}}70%,94%{{transform:scaleY(1);opacity:1}}100%{{transform:scaleY(.2);opacity:.4}}}}
    .flow{{stroke-dasharray:5 11;animation:flow 2s linear infinite}}
    @keyframes flow{{to{{stroke-dashoffset:-32}}}}
    .status{{animation:pulse 2.8s ease-in-out infinite}}
    @keyframes pulse{{50%{{opacity:.4}}}}
    @media(prefers-reduced-motion:reduce){{.reveal,.progress,.success,.building,.preview,.bars,.flow,.status{{animation:none}}.building{{opacity:0}}}}
  </style>"""

    if mobile:
        body = f"""  <circle cx="420" cy="120" r="240" fill="url(#glow)"/>
  <rect x="32" y="34" width="26" height="3.5" rx="1.75" fill="url(#accent)"/>
  <text x="66" y="39" font-family="{MONO_FONT}" font-size="10.5" letter-spacing="1.2" fill="{c_muted}">SYSTEMS &amp; FULL-STACK ENGINEER</text>
  <text x="32" y="88" font-family="{SANS_FONT}" font-size="38" font-weight="800" letter-spacing="-1" fill="{c_text}">Pushpika</text>
  <text x="32" y="130" font-family="{SANS_FONT}" font-size="38" font-weight="800" letter-spacing="-1" fill="url(#accent)">Odisha</text>
  <text x="32" y="166" font-family="{SANS_FONT}" font-size="16" font-weight="500" fill="{c_subtext}">Zero-dependency engines. Resilient systems.</text>
  <text x="32" y="194" font-family="{MONO_FONT}" font-size="10.5" letter-spacing="1" fill="{c_muted}">NODE.JS  /  PHP 8  /  CRYPTO  /  CANVAS</text>
{ide_scene(t, 76, 218, 0.96)}
  <line x1="32" y1="510" x2="508" y2="510" stroke="{c_border}" stroke-width="1"/>
  <circle cx="38" cy="534" r="3.5" fill="{c_accent_3}" class="status"/>
  <text x="50" y="538" font-family="{MONO_FONT}" font-size="10" letter-spacing="0.8" fill="{c_muted}">OPEN TO ENGINEERING ROLES</text>
  <text x="508" y="538" text-anchor="end" font-family="{MONO_FONT}" font-size="10" fill="{c_muted}">SRI LANKA · @{html.escape(USERNAME.upper())}</text>"""
    else:
        body = f"""  <circle cx="710" cy="160" r="270" fill="url(#glow)"/>
  <rect x="48" y="42" width="28" height="3.5" rx="1.75" fill="url(#accent)"/>
  <text x="86" y="47" font-family="{MONO_FONT}" font-size="11.5" letter-spacing="1.4" fill="{c_muted}">SYSTEMS &amp; FULL-STACK ENGINEER</text>
  <text x="48" y="102" font-family="{SANS_FONT}" font-size="44" font-weight="800" letter-spacing="-1.2" fill="{c_text}">Pushpika</text>
  <text x="48" y="148" font-family="{SANS_FONT}" font-size="44" font-weight="800" letter-spacing="-1.2" fill="url(#accent)">Odisha</text>
  <text x="48" y="186" font-family="{SANS_FONT}" font-size="16" font-weight="500" fill="{c_subtext}">Zero-dependency engines.</text>
  <text x="48" y="210" font-family="{SANS_FONT}" font-size="16" font-weight="500" fill="{c_subtext}">Resilient full-stack systems.</text>
  <text x="48" y="246" font-family="{MONO_FONT}" font-size="11" letter-spacing="1.2" fill="{c_muted}">NODE.JS  /  PHP 8  /  CRYPTOGRAPHY  /  CANVAS</text>
  <line x1="48" y1="278" x2="912" y2="278" stroke="{c_border}" stroke-width="1"/>
  <circle cx="54" cy="303" r="3.8" fill="{c_accent_3}" class="status"/>
  <text x="67" y="307" font-family="{MONO_FONT}" font-size="10.5" letter-spacing="0.9" fill="{c_muted}">OPEN TO SOFTWARE ENGINEERING OPPORTUNITIES</text>
  <text x="912" y="307" text-anchor="end" font-family="{MONO_FONT}" font-size="10.5" letter-spacing="0.9" fill="{c_muted}">SRI LANKA · @{html.escape(USERNAME.upper())}</text>
{ide_scene(t, 536, 26, 0.88)}"""

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Pushpika Odisha — Systems and Full-Stack Software Engineer">
{shared_defs}
  <rect width="{w}" height="{h}" rx="16" fill="url(#background)" stroke="{c_border}" stroke-width="1.5"/>
  <rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="15" fill="url(#dots)"/>
{body}
</svg>
"""


def render_architecture(t: dict, mobile: bool = False) -> str:
    """Render an animated 3-tier system architecture showcase SVG."""
    w, h = (540, 390) if mobile else (960, 190)
    c_bg1 = t["bg_start"]
    c_bg2 = t["bg_end"]
    c_border = t["border"]
    c_surface = t["surface"]
    c_text = t["text"]
    c_muted = t["muted"]
    c_accent = t["accent"]
    c_accent_2 = t["accent_2"]
    c_accent_3 = t["accent_3"]
    c_wire = t["wire"]

    nodes = [
        ("01 · INTERFACE &amp; SIMULATION", "Canvas 2D/3D · Web Audio", "Real-time physics, 4D projections, UI", c_accent_3),
        ("02 · ENGINES &amp; APIs", "Node.js ESM · PHP 8.3 MVC", "Chaos testing, SSE telemetry, RBAC", c_accent),
        ("03 · DATA &amp; INTEGRITY", "SQLite FTS5/PDO · Merkle", "Full-text indexing &amp; RFC 6962 proofs", c_accent_2),
    ]

    cards = []
    if mobile:
        for i, (tag, title, sub, col) in enumerate(nodes):
            y = 24 + i * 118
            cards.append(
                f'<rect x="24" y="{y}" width="492" height="96" rx="12" fill="{c_surface}" stroke="{c_border}" stroke-width="1.2"/>'
                f'<rect x="24" y="{y}" width="4" height="96" rx="2" fill="{col}"/>'
                f'<text x="44" y="{y + 26}" font-family="{MONO_FONT}" font-size="10.5" fill="{col}">{tag}</text>'
                f'<text x="44" y="{y + 52}" font-family="{SANS_FONT}" font-size="17" font-weight="700" fill="{c_text}">{title}</text>'
                f'<text x="44" y="{y + 76}" font-family="{SANS_FONT}" font-size="12.5" fill="{c_muted}">{sub}</text>'
            )
        wires = (
            f'<line x1="270" y1="120" x2="270" y2="142" stroke="{c_wire}" stroke-width="2"/>'
            f'<line x1="270" y1="238" x2="270" y2="260" stroke="{c_wire}" stroke-width="2"/>'
        )
    else:
        for i, (tag, title, sub, col) in enumerate(nodes):
            x = 28 + i * 314
            cards.append(
                f'<rect x="{x}" y="44" width="276" height="114" rx="12" fill="{c_surface}" stroke="{c_border}" stroke-width="1.2"/>'
                f'<rect x="{x}" y="44" width="276" height="3" rx="1.5" fill="{col}"/>'
                f'<text x="{x + 18}" y="74" font-family="{MONO_FONT}" font-size="10" letter-spacing="0.7" fill="{col}">{tag}</text>'
                f'<text x="{x + 18}" y="102" font-family="{SANS_FONT}" font-size="16" font-weight="700" fill="{c_text}">{title}</text>'
                f'<text x="{x + 18}" y="128" font-family="{SANS_FONT}" font-size="12" fill="{c_muted}">{sub}</text>'
            )
        wires = (
            f'<path d="M 304 101 H 342" stroke="{c_wire}" stroke-width="2"/>'
            f'<path class="flow" d="M 304 101 H 342" stroke="{c_accent}" stroke-width="2"/>'
            f'<path d="M 618 101 H 656" stroke="{c_wire}" stroke-width="2"/>'
            f'<path class="flow" d="M 618 101 H 656" stroke="{c_accent_2}" stroke-width="2"/>'
        )

    header_label = (
        f'<text x="28" y="28" font-family="{MONO_FONT}" font-size="10.5" letter-spacing="1.2" fill="{c_muted}">ENGINEERING ARCHITECTURE PIPELINE</text>'
        if not mobile
        else ""
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Engineering Architecture Pipeline">
  <defs>
    <linearGradient id="archBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{c_bg1}"/>
      <stop offset="100%" stop-color="{c_bg2}"/>
    </linearGradient>
  </defs>
  <style>
    .flow{{stroke-dasharray:5 9;animation:flow 1.8s linear infinite}}
    @keyframes flow{{to{{stroke-dashoffset:-28}}}}
    @media(prefers-reduced-motion:reduce){{.flow{{animation:none}}}}
  </style>
  <rect width="{w}" height="{h}" rx="16" fill="url(#archBg)" stroke="{c_border}" stroke-width="1.5"/>
  {header_label}
  {wires}
  {"".join(cards)}
</svg>
"""


def render_stats(t: dict, m: dict, mobile: bool = False) -> str:
    """Render an executive GitHub metrics + language + top repositories SVG."""
    w, h = (540, 390) if mobile else (960, 240)
    pad = 26 if mobile else 34

    c_bg1 = t["bg_start"]
    c_bg2 = t["bg_end"]
    c_surface = t["surface"]
    c_border = t["border"]
    c_text = t["text"]
    c_muted = t["muted"]
    c_accent = t["accent"]
    c_accent_2 = t["accent_2"]
    c_accent_3 = t["accent_3"]
    c_bar_bg = t["bar_bg"]

    kpi_items = [
        ("REPOSITORIES", str(m["public_repos"]), c_accent),
        ("LANGUAGES", str(m["lang_count"]), c_accent_3),
        ("TOTAL STARS", str(m["stars"]), c_accent_2),
        ("FOLLOWERS", str(m["followers"]), c_accent),
    ]

    bar_x = pad if mobile else 490
    bar_w = (w - pad * 2) if mobile else 436
    bar_y = 204 if mobile else 66

    segments = []
    legend = []
    cursor_x = bar_x
    for idx, (lang, pct) in enumerate(m["top_langs"]):
        color = LANG_COLORS.get(lang, c_accent)
        seg_w = max(round((pct / 100.0) * bar_w), 4)
        if idx == len(m["top_langs"]) - 1:
            seg_w = max(bar_x + bar_w - cursor_x, 4)
        segments.append(
            f'<rect x="{cursor_x}" y="{bar_y}" width="{seg_w}" height="11" fill="{color}"/>'
        )
        cursor_x += seg_w

        row_y = (bar_y + 38 + idx * 25) if mobile else (104 + idx * 24)
        esc_lang = html.escape(lang)
        legend.append(
            f'<circle cx="{bar_x + 6}" cy="{row_y - 4}" r="4.5" fill="{color}"/>'
            f'<text x="{bar_x + 19}" y="{row_y}" font-family="{SANS_FONT}" font-size="13" font-weight="600" fill="{c_text}">{esc_lang}</text>'
            f'<text x="{bar_x + bar_w}" y="{row_y}" text-anchor="end" font-family="{MONO_FONT}" font-size="12" fill="{c_muted}">{pct:.1f}%</text>'
        )

    kpi_svg = []
    if mobile:
        col_w = (w - pad * 2 - 12) // 2
        for idx, (label, value, col) in enumerate(kpi_items):
            cx = idx % 2
            cy = idx // 2
            kx = pad + cx * (col_w + 12)
            ky = 56 + cy * 58
            kpi_svg.append(
                f'<rect x="{kx}" y="{ky}" width="{col_w}" height="48" rx="9" fill="{c_surface}" stroke="{c_border}" stroke-width="1.2"/>'
                f'<rect x="{kx}" y="{ky}" width="{col_w}" height="2.5" rx="1.2" fill="{col}"/>'
                f'<text x="{kx + 12}" y="{ky + 20}" font-family="{MONO_FONT}" font-size="9.5" fill="{c_muted}">{label}</text>'
                f'<text x="{kx + 12}" y="{ky + 40}" font-family="{SANS_FONT}" font-size="18" font-weight="700" fill="{c_text}">{value}</text>'
            )
        lang_title_y = 192
        divider = f'<line x1="{pad}" y1="174" x2="{w - pad}" y2="174" stroke="{c_border}" stroke-width="1"/>'
    else:
        col_w = 198
        for idx, (label, value, col) in enumerate(kpi_items):
            cx = idx % 2
            cy = idx // 2
            kx = pad + cx * (col_w + 14)
            ky = 58 + cy * 70
            kpi_svg.append(
                f'<rect x="{kx}" y="{ky}" width="{col_w}" height="58" rx="10" fill="{c_surface}" stroke="{c_border}" stroke-width="1.2"/>'
                f'<rect x="{kx}" y="{ky}" width="{col_w}" height="2.5" rx="1.2" fill="{col}"/>'
                f'<text x="{kx + 14}" y="{ky + 22}" font-family="{MONO_FONT}" font-size="10" letter-spacing="0.6" fill="{c_muted}">{label}</text>'
                f'<text x="{kx + 14}" y="{ky + 46}" font-family="{SANS_FONT}" font-size="22" font-weight="700" fill="{c_text}">{value}</text>'
            )
        lang_title_y = 46
        divider = f'<line x1="464" y1="28" x2="464" y2="210" stroke="{c_border}" stroke-width="1"/>'

    clip_id = f"langClip_{'m' if mobile else 'd'}"
    updated = html.escape(m["updated"])

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="GitHub Engineering Metrics">
  <defs>
    <linearGradient id="statsBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{c_bg1}"/>
      <stop offset="100%" stop-color="{c_bg2}"/>
    </linearGradient>
    <clipPath id="{clip_id}">
      <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="11" rx="5.5"/>
    </clipPath>
  </defs>
  <rect width="{w}" height="{h}" rx="16" fill="url(#statsBg)" stroke="{c_border}" stroke-width="1.5"/>
  <text x="{pad}" y="38" font-family="{MONO_FONT}" font-size="11" font-weight="600" letter-spacing="1" fill="{c_muted}">GITHUB SNAPSHOT</text>
  {"".join(kpi_svg)}
  {divider}
  <text x="{bar_x}" y="{lang_title_y}" font-family="{MONO_FONT}" font-size="11" font-weight="600" letter-spacing="1" fill="{c_muted}">LANGUAGE DISTRIBUTION (BY BYTES)</text>
  <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="11" rx="5.5" fill="{c_bar_bg}"/>
  <g clip-path="url(#{clip_id})">{"".join(segments)}</g>
  {"".join(legend)}
  <text x="{pad}" y="{h - 14}" font-family="{MONO_FONT}" font-size="10.5" fill="{c_muted}">Updated daily via GitHub Actions · {updated}</text>
</svg>
"""


def render_footer(t: dict) -> str:
    """Render sleek footer banner SVG."""
    w, h = 960, 108
    c_bg1 = t["bg_start"]
    c_bg2 = t["bg_end"]
    c_border = t["border"]
    c_text = t["text"]
    c_muted = t["muted"]
    c_accent = t["accent"]
    c_accent_2 = t["accent_2"]
    c_accent_3 = t["accent_3"]
    esc_user = html.escape(USERNAME)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Let's build something dependable">
  <defs>
    <linearGradient id="footerBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{c_bg1}"/>
      <stop offset="100%" stop-color="{c_bg2}"/>
    </linearGradient>
    <linearGradient id="footerAccent" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{c_accent_3}"/>
      <stop offset="55%" stop-color="{c_accent}"/>
      <stop offset="100%" stop-color="{c_accent_2}"/>
    </linearGradient>
  </defs>
  <rect width="{w}" height="{h}" rx="16" fill="url(#footerBg)" stroke="{c_border}" stroke-width="1.5"/>
  <rect x="36" y="31" width="4" height="46" rx="2" fill="url(#footerAccent)"/>
  <text x="56" y="49" font-family="{SANS_FONT}" font-size="16.5" font-weight="700" fill="{c_text}">Let's build dependable software and high-impact engineering systems.</text>
  <text x="56" y="73" font-family="{MONO_FONT}" font-size="12" fill="{c_muted}">pushpikaodisha.contact@gmail.com  ·  github.com/{esc_user}  ·  Sri Lanka</text>
</svg>
"""


def main() -> None:
    os.makedirs(ASSETS_DIR, exist_ok=True)
    metrics = fetch_github_metrics()

    outputs = {}
    for mode, theme in THEMES.items():
        outputs[f"hero-{mode}.svg"] = render_hero(theme, mobile=False)
        outputs[f"hero-{mode}-mobile.svg"] = render_hero(theme, mobile=True)
        outputs[f"arch-{mode}.svg"] = render_architecture(theme, mobile=False)
        outputs[f"arch-{mode}-mobile.svg"] = render_architecture(theme, mobile=True)
        outputs[f"stats-{mode}.svg"] = render_stats(theme, metrics, mobile=False)
        outputs[f"stats-{mode}-mobile.svg"] = render_stats(theme, metrics, mobile=True)
        outputs[f"footer-{mode}.svg"] = render_footer(theme)

    for filename, content in outputs.items():
        path = os.path.join(ASSETS_DIR, filename)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"Generated {filename}")


if __name__ == "__main__":
    main()
