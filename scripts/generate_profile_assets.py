"""Generate original mathematical & telemetry SVG assets for pushpikaodisha."""

from __future__ import annotations

import html
import json
import math
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone

USERNAME = os.getenv("GITHUB_REPOSITORY_OWNER", "pushpikaodisha")
TOKEN = os.getenv("PROFILE_GH_TOKEN") or os.getenv("GITHUB_TOKEN", "")
EMAIL = "pushpikaodisha.contact@gmail.com"
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

SANS_FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
MONO_FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"

THEMES = {
    "dark": {
        "bg_1": "#060A12",
        "bg_2": "#0D1526",
        "panel": "#0B111E",
        "panel_alt": "#111A2E",
        "border": "#1E293B",
        "border_hi": "#334155",
        "text": "#F8FAFC",
        "subtext": "#CBD5E1",
        "muted": "#64748B",
        "cyan": "#22D3EE",
        "indigo": "#818CF8",
        "violet": "#A855F7",
        "emerald": "#34D399",
        "grid": "#1E293B",
        "glow": "#22D3EE",
        "radar_fill": "#22D3EE",
    },
    "light": {
        "bg_1": "#F8FAFC",
        "bg_2": "#EFF6FF",
        "panel": "#FFFFFF",
        "panel_alt": "#F1F5F9",
        "border": "#CBD5E1",
        "border_hi": "#94A3B8",
        "text": "#0F172A",
        "subtext": "#334155",
        "muted": "#64748B",
        "cyan": "#0284C7",
        "indigo": "#4F46E5",
        "violet": "#7C3AED",
        "emerald": "#059669",
        "grid": "#CBD5E1",
        "glow": "#0284C7",
        "radar_fill": "#0284C7",
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
    """Execute a GitHub REST API GET request."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "pushpikaodisha-observatory",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def gh_graphql(query: str, variables: dict) -> dict | None:
    """Execute a GitHub GraphQL query when a token is available."""
    if not TOKEN:
        return None
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "pushpikaodisha-observatory",
    }
    req = urllib.request.Request("https://api.github.com/graphql", data=payload, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "errors" in data:
                return None
            return data.get("data")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None


def fetch_metrics() -> dict:
    """Fetch public and optional contribution metrics from GitHub APIs."""
    user = gh_get(f"https://api.github.com/users/{USERNAME}")
    repos = gh_get(f"https://api.github.com/users/{USERNAME}/repos?per_page=100&type=owner")

    non_forks = [
        r for r in repos if not r.get("fork") and r.get("name", "").lower() != USERNAME.lower()
    ]
    stars = sum(int(r.get("stargazers_count", 0)) for r in repos)

    lang_bytes: dict[str, int] = {}
    repo_names = {r.get("name", "").lower() for r in non_forks}
    for repo in non_forks:
        lang_url = repo.get("languages_url")
        if not lang_url:
            continue
        try:
            data = gh_get(lang_url)
            if isinstance(data, dict):
                for lang, bcount in data.items():
                    lang_bytes[lang] = lang_bytes.get(lang, 0) + int(bcount)
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

    # Optional GraphQL yearly contributions (works automatically when PAT or Actions token permits)
    contributions_year = None
    gql = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
          }
        }
      }
    }
    """
    gql_data = gh_graphql(gql, {"login": USERNAME})
    if gql_data and gql_data.get("user"):
        contributions_year = (
            gql_data["user"]
            .get("contributionsCollection", {})
            .get("contributionCalendar", {})
            .get("totalContributions")
        )

    # Compute 5-axis capability weights (0.55 to 0.95) from real repo domains & language bytes
    js_ratio = lang_bytes.get("JavaScript", 0) / total_bytes
    php_ratio = lang_bytes.get("PHP", 0) / total_bytes
    html_ratio = lang_bytes.get("HTML", 0) / total_bytes

    def score(base: float, boost: float) -> float:
        return round(min(0.95, max(0.55, base + boost)), 3)

    radar = [
        ("SYSTEMS / NODE", score(0.76, js_ratio * 0.45 + (0.06 if "polyglot-forge" in repo_names else 0.0))),
        ("BACKEND / PHP", score(0.74, php_ratio * 0.65 + (0.06 if "apexguild-workflow" in repo_names else 0.0))),
        ("CRYPTO / DATA", score(0.78, (0.12 if "chronoledger-vault" in repo_names else 0.0) + (0.04 if "neuroscribe-vault" in repo_names else 0.0))),
        ("4D / GRAPHICS", score(0.72, html_ratio * 0.28 + (0.08 if "chronoforge-4d" in repo_names else 0.0))),
        ("AUDIO / ALIFE", score(0.70, (0.10 if "binaural-flow-studio" in repo_names else 0.0) + (0.10 if "bioswarm-genesis" in repo_names else 0.0))),
    ]

    return {
        "public_repos": int(user.get("public_repos", len(repos))),
        "lang_count": len(top_langs),
        "stars": stars,
        "followers": int(user.get("followers", 0)),
        "contributions_year": contributions_year,
        "top_langs": top_langs,
        "total_kb": round(total_bytes / 1024),
        "radar": radar,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


def project_tesseract(cx: float, cy: float, scale: float) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, float]]]:
    """Project a 4D tesseract (16 vertices, 32 edges) into 2D screen coordinates."""
    verts_4d = []
    for i in range(16):
        verts_4d.append((
            1.0 if (i & 1) else -1.0,
            1.0 if (i & 2) else -1.0,
            1.0 if (i & 4) else -1.0,
            1.0 if (i & 8) else -1.0,
        ))

    # Aesthetic 4D rotation angles
    a_xw, a_zw, a_xz, a_yz = 0.62, 0.44, 0.52, 0.35

    def rot(a: float, b: float, angle: float) -> tuple[float, float]:
        ca, sa = math.cos(angle), math.sin(angle)
        return a * ca - b * sa, a * sa + b * ca

    projected: list[tuple[float, float, float]] = []
    for x, y, z, w in verts_4d:
        x, w = rot(x, w, a_xw)
        z, w = rot(z, w, a_zw)
        x, z = rot(x, z, a_xz)
        y, z = rot(y, z, a_yz)

        d4 = 3.2
        f4 = d4 / (d4 - w)
        x3, y3, z3 = x * f4, y * f4, z * f4

        d3 = 4.2
        f3 = d3 / (d3 - z3)
        px = cx + x3 * f3 * scale
        py = cy + y3 * f3 * scale
        depth = (w + z3) * 0.5
        projected.append((px, py, depth))

    edges: list[tuple[int, int, float]] = []
    for i in range(16):
        for j in range(i + 1, 16):
            if bin(i ^ j).count("1") == 1:
                avg_d = (projected[i][2] + projected[j][2]) * 0.5
                edges.append((i, j, avg_d))

    edges.sort(key=lambda e: e[2])
    return projected, edges


