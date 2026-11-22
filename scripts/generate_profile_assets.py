"""Generate clean, product-grade Software/Web/AI SVG assets for pushpikaodisha."""

from __future__ import annotations

import html
import json
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
        "bg_1": "#0B0F17",
        "bg_2": "#111827",
        "card": "#131B2B",
        "card_alt": "#182235",
        "border": "#1F2937",
        "border_hi": "#334155",
        "text": "#F8FAFC",
        "subtext": "#CBD5E1",
        "muted": "#94A3B8",
        "accent": "#38BDF8",
        "accent_2": "#6366F1",
        "emerald": "#10B981",
        "amber": "#F59E0B",
        "grid": "#1E293B",
        "bar_bg": "#1E293B",
    },
    "light": {
        "bg_1": "#FFFFFF",
        "bg_2": "#F8FAFC",
        "card": "#FFFFFF",
        "card_alt": "#F1F5F9",
        "border": "#E2E8F0",
        "border_hi": "#CBD5E1",
        "text": "#0F172A",
        "subtext": "#334155",
        "muted": "#64748B",
        "accent": "#0284C7",
        "accent_2": "#4F46E5",
        "emerald": "#059669",
        "amber": "#D97706",
        "grid": "#E2E8F0",
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
    """Execute a GitHub REST API GET request."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "pushpikaodisha-profile-suite",
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
        "User-Agent": "pushpikaodisha-profile-suite",
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
    """Fetch public profile, repository, and language footprint metrics."""
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

    return {
        "public_repos": int(user.get("public_repos", len(repos))),
        "lang_count": len(top_langs),
        "stars": stars,
        "followers": int(user.get("followers", 0)),
        "contributions_year": contributions_year,
        "top_langs": top_langs,
        "total_kb": round(total_bytes / 1024),
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


def render_hero(t: dict) -> str:
    """Render clean Software, Web & AI Architecture Hero SVG (960x265)."""
    w, h = 960, 265
    c_bg1 = t["bg_1"]
    c_bg2 = t["bg_2"]
    c_card = t["card"]
    c_card_alt = t["card_alt"]
    c_border = t["border"]
    c_border_hi = t["border_hi"]
    c_text = t["text"]
    c_sub = t["subtext"]
    c_muted = t["muted"]
    c_accent = t["accent"]
    c_accent_2 = t["accent_2"]
    c_emerald = t["emerald"]
    c_grid = t["grid"]

    esc_user = html.escape(USERNAME)

    # Right-side 2x2 Architecture Nodes: Web App -> API Gateway -> AI & Search -> Data Layer
    nodes = [
        (560, 42, "01 · WEB CLIENT", "Responsive UI &amp; Apps", "HTML5 · JS · SSE Streams", c_accent),
        (748, 42, "02 · API &amp; CORE", "Backend Services", "Node.js · PHP 8 · RBAC", c_accent_2),
        (560, 146, "03 · AI &amp; SEARCH", "Intelligent Workflows", "LLM APIs · FTS5 · Graphs", c_emerald),
        (748, 146, "04 · DATA LAYER", "Storage &amp; Proofs", "SQLite PDO · Merkle Audit", c_accent),
    ]

    node_svg = []
    for nx, ny, tag, title, sub, col in nodes:
        node_svg.append(
            f'<rect x="{nx}" y="{ny}" width="172" height="76" rx="10" fill="{c_card}" stroke="{c_border_hi}" stroke-width="1.2"/>'
            f'<rect x="{nx}" y="{ny}" width="172" height="2.5" rx="1.2" fill="{col}"/>'
            f'<text x="{nx + 13}" y="{ny + 22}" font-family="{MONO_FONT}" font-size="9" font-weight="600" letter-spacing="0.6" fill="{col}">{tag}</text>'
            f'<text x="{nx + 13}" y="{ny + 43}" font-family="{SANS_FONT}" font-size="13.5" font-weight="700" fill="{c_text}">{title}</text>'
            f'<text x="{nx + 13}" y="{ny + 61}" font-family="{MONO_FONT}" font-size="9.5" fill="{c_muted}">{sub}</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Pushpika Odisha — Software, Web Applications and AI Systems Engineer">
  <defs>
    <linearGradient id="heroBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{c_bg1}"/>
      <stop offset="100%" stop-color="{c_bg2}"/>
    </linearGradient>
    <linearGradient id="brandGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{c_accent}"/>
      <stop offset="100%" stop-color="{c_accent_2}"/>
    </linearGradient>
    <pattern id="subtleGrid" width="28" height="28" patternUnits="userSpaceOnUse">
      <path d="M 28 0 L 0 0 0 28" fill="none" stroke="{c_grid}" stroke-width="0.6" stroke-opacity="0.45"/>
    </pattern>
  </defs>
  <style>
    .flow{{stroke-dasharray:5 11;animation:flow 2.4s linear infinite}}
    @keyframes flow{{to{{stroke-dashoffset:-32}}}}
    .pulse{{animation:blink 3s ease-in-out infinite}}
    @keyframes blink{{50%{{opacity:0.4}}}}
    @media(prefers-reduced-motion:reduce){{.flow,.pulse{{animation:none}}}}
  </style>

  <rect width="{w}" height="{h}" rx="16" fill="url(#heroBg)" stroke="{c_border}" stroke-width="1.5"/>
  <rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="15" fill="url(#subtleGrid)"/>

  <!-- Left Identity Column -->
  <rect x="40" y="38" width="24" height="3.5" rx="1.75" fill="url(#brandGrad)"/>
  <text x="74" y="43" font-family="{MONO_FONT}" font-size="10.5" font-weight="600" letter-spacing="1.2" fill="{c_accent}">SOFTWARE · WEB APPS · AI SYSTEMS</text>

  <text x="40" y="94" font-family="{SANS_FONT}" font-size="40" font-weight="800" letter-spacing="-1" fill="{c_text}">Pushpika <tspan fill="url(#brandGrad)">Odisha</tspan></text>
  <text x="40" y="128" font-family="{SANS_FONT}" font-size="15.5" font-weight="500" fill="{c_sub}">Building full-stack web applications, reliable backend</text>
  <text x="40" y="150" font-family="{SANS_FONT}" font-size="15.5" font-weight="500" fill="{c_sub}">software, and practical AI-integrated workflows.</text>

  <!-- Clean Capability Pill -->
  <rect x="40" y="176" width="326" height="26" rx="6" fill="{c_card_alt}" stroke="{c_border_hi}" stroke-width="1"/>
  <text x="54" y="193" font-family="{MONO_FONT}" font-size="10.5" fill="{c_sub}">Node.js · PHP 8 · JavaScript · SQL · AI APIs</text>

  <!-- Bottom Status Strip -->
  <line x1="40" y1="222" x2="520" y2="222" stroke="{c_border}" stroke-width="1"/>
  <circle cx="46" cy="242" r="3.5" fill="{c_emerald}" class="pulse"/>
  <text x="58" y="246" font-family="{MONO_FONT}" font-size="10.5" fill="{c_sub}">Open to Software &amp; Web/AI Engineering Roles</text>
  <text x="520" y="246" text-anchor="end" font-family="{MONO_FONT}" font-size="10.5" fill="{c_muted}">Sri Lanka · @{esc_user}</text>

  <!-- Right System Architecture Bus & Nodes -->
  <path d="M 732 80 H 748 M 834 118 V 132 H 646 V 146 M 732 184 H 748" fill="none" stroke="{c_border_hi}" stroke-width="1.5"/>
  <path class="flow" d="M 732 80 H 748 M 834 118 V 132 H 646 V 146 M 732 184 H 748" fill="none" stroke="{c_accent}" stroke-width="1.6"/>
  {"".join(node_svg)}
  <text x="740" y="246" text-anchor="middle" font-family="{MONO_FONT}" font-size="9.5" letter-spacing="1" fill="{c_muted}">PRODUCTION WEB &amp; AI ARCHITECTURE</text>
</svg>
"""


def render_dashboard(t: dict, m: dict) -> str:
    """Render Bento Capability + Live GitHub Metrics Dashboard SVG (960x245)."""
    w, h = 960, 245
    c_bg1 = t["bg_1"]
    c_bg2 = t["bg_2"]
    c_card = t["card"]
    c_card_alt = t["card_alt"]
    c_border = t["border"]
    c_border_hi = t["border_hi"]
    c_text = t["text"]
    c_sub = t["subtext"]
    c_muted = t["muted"]
    c_accent = t["accent"]
    c_accent_2 = t["accent_2"]
    c_emerald = t["emerald"]
    c_amber = t["amber"]
    c_bar_bg = t["bar_bg"]

    # Left Bento Panel: 3 Engineering Domains
    domains = [
        ("Web Applications", "Responsive UI, SPA/MVC, Real-Time SSE", c_accent, 0.90),
        ("Backend Software", "Node.js APIs, PHP 8.3 OOP, RBAC, Testing", c_accent_2, 0.92),
        ("AI &amp; Knowledge", "Semantic Search, LLM Tooling, Automation", c_emerald, 0.85),
    ]
    domain_svg = []
    for idx, (title, desc, col, ratio) in enumerate(domains):
        dy = 56 + idx * 56
        fill_w = int(316 * ratio)
        domain_svg.append(
            f'<rect x="32" y="{dy}" width="352" height="46" rx="9" fill="{c_card}" stroke="{c_border}" stroke-width="1.2"/>'
            f'<text x="46" y="{dy + 19}" font-family="{SANS_FONT}" font-size="13" font-weight="700" fill="{c_text}">{title}</text>'
            f'<text x="370" y="{dy + 19}" text-anchor="end" font-family="{MONO_FONT}" font-size="9.5" fill="{col}">ACTIVE</text>'
            f'<text x="46" y="{dy + 35}" font-family="{MONO_FONT}" font-size="9.5" fill="{c_muted}">{desc}</text>'
            f'<rect x="32" y="{dy + 43}" width="352" height="3" rx="1.5" fill="{c_bar_bg}"/>'
            f'<rect x="32" y="{dy + 43}" width="{fill_w}" height="3" rx="1.5" fill="{col}"/>'
        )

    # Right Bento Panel: 4 KPIs + Byte-Weighted Language Spectrum
    kpis = [
        ("PUBLIC REPOS", str(m["public_repos"]), c_accent),
        ("CODE VOLUME", f"{m['total_kb']} KB", c_accent_2),
        (
            "YEAR COMMITS" if m["contributions_year"] is not None else "LANGUAGES",
            str(m["contributions_year"] if m["contributions_year"] is not None else m["lang_count"]),
            c_emerald,
        ),
        ("FOLLOWERS", str(m["followers"]), c_amber),
    ]

    kpi_svg = []
    for idx, (label, val, col) in enumerate(kpis):
        kx = 420 + idx * 128
        ky = 56
        kpi_svg.append(
            f'<rect x="{kx}" y="{ky}" width="118" height="58" rx="9" fill="{c_card}" stroke="{c_border}" stroke-width="1.2"/>'
            f'<rect x="{kx}" y="{ky}" width="118" height="2.5" rx="1.2" fill="{col}"/>'
            f'<text x="{kx + 12}" y="{ky + 21}" font-family="{MONO_FONT}" font-size="9" letter-spacing="0.5" fill="{c_muted}">{label}</text>'
            f'<text x="{kx + 12}" y="{ky + 46}" font-family="{SANS_FONT}" font-size="19" font-weight="700" fill="{c_text}">{html.escape(val)}</text>'
        )

    bar_x, bar_y, bar_w = 420, 146, 502
    segments = []
    legend = []
    cursor_x = bar_x
    for idx, (lang, pct) in enumerate(m["top_langs"]):
        col = LANG_COLORS.get(lang, c_accent)
        seg_w = max(round((pct / 100.0) * bar_w), 4)
        if idx == len(m["top_langs"]) - 1:
            seg_w = max(bar_x + bar_w - cursor_x, 4)
        segments.append(f'<rect x="{cursor_x}" y="{bar_y}" width="{seg_w}" height="10" fill="{col}"/>')
        cursor_x += seg_w

        col_idx = idx % 2
        row_idx = idx // 2
        lx = bar_x + col_idx * 256
        ly = 178 + row_idx * 21
        legend.append(
            f'<circle cx="{lx + 5}" cy="{ly - 4}" r="4" fill="{col}"/>'
            f'<text x="{lx + 16}" y="{ly}" font-family="{SANS_FONT}" font-size="12.5" font-weight="600" fill="{c_text}">{html.escape(lang)}</text>'
            f'<text x="{lx + 232}" y="{ly}" text-anchor="end" font-family="{MONO_FONT}" font-size="11.5" fill="{c_muted}">{pct:.1f}%</text>'
        )

    updated = html.escape(m["updated"])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Engineering Capabilities and Live GitHub Metrics">
  <defs>
    <linearGradient id="dashBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{c_bg1}"/>
      <stop offset="100%" stop-color="{c_bg2}"/>
    </linearGradient>
    <clipPath id="dashLangClip">
      <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="10" rx="5"/>
    </clipPath>
  </defs>

  <rect width="{w}" height="{h}" rx="16" fill="url(#dashBg)" stroke="{c_border}" stroke-width="1.5"/>

  <!-- Left Bento Column -->
  <text x="32" y="36" font-family="{MONO_FONT}" font-size="10.5" font-weight="600" letter-spacing="1.1" fill="{c_muted}">CORE ENGINEERING FOCUS</text>
  {"".join(domain_svg)}

  <!-- Center Divider -->
  <line x1="402" y1="24" x2="402" y2="220" stroke="{c_border_hi}" stroke-width="1"/>

  <!-- Right Bento Column -->
  <text x="420" y="36" font-family="{MONO_FONT}" font-size="10.5" font-weight="600" letter-spacing="1.1" fill="{c_muted}">LIVE GITHUB METRICS</text>
  {"".join(kpi_svg)}
  <text x="420" y="135" font-family="{MONO_FONT}" font-size="9.5" letter-spacing="0.8" fill="{c_muted}">LANGUAGE DISTRIBUTION (BY CODE BYTES)</text>
  <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="10" rx="5" fill="{c_bar_bg}"/>
  <g clip-path="url(#dashLangClip)">{"".join(segments)}</g>
  {"".join(legend)}
  <text x="922" y="228" text-anchor="end" font-family="{MONO_FONT}" font-size="10" fill="{c_muted}">Auto-synced via GitHub Actions · {updated}</text>
</svg>
"""


def render_footer(t: dict) -> str:
    """Render clean corporate footer SVG (960x90)."""
    w, h = 960, 90
    c_bg1 = t["bg_1"]
    c_bg2 = t["bg_2"]
    c_border = t["border"]
    c_text = t["text"]
    c_muted = t["muted"]
    c_accent = t["accent"]
    c_accent_2 = t["accent_2"]
    esc_user = html.escape(USERNAME)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Contact Pushpika Odisha">
  <defs>
    <linearGradient id="fBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{c_bg1}"/>
      <stop offset="100%" stop-color="{c_bg2}"/>
    </linearGradient>
    <linearGradient id="fLine" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{c_accent}"/>
      <stop offset="100%" stop-color="{c_accent_2}"/>
    </linearGradient>
  </defs>
  <rect width="{w}" height="{h}" rx="14" fill="url(#fBg)" stroke="{c_border}" stroke-width="1.5"/>
  <rect x="34" y="26" width="4" height="38" rx="2" fill="url(#fLine)"/>
  <text x="52" y="42" font-family="{SANS_FONT}" font-size="15" font-weight="700" fill="{c_text}">Available for Software Engineering, Web Application, and AI Systems projects.</text>
  <text x="52" y="64" font-family="{MONO_FONT}" font-size="11.5" fill="{c_muted}">{EMAIL}  ·  github.com/{esc_user}  ·  Sri Lanka</text>
</svg>
"""


def main() -> None:
    os.makedirs(ASSETS_DIR, exist_ok=True)
    metrics = fetch_metrics()

    outputs = {}
    for mode, theme in THEMES.items():
        outputs[f"hero-{mode}.svg"] = render_hero(theme)
        outputs[f"dashboard-{mode}.svg"] = render_dashboard(theme, metrics)
        outputs[f"footer-{mode}.svg"] = render_footer(theme)

    for filename, content in outputs.items():
        path = os.path.join(ASSETS_DIR, filename)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"Generated {filename}")


if __name__ == "__main__":
    main()