def render_hero(t: dict) -> str:
    """Render original 4D Tesseract Constellation Hero SVG (960x300)."""
    w, h = 960, 300
    c_bg1 = t["bg_1"]
    c_bg2 = t["bg_2"]
    c_border = t["border"]
    c_border_hi = t["border_hi"]
    c_text = t["text"]
    c_sub = t["subtext"]
    c_muted = t["muted"]
    c_cyan = t["cyan"]
    c_indigo = t["indigo"]
    c_violet = t["violet"]
    c_emerald = t["emerald"]
    c_grid = t["grid"]
    c_glow = t["glow"]

    verts, edges = project_tesseract(cx=745.0, cy=136.0, scale=43.0)

    edge_svg = []
    pulse_paths = []
    for idx, (i, j, depth) in enumerate(edges):
        x1, y1, _ = verts[i]
        x2, y2, _ = verts[j]
        is_hyper = (i ^ j) == 8
        op = round(min(0.88, max(0.22, 0.48 + depth * 0.25)), 2)
        stroke = c_violet if is_hyper else (c_cyan if depth > 0 else c_indigo)
        sw = "1.45" if depth > 0.1 else "1.0"
        edge_svg.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{stroke}" stroke-width="{sw}" stroke-opacity="{op}"/>'
        )
        if idx % 5 == 0:
            pulse_paths.append(
                f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                f'stroke="{c_cyan}" stroke-width="1.8" class="pkt"/>'
            )

    vert_svg = []
    for idx, (px, py, depth) in enumerate(verts):
        r = round(max(2.2, min(4.3, 3.0 + depth * 0.9)), 1)
        col = c_cyan if (idx & 8) else c_violet
        op = round(min(1.0, max(0.45, 0.72 + depth * 0.22)), 2)
        vert_svg.append(
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r}" fill="{col}" fill-opacity="{op}"/>'
        )

    esc_user = html.escape(USERNAME.upper())
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Pushpika Odisha — Systems and Full-Stack Architect">
  <defs>
    <linearGradient id="heroBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{c_bg1}"/>
      <stop offset="100%" stop-color="{c_bg2}"/>
    </linearGradient>
    <linearGradient id="brandGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{c_cyan}"/>
      <stop offset="55%" stop-color="{c_indigo}"/>
      <stop offset="100%" stop-color="{c_violet}"/>
    </linearGradient>
    <radialGradient id="constellationGlow">
      <stop offset="0%" stop-color="{c_glow}" stop-opacity="0.22"/>
      <stop offset="60%" stop-color="{c_violet}" stop-opacity="0.08"/>
      <stop offset="100%" stop-color="{c_glow}" stop-opacity="0"/>
    </radialGradient>
    <pattern id="orthoGrid" width="32" height="32" patternUnits="userSpaceOnUse">
      <path d="M 32 0 L 0 0 0 32" fill="none" stroke="{c_grid}" stroke-width="0.6" stroke-opacity="0.45"/>
    </pattern>
  </defs>
  <style>
    .pkt{{stroke-dasharray:6 18;animation:flow 2.8s linear infinite}}
    @keyframes flow{{to{{stroke-dashoffset:-48}}}}
    .orbit{{transform-origin:745px 136px;animation:spin 32s linear infinite}}
    @keyframes spin{{to{{transform:rotate(360deg)}}}}
    .pulse{{animation:blink 3s ease-in-out infinite}}
    @keyframes blink{{50%{{opacity:0.35}}}}
    @media(prefers-reduced-motion:reduce){{.pkt,.orbit,.pulse{{animation:none}}}}
  </style>

  <rect width="{w}" height="{h}" rx="16" fill="url(#heroBg)" stroke="{c_border}" stroke-width="1.5"/>
  <rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="15" fill="url(#orthoGrid)"/>
  <circle cx="745" cy="136" r="190" fill="url(#constellationGlow)"/>

  <!-- 4D Hypercube Constellation + Subtle Orbital Telemetry Rings -->
  <g class="orbit">
    <circle cx="745" cy="136" r="114" fill="none" stroke="{c_border_hi}" stroke-width="1" stroke-dasharray="3 9" opacity="0.55"/>
    <circle cx="859" cy="136" r="2.5" fill="{c_cyan}"/>
    <circle cx="631" cy="136" r="2.5" fill="{c_violet}"/>
  </g>
  <circle cx="745" cy="136" r="90" fill="none" stroke="{c_border}" stroke-width="0.9" opacity="0.6"/>
  {"".join(edge_svg)}
  {"".join(pulse_paths)}
  {"".join(vert_svg)}
  <text x="745" y="276" text-anchor="middle" font-family="{MONO_FONT}" font-size="9.5" letter-spacing="1.4" fill="{c_muted}">4D HYPERCUBE PROJECTION · 16 VERTICES · 32 EDGES</text>

  <!-- PO Geometric Monogram Crest -->
  <g transform="translate(44, 34)">
    <polygon points="16,0 30,8 30,24 16,32 2,24 2,8" fill="none" stroke="url(#brandGrad)" stroke-width="1.8"/>
    <text x="16" y="20" text-anchor="middle" font-family="{MONO_FONT}" font-size="11" font-weight="700" fill="{c_text}">PO</text>
  </g>
  <text x="88" y="54" font-family="{MONO_FONT}" font-size="11" letter-spacing="1.6" fill="{c_cyan}">SYSTEMS &amp; FULL-STACK ARCHITECT</text>

  <!-- Main Typography -->
  <text x="44" y="114" font-family="{SANS_FONT}" font-size="42" font-weight="800" letter-spacing="-1.1" fill="{c_text}">Pushpika <tspan fill="url(#brandGrad)">Odisha</tspan></text>
  <text x="44" y="150" font-family="{SANS_FONT}" font-size="16" font-weight="500" fill="{c_sub}">Zero-dependency engines, cryptographic integrity,</text>
  <text x="44" y="173" font-family="{SANS_FONT}" font-size="16" font-weight="500" fill="{c_sub}">and deterministic full-stack systems.</text>

  <!-- Stack Coordinate Chips -->
  <text x="44" y="214" font-family="{MONO_FONT}" font-size="11" letter-spacing="1.1" fill="{c_muted}">NODE.JS ESM  ·  PHP 8.3 MVC  ·  MERKLE CRYPTO  ·  4D / AUDIO</text>

  <!-- Bottom Observatory Status Bar -->
  <line x1="44" y1="246" x2="540" y2="246" stroke="{c_border}" stroke-width="1"/>
  <circle cx="50" cy="268" r="3.5" fill="{c_emerald}" class="pulse"/>
  <text x="63" y="272" font-family="{MONO_FONT}" font-size="10.5" letter-spacing="0.8" fill="{c_sub}">SRI LANKA (6.93° N, 79.86° E)</text>
  <text x="540" y="272" text-anchor="end" font-family="{MONO_FONT}" font-size="10.5" letter-spacing="0.8" fill="{c_muted}">@{esc_user}</text>
</svg>
"""


def render_telemetry(t: dict, m: dict) -> str:
    """Render dual-panel Engineering Radar + Live GitHub Telemetry SVG (960x265)."""
    w, h = 960, 265
    c_bg1 = t["bg_1"]
    c_bg2 = t["bg_2"]
    c_panel = t["panel"]
    c_border = t["border"]
    c_border_hi = t["border_hi"]
    c_text = t["text"]
    c_sub = t["subtext"]
    c_muted = t["muted"]
    c_cyan = t["cyan"]
    c_indigo = t["indigo"]
    c_violet = t["violet"]
    c_emerald = t["emerald"]

    # Left Panel: 5-axis Pentagon Radar centered at (205, 144), max radius 72
    rcx, rcy, rmax = 205.0, 145.0, 70.0
    radar_rings = []
    for frac in (0.25, 0.5, 0.75, 1.0):
        pts = []
        for idx in range(5):
            ang = -math.pi / 2 + idx * (2 * math.pi / 5)
            px = rcx + math.cos(ang) * rmax * frac
            py = rcy + math.sin(ang) * rmax * frac
            pts.append(f"{px:.1f},{py:.1f}")
        radar_rings.append(
            f'<polygon points="{" ".join(pts)}" fill="none" stroke="{c_border}" stroke-width="1"/>'
        )

    axis_lines = []
    poly_pts = []
    vertex_dots = []
    axis_labels = []
    for idx, (label, val) in enumerate(m["radar"]):
        ang = -math.pi / 2 + idx * (2 * math.pi / 5)
        ax_x = rcx + math.cos(ang) * rmax
        ax_y = rcy + math.sin(ang) * rmax
        axis_lines.append(
            f'<line x1="{rcx:.1f}" y1="{rcy:.1f}" x2="{ax_x:.1f}" y2="{ax_y:.1f}" stroke="{c_border}" stroke-width="1"/>'
        )

        vx = rcx + math.cos(ang) * rmax * val
        vy = rcy + math.sin(ang) * rmax * val
        poly_pts.append(f"{vx:.1f},{vy:.1f}")
        vertex_dots.append(f'<circle cx="{vx:.1f}" cy="{vy:.1f}" r="3.5" fill="{c_cyan}"/>')

        lx = rcx + math.cos(ang) * (rmax + 18)
        ly = rcy + math.sin(ang) * (rmax + 18)
        anchor = "middle"
        if math.cos(ang) > 0.25:
            anchor = "start"
        elif math.cos(ang) < -0.25:
            anchor = "end"
        if idx == 0:
            ly -= 2
        elif idx in (2, 3):
            ly += 8
        axis_labels.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" font-family="{MONO_FONT}" font-size="9.5" font-weight="600" fill="{c_sub}">{html.escape(label)}</text>'
        )

    # Right Panel: KPIs + Language Distribution Bar
    kpis = [
        ("PUBLIC REPOS", str(m["public_repos"]), c_cyan),
        ("CODEBASE", f"{m['total_kb']} KB", c_indigo),
        (
            "YEAR COMMITS" if m["contributions_year"] is not None else "LANGUAGES",
            str(m["contributions_year"] if m["contributions_year"] is not None else m["lang_count"]),
            c_emerald,
        ),
        ("FOLLOWERS", str(m["followers"]), c_violet),
    ]

    kpi_svg = []
    for idx, (label, val, col) in enumerate(kpis):
        kx = 452 + idx * 120
        ky = 56
        kpi_svg.append(
            f'<rect x="{kx}" y="{ky}" width="110" height="58" rx="9" fill="{c_panel}" stroke="{c_border}" stroke-width="1.2"/>'
            f'<rect x="{kx}" y="{ky}" width="110" height="2.5" rx="1.2" fill="{col}"/>'
            f'<text x="{kx + 11}" y="{ky + 21}" font-family="{MONO_FONT}" font-size="9" letter-spacing="0.5" fill="{c_muted}">{label}</text>'
            f'<text x="{kx + 11}" y="{ky + 46}" font-family="{SANS_FONT}" font-size="19" font-weight="700" fill="{c_text}">{html.escape(val)}</text>'
        )

    bar_x, bar_y, bar_w = 452, 146, 470
    segments = []
    legend = []
    cursor_x = bar_x
    for idx, (lang, pct) in enumerate(m["top_langs"]):
        col = LANG_COLORS.get(lang, c_cyan)
        seg_w = max(round((pct / 100.0) * bar_w), 4)
        if idx == len(m["top_langs"]) - 1:
            seg_w = max(bar_x + bar_w - cursor_x, 4)
        segments.append(f'<rect x="{cursor_x}" y="{bar_y}" width="{seg_w}" height="10" fill="{col}"/>')
        cursor_x += seg_w

        # Two-column legend below bar
        col_idx = idx % 2
        row_idx = idx // 2
        lx = bar_x + col_idx * 240
        ly = 180 + row_idx * 22
        legend.append(
            f'<circle cx="{lx + 5}" cy="{ly - 4}" r="4" fill="{col}"/>'
            f'<text x="{lx + 16}" y="{ly}" font-family="{SANS_FONT}" font-size="12.5" font-weight="600" fill="{c_text}">{html.escape(lang)}</text>'
            f'<text x="{lx + 218}" y="{ly}" text-anchor="end" font-family="{MONO_FONT}" font-size="11.5" fill="{c_muted}">{pct:.1f}%</text>'
        )

    updated = html.escape(m["updated"])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Engineering Capability Radar and GitHub Telemetry">
  <defs>
    <linearGradient id="telBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{c_bg1}"/>
      <stop offset="100%" stop-color="{c_bg2}"/>
    </linearGradient>
    <linearGradient id="radarGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{c_cyan}" stop-opacity="0.34"/>
      <stop offset="100%" stop-color="{c_violet}" stop-opacity="0.24"/>
    </linearGradient>
    <clipPath id="langSpectrum">
      <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="10" rx="5"/>
    </clipPath>
  </defs>

  <rect width="{w}" height="{h}" rx="16" fill="url(#telBg)" stroke="{c_border}" stroke-width="1.5"/>

  <!-- Left Radar Section -->
  <text x="34" y="36" font-family="{MONO_FONT}" font-size="10.5" font-weight="600" letter-spacing="1.2" fill="{c_muted}">DOMAIN CAPABILITY RADAR</text>
  {"".join(radar_rings)}
  {"".join(axis_lines)}
  <polygon points="{" ".join(poly_pts)}" fill="url(#radarGrad)" stroke="{c_cyan}" stroke-width="2"/>
  {"".join(vertex_dots)}
  {"".join(axis_labels)}

  <!-- Center Divider -->
  <line x1="418" y1="26" x2="418" y2="238" stroke="{c_border_hi}" stroke-width="1" stroke-dasharray="3 4"/>

  <!-- Right Live Telemetry Section -->
  <text x="452" y="36" font-family="{MONO_FONT}" font-size="10.5" font-weight="600" letter-spacing="1.2" fill="{c_muted}">LIVE GITHUB TELEMETRY</text>
  {"".join(kpi_svg)}
  <text x="452" y="135" font-family="{MONO_FONT}" font-size="10" letter-spacing="0.9" fill="{c_muted}">BYTE-WEIGHTED LANGUAGE SPECTRUM</text>
  <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="10" rx="5" fill="{c_border}"/>
  <g clip-path="url(#langSpectrum)">{"".join(segments)}</g>
  {"".join(legend)}
  <text x="922" y="246" text-anchor="end" font-family="{MONO_FONT}" font-size="10" fill="{c_muted}">SYNCED {updated}</text>
</svg>
"""


def render_labs(t: dict) -> str:
    """Render 3 mathematical mini-visual panels for Simulation & Audio Labs (960x185)."""
    w, h = 960, 185
    c_bg1 = t["bg_1"]
    c_bg2 = t["bg_2"]
    c_panel = t["panel"]
    c_border = t["border"]
    c_text = t["text"]
    c_muted = t["muted"]
    c_cyan = t["cyan"]
    c_indigo = t["indigo"]
    c_violet = t["violet"]
    c_emerald = t["emerald"]

    # Lab 1: Harmonic Interference Wave (Binaural Flow Studio)
    wave_1 = []
    wave_2 = []
    for step in range(46):
        x = 50 + step * 5.0
        u = step / 45.0 * math.pi * 4.0
        y1 = 112 + math.sin(u) * math.cos(u * 0.35) * 18
        y2 = 112 + math.cos(u * 1.4) * 12
        wave_1.append(f"{'M' if step == 0 else 'L'} {x:.1f} {y1:.1f}")
        wave_2.append(f"{'M' if step == 0 else 'L'} {x:.1f} {y2:.1f}")

    # Lab 2: 4D Tesseract Wireframe Miniature (ChronoForge 4D)
    t_verts, t_edges = project_tesseract(cx=480.0, cy=105.0, scale=12.5)
    mini_t_edges = []
    for i, j, depth in t_edges:
        x1, y1, _ = t_verts[i]
        x2, y2, _ = t_verts[j]
        col = c_violet if (i ^ j) == 8 else c_cyan
        op = round(min(0.9, max(0.25, 0.5 + depth * 0.25)), 2)
        mini_t_edges.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col}" stroke-width="1.1" stroke-opacity="{op}"/>'
        )

    # Lab 3: BioSwarm Neural Nodes (BioSwarm Genesis)
    swarm_nodes = [
        (726, 98, 4.0, c_emerald),
        (752, 126, 3.2, c_cyan),
        (778, 92, 4.5, c_emerald),
        (805, 118, 3.6, c_indigo),
        (834, 96, 3.0, c_cyan),
        (856, 124, 4.2, c_emerald),
        (742, 108, 2.6, c_violet),
        (820, 102, 2.8, c_violet),
    ]
    swarm_edges = [(0, 1), (0, 6), (1, 2), (2, 3), (3, 4), (3, 7), (4, 5), (6, 2), (7, 5)]
    swarm_svg = []
    for a, b in swarm_edges:
        x1, y1, _, _ = swarm_nodes[a]
        x2, y2, _, _ = swarm_nodes[b]
        swarm_svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{c_emerald}" stroke-width="1" stroke-opacity="0.4"/>')
    for nx, ny, nr, ncol in swarm_nodes:
        swarm_svg.append(f'<circle cx="{nx}" cy="{ny}" r="{nr}" fill="{ncol}"/>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Interactive Simulation and Audio Labs">
  <defs>
    <linearGradient id="labsBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{c_bg1}"/>
      <stop offset="100%" stop-color="{c_bg2}"/>
    </linearGradient>
  </defs>
  <rect width="{w}" height="{h}" rx="16" fill="url(#labsBg)" stroke="{c_border}" stroke-width="1.5"/>

  <!-- Card 1: Binaural Flow -->
  <rect x="24" y="20" width="288" height="145" rx="12" fill="{c_panel}" stroke="{c_border}" stroke-width="1.2"/>
  <text x="42" y="45" font-family="{MONO_FONT}" font-size="10" font-weight="600" fill="{c_cyan}">LAB-01 · ACOUSTIC CYMATICS</text>
  <text x="42" y="66" font-family="{SANS_FONT}" font-size="15.5" font-weight="700" fill="{c_text}">Binaural Flow Studio</text>
  <path d="{" ".join(wave_2)}" fill="none" stroke="{c_indigo}" stroke-width="1.3" stroke-opacity="0.55"/>
  <path d="{" ".join(wave_1)}" fill="none" stroke="{c_cyan}" stroke-width="2"/>
  <text x="42" y="151" font-family="{MONO_FONT}" font-size="10" fill="{c_muted}">WEB AUDIO · HRTF 3D · CHLADNI</text>

  <!-- Card 2: ChronoForge 4D -->
  <rect x="336" y="20" width="288" height="145" rx="12" fill="{c_panel}" stroke="{c_border}" stroke-width="1.2"/>
  <text x="354" y="45" font-family="{MONO_FONT}" font-size="10" font-weight="600" fill="{c_violet}">LAB-02 · HYPER-GEOMETRY</text>
  <text x="354" y="66" font-family="{SANS_FONT}" font-size="15.5" font-weight="700" fill="{c_text}">ChronoForge 4D</text>
  {"".join(mini_t_edges)}
  <text x="354" y="151" font-family="{MONO_FONT}" font-size="10" fill="{c_muted}">4D TESSERACT · CANVAS · GYRO</text>

  <!-- Card 3: BioSwarm Genesis -->
  <rect x="648" y="20" width="288" height="145" rx="12" fill="{c_panel}" stroke="{c_border}" stroke-width="1.2"/>
  <text x="666" y="45" font-family="{MONO_FONT}" font-size="10" font-weight="600" fill="{c_emerald}">LAB-03 · ARTIFICIAL LIFE</text>
  <text x="666" y="66" font-family="{SANS_FONT}" font-size="15.5" font-weight="700" fill="{c_text}">BioSwarm Genesis</text>
  {"".join(swarm_svg)}
  <text x="666" y="151" font-family="{MONO_FONT}" font-size="10" fill="{c_muted}">NEURAL PERCEPTRON · 60 FPS</text>
</svg>
"""


def render_footer(t: dict) -> str:
    """Render minimalist monogram footer SVG (960x96)."""
    w, h = 960, 96
    c_bg1 = t["bg_1"]
    c_bg2 = t["bg_2"]
    c_border = t["border"]
    c_text = t["text"]
    c_muted = t["muted"]
    c_cyan = t["cyan"]
    c_indigo = t["indigo"]
    c_violet = t["violet"]
    esc_user = html.escape(USERNAME)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Pushpika Odisha contact signature">
  <defs>
    <linearGradient id="fBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{c_bg1}"/>
      <stop offset="100%" stop-color="{c_bg2}"/>
    </linearGradient>
    <linearGradient id="fAccent" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{c_cyan}"/>
      <stop offset="55%" stop-color="{c_indigo}"/>
      <stop offset="100%" stop-color="{c_violet}"/>
    </linearGradient>
  </defs>
  <rect width="{w}" height="{h}" rx="16" fill="url(#fBg)" stroke="{c_border}" stroke-width="1.5"/>
  <g transform="translate(34, 32)">
    <polygon points="16,0 30,8 30,24 16,32 2,24 2,8" fill="none" stroke="url(#fAccent)" stroke-width="1.6"/>
    <text x="16" y="20" text-anchor="middle" font-family="{MONO_FONT}" font-size="10.5" font-weight="700" fill="{c_text}">PO</text>
  </g>
  <text x="82" y="45" font-family="{SANS_FONT}" font-size="15.5" font-weight="700" fill="{c_text}">Open to systems engineering, backend architecture, and collaborative R&amp;D.</text>
  <text x="82" y="68" font-family="{MONO_FONT}" font-size="11.5" fill="{c_muted}">{EMAIL}  ·  github.com/{esc_user}  ·  Sri Lanka</text>
</svg>
"""


def main() -> None:
    os.makedirs(ASSETS_DIR, exist_ok=True)
    metrics = fetch_metrics()

    outputs = {}
    for mode, theme in THEMES.items():
        outputs[f"hero-{mode}.svg"] = render_hero(theme)
        outputs[f"telemetry-{mode}.svg"] = render_telemetry(theme, metrics)
        outputs[f"labs-{mode}.svg"] = render_labs(theme)
        outputs[f"footer-{mode}.svg"] = render_footer(theme)

    for filename, content in outputs.items():
        path = os.path.join(ASSETS_DIR, filename)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"Generated {filename}")


if __name__ == "__main__":
    main()
