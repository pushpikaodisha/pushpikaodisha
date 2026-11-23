"""Generate multi-section animated SVGs and auto-sync dynamic projects in README.md."""

from __future__ import annotations

import base64
import html
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone

USERNAME = os.getenv("GITHUB_REPOSITORY_OWNER", "pushpikaodisha")
TOKEN = os.getenv("PROFILE_GH_TOKEN") or os.getenv("GITHUB_TOKEN", "")
EMAIL = "pushpikaodisha.contact@gmail.com"
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")
README_PATH = os.path.join(ROOT_DIR, "README.md")

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
        "violet": "#A855F7",
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
        "violet": "#7C3AED",
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

CURATED_PROJECTS = {
    "neuroscribe-vault": {
        "title": "NeuroScribe Studio",
        "tag": "AI & SEARCH",
        "short": "Semantic vault & FTS5 knowledge graph",
        "desc": "Semantic Markdown knowledge vault and research workspace with SQLite FTS5 indexing and interactive graph exploration.",
        "stack": ["Node.js", "SQLite FTS5", "Semantic Search"],
        "icon": "graph",
        "color": "accent",
        "bullets": [
            "<b>Core:</b> Node.js 22 runtime with zero external search bloat",
            "<b>Indexing:</b> SQLite FTS5 full-text semantic query engine",
            "<b>Visualization:</b> Force-directed document link graph",
        ],
    },
    "apexguild-workflow": {
        "title": "ApexGuild Workflow",
        "tag": "ENTERPRISE SAAS",
        "short": "Multi-tier approval & RBAC state engine",
        "desc": "Enterprise multi-tier approval and state-machine web platform enforcing strict transition invariants and granular RBAC.",
        "stack": ["PHP 8.3 MVC", "SQLite PDO", "RBAC"],
        "icon": "flow",
        "color": "accent_2",
        "bullets": [
            "<b>Backend:</b> PHP 8.3 strict OOP/MVC service architecture",
            "<b>Security:</b> Role-based access control &amp; guarded state transitions",
            "<b>Persistence:</b> Parameterized SQLite PDO storage layer",
        ],
    },
    "omnimesh-telemetry": {
        "title": "OmniMesh Telemetry",
        "tag": "REAL-TIME WEB",
        "short": "Live SSE edge device telemetry platform",
        "desc": "Distributed edge telemetry and automation web orchestrator streaming live device events via Server-Sent Events (SSE).",
        "stack": ["PHP 8.3 MVC", "SSE Streaming", "SQLite PDO"],
        "icon": "stream",
        "color": "emerald",
        "bullets": [
            "<b>Streaming:</b> Real-time SSE push pipeline to web dashboards",
            "<b>Automation:</b> Rule-driven edge event orchestration in PHP 8.3",
            "<b>Storage:</b> Lightweight SQLite PDO event persistence",
        ],
    },
    "polyglot-forge": {
        "title": "PolyglotForge",
        "tag": "API & TESTING",
        "short": "Zero-dep API simulator & chaos testing",
        "desc": "Zero-dependency API contract simulator and chaos engineering workbench built on pure Node.js ESM for resilience testing.",
        "stack": ["Node.js ESM", "API Simulation", "0 NPM Deps"],
        "icon": "shield",
        "color": "amber",
        "bullets": [
            "<b>Runtime:</b> Pure Node.js 22 ESM with 0 NPM dependencies",
            "<b>Resilience:</b> Deterministic fault injection &amp; latency simulation",
            "<b>Purpose:</b> Validates API contract behavior under failure modes",
        ],
    },
    "chronoledger-vault": {
        "title": "ChronoLedger Vault",
        "tag": "AUDIT SECURITY",
        "short": "RFC 6962 Merkle cryptographic notary",
        "desc": "Tamper-evident document notary and cryptographic audit system implementing RFC 6962 Merkle Tree verification proofs.",
        "stack": ["Node.js", "RFC 6962 Merkle", "0 NPM Deps"],
        "icon": "lock",
        "color": "violet",
        "bullets": [
            "<b>Cryptography:</b> RFC 6962 Merkle Tree inclusion &amp; consistency proofs",
            "<b>Footprint:</b> Zero external NPM dependencies on Node.js 22",
            "<b>Use Case:</b> Verifiable audit trails for critical records",
        ],
    },
    "basic-website": {
        "title": "Responsive Web Systems",
        "tag": "WEB SYSTEMS",
        "short": "Multi-theme modular web architecture",
        "desc": "Modern responsive web application architecture with adaptive dark/light theming, modular CSS layouts, and accessible UI state.",
        "stack": ["HTML5", "CSS3", "JavaScript ES6+"],
        "icon": "ui",
        "color": "accent",
        "bullets": [
            "<b>Frontend:</b> Semantic HTML5, modular CSS3, Vanilla ES6+",
            "<b>UX:</b> Adaptive Dark/Light theme switching &amp; mobile layout",
            "<b>Performance:</b> Clean zero-framework bundle delivery",
        ],
    },
    "binaural-flow-studio": {
        "title": "Binaural Flow Studio",
        "tag": "WEB AUDIO APP",
        "short": "Web Audio synthesizer & spatial sound",
        "desc": "Interactive browser audio synthesizer and spatial sound visualization app powered by the Web Audio API.",
        "stack": ["Web Audio API", "HTML5", "JavaScript"],
        "icon": "stream",
        "color": "accent",
        "bullets": [
            "<b>Audio Engine:</b> Real-time browser synthesis using Web Audio API",
            "<b>Spatial:</b> HRTF 3D binaural panning &amp; acoustic visualization",
        ],
    },
    "chronoforge-4d": {
        "title": "ChronoForge 4D",
        "tag": "INTERACTIVE UI",
        "short": "Browser geometric projection engine",
        "desc": "Browser-based 3D/4D geometric projection engine with responsive touch and mobile sensor controls.",
        "stack": ["HTML5 Canvas", "JavaScript", "Geometry"],
        "icon": "graph",
        "color": "violet",
        "bullets": [
            "<b>Rendering:</b> Smooth HTML5 Canvas 2D/3D real-time projection",
            "<b>Input:</b> Desktop controls &amp; mobile gyroscope integration",
        ],
    },
    "bioswarm-genesis": {
        "title": "BioSwarm Genesis",
        "tag": "WEB SIMULATION",
        "short": "60 FPS neural-perceptron web engine",
        "desc": "Real-time 60 FPS browser simulation driven by lightweight neural-perceptron agents in Vanilla ES6+.",
        "stack": ["JavaScript ES6+", "HTML5 Canvas", "AI Agents"],
        "icon": "graph",
        "color": "emerald",
        "bullets": [
            "<b>Simulation:</b> 60 FPS HTML5 Canvas agent ecosystem loop",
            "<b>AI Logic:</b> Lightweight neural-perceptron decision engine",
        ],
    },
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


def truncate(text: str, limit: int) -> str:
    """Shorten text cleanly to fit inside fixed-width SVG slots."""
    clean = " ".join(text.split())
    if len(clean) <= limit:
        return clean
    return clean[: max(limit - 1, 1)].rstrip() + "…"


def fetch_repo_readme_summary(repo_name: str) -> tuple[str | None, str | None]:
    """Fetch title and subtitle/description from a repo's README if GitHub description is empty."""
    try:
        data = gh_get(f"https://api.github.com/repos/{USERNAME}/{repo_name}/readme")
        if not isinstance(data, dict) or not data.get("content"):
            return None, None
        raw = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
        title = None
        summary = None
        for line in raw.splitlines():
            s = line.strip()
            if not s or s.startswith("![") or s.startswith("[![") or s.startswith("<"):
                continue
            if s.startswith("# ") and not title:
                title = s[2:].strip()
            elif s.startswith("### ") and not summary:
                summary = s[4:].strip()
                break
            elif not s.startswith("#") and not summary:
                summary = s
                break
        return title, summary
    except (urllib.error.URLError, TimeoutError, ValueError):
        return None, None


def infer_visual_meta(name: str, desc: str, lang: str, topics: list[str]) -> tuple[str, str, str]:
    """Pick tag, icon key, and theme color key for newly discovered public repositories."""
    haystack = f"{name} {desc} {lang} {' '.join(topics)}".lower()
    if any(k in haystack for k in ("ai", "llm", "rag", "ml", "agent", "neural", "search", "graph")):
        return "AI & SOFTWARE", "graph", "emerald"
    if any(k in haystack for k in ("api", "test", "cli", "sdk", "node", "express", "nest")):
        return "BACKEND & API", "shield", "amber"
    if any(k in haystack for k in ("crypto", "auth", "vault", "merkle", "security", "ledger")):
        return "SECURITY & DATA", "lock", "violet"
    if any(k in haystack for k in ("stream", "iot", "telemetry", "realtime", "socket", "sse")):
        return "REAL-TIME SYSTEM", "stream", "emerald"
    if lang.lower() == "php" or any(k in haystack for k in ("workflow", "saas", "admin", "laravel")):
        return "WEB PLATFORM", "flow", "accent_2"
    return "WEB APPLICATION", "ui", "accent"


def build_dynamic_projects(non_forks: list[dict], pinned_names: list[str]) -> list[dict]:
    """Select top 6 live public projects: featured/pinned first, then newest pushed active repos."""
    candidates = []
    for repo in non_forks:
        name = repo.get("name", "")
        topics = [t.lower() for t in (repo.get("topics") or [])]
        if "ignore" in topics or "archived" in topics:
            continue
        size = int(repo.get("size", 0))
        has_desc = bool((repo.get("description") or "").strip())
        # Skip empty placeholder repos unless explicitly marked featured/pinned
        if size < 5 and not has_desc and "featured" not in topics and name.lower() not in pinned_names:
            continue
        candidates.append(repo)

    def sort_key(r: dict) -> tuple[int, int, str]:
        rname = r.get("name", "").lower()
        topics = [t.lower() for t in (r.get("topics") or [])]
        is_featured = 1 if ("featured" in topics or rname in pinned_names) else 0
        pushed = r.get("pushed_at") or ""
        return (is_featured, 1 if r.get("stargazers_count", 0) > 0 else 0, pushed)

    ordered = sorted(candidates, key=sort_key, reverse=True)[:6]

    resolved = []
    for repo in ordered:
        rname = repo.get("name", "")
        key = rname.lower()
        lang = repo.get("language") or "Web"
        topics = repo.get("topics") or []
        pushed_date = (repo.get("pushed_at") or "")[:10] or "Active"
        url = repo.get("html_url") or f"https://github.com/{USERNAME}/{rname}"
        curated = CURATED_PROJECTS.get(key)

        if curated:
            resolved.append({
                "repo": rname,
                "url": url,
                "title": curated["title"],
                "tag": curated["tag"],
                "short": curated["short"],
                "desc": curated["desc"],
                "stack": curated["stack"],
                "icon": curated["icon"],
                "color": curated["color"],
                "bullets": curated.get("bullets", []),
                "updated": pushed_date,
                "lang": lang,
            })
        else:
            gh_desc = (repo.get("description") or "").strip()
            readme_title, readme_summary = (None, None)
            if not gh_desc:
                readme_title, readme_summary = fetch_repo_readme_summary(rname)
            pretty_title = readme_title or rname.replace("-", " ").replace("_", " ").title()
            full_desc = gh_desc or readme_summary or f"Public {lang} software project hosted on GitHub."
            tag, icon_key, color_key = infer_visual_meta(rname, full_desc, lang, topics)
            stack_tags = [lang] + [t.replace("-", " ").title() for t in topics[:2]]
            if len(stack_tags) < 2:
                stack_tags.append("GitHub")

            resolved.append({
                "repo": rname,
                "url": url,
                "title": truncate(pretty_title, 22),
                "tag": tag,
                "short": truncate(full_desc, 40),
                "desc": full_desc,
                "stack": stack_tags[:3],
                "icon": icon_key,
                "color": color_key,
                "bullets": [
                    f"<b>Repository:</b> <code>{html.escape(rname)}</code>",
                    f"<b>Primary Language:</b> {html.escape(lang)}",
                    f"<b>Last Updated:</b> {html.escape(pushed_date)}",
                ],
                "updated": pushed_date,
                "lang": lang,
            })

    return resolved


def fetch_metrics() -> dict:
    """Fetch public profile, live projects, repository footprint, and activity metrics."""
    user = gh_get(f"https://api.github.com/users/{USERNAME}")
    repos = gh_get(f"https://api.github.com/users/{USERNAME}/repos?sort=pushed&per_page=100&type=owner")

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

    top_repos = sorted(non_forks, key=lambda r: int(r.get("size", 0)), reverse=True)[:5]
    repo_sizes = [
        (
            r.get("name", "repo"),
            max(int(r.get("size", 1)), 1),
            r.get("language") or "Web",
        )
        for r in top_repos
    ]

    pulse = [2, 4, 3, 6, 5, 8, 7, 10, 9, 12, 11, 14]
    try:
        events = gh_get(f"https://api.github.com/users/{USERNAME}/events/public?per_page=60")
        if isinstance(events, list) and events:
            buckets = [0] * 12
            for idx, ev in enumerate(events):
                b = min(11, (idx * 12) // max(len(events), 1))
                buckets[11 - b] += 2 if ev.get("type") == "PushEvent" else 1
            if max(buckets) > 0:
                pulse = buckets
    except (urllib.error.URLError, TimeoutError):
        pass

    contributions_year = None
    pinned_names: list[str] = []
    gql = """
    query($login: String!) {
      user(login: $login) {
        pinnedItems(first: 6, types: REPOSITORY) {
          nodes {
            ... on Repository { name }
          }
        }
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
        u_obj = gql_data["user"]
        contributions_year = (
            u_obj.get("contributionsCollection", {})
            .get("contributionCalendar", {})
            .get("totalContributions")
        )
        for node in (u_obj.get("pinnedItems") or {}).get("nodes") or []:
            if node and node.get("name"):
                pinned_names.append(node["name"].lower())

    featured_projects = build_dynamic_projects(non_forks, pinned_names)

    return {
        "public_repos": int(user.get("public_repos", len(repos))),
        "lang_count": len(top_langs),
        "stars": stars,
        "followers": int(user.get("followers", 0)),
        "contributions_year": contributions_year,
        "top_langs": top_langs,
        "repo_sizes": repo_sizes,
        "pulse": pulse,
        "featured_projects": featured_projects,
        "total_kb": round(total_bytes / 1024),
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


def render_hero(t: dict) -> str:
    """Section 1: Animated Software, Web & AI Systems Hero (960x285)."""
    w, h = 960, 285
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

    nodes = [
        (552, 54, "01 · WEB CLIENT", "Responsive UI &amp; Apps", "HTML5 · JS · SSE Streams", c_accent, "p1"),
        (742, 54, "02 · API &amp; CORE", "Backend Services", "Node.js · PHP 8 · RBAC", c_accent_2, "p2"),
        (552, 152, "03 · AI &amp; SEARCH", "Intelligent Workflows", "LLM APIs · FTS5 · Graphs", c_emerald, "p3"),
        (742, 152, "04 · DATA LAYER", "Storage &amp; Proofs", "SQLite PDO · Merkle Audit", c_accent, "p4"),
    ]

    node_svg = []
    for nx, ny, tag, title, sub, col, cls in nodes:
        node_svg.append(
            f'<rect x="{nx}" y="{ny}" width="174" height="76" rx="10" fill="{c_card}" stroke="{c_border_hi}" stroke-width="1.2"/>'
            f'<rect x="{nx}" y="{ny}" width="174" height="2.5" rx="1.2" fill="{col}"/>'
            f'<circle cx="{nx + 159}" cy="{ny + 18}" r="3" fill="{col}" class="pulse {cls}"/>'
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
    .flow{{stroke-dasharray:5 11;animation:flow 2.2s linear infinite}}
    @keyframes flow{{to{{stroke-dashoffset:-32}}}}
    .pulse{{animation:blink 3s ease-in-out infinite}}
    .p2{{animation-delay:0.6s}}.p3{{animation-delay:1.2s}}.p4{{animation-delay:1.8s}}
    @keyframes blink{{50%{{opacity:0.3}}}}
    .wave{{stroke-dasharray:120;animation:wave 4s ease-in-out infinite}}
    @keyframes wave{{0%{{stroke-dashoffset:120}}50%,100%{{stroke-dashoffset:0}}}}
    @media(prefers-reduced-motion:reduce){{.flow,.pulse,.wave{{animation:none}}}}
  </style>

  <rect width="{w}" height="{h}" rx="16" fill="url(#heroBg)" stroke="{c_border}" stroke-width="1.5"/>
  <rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="15" fill="url(#subtleGrid)"/>

  <rect x="40" y="38" width="24" height="3.5" rx="1.75" fill="url(#brandGrad)"/>
  <text x="74" y="43" font-family="{MONO_FONT}" font-size="10.5" font-weight="600" letter-spacing="1.2" fill="{c_accent}">SOFTWARE · WEB APPS · AI SYSTEMS</text>

  <text x="40" y="96" font-family="{SANS_FONT}" font-size="41" font-weight="800" letter-spacing="-1" fill="{c_text}">Pushpika <tspan fill="url(#brandGrad)">Odisha</tspan></text>
  <text x="40" y="131" font-family="{SANS_FONT}" font-size="15.5" font-weight="500" fill="{c_sub}">Building full-stack web applications, reliable backend</text>
  <text x="40" y="153" font-family="{SANS_FONT}" font-size="15.5" font-weight="500" fill="{c_sub}">software, and practical AI-integrated workflows.</text>

  <rect x="40" y="180" width="332" height="27" rx="6" fill="{c_card_alt}" stroke="{c_border_hi}" stroke-width="1"/>
  <text x="54" y="197" font-family="{MONO_FONT}" font-size="10.5" fill="{c_sub}">Node.js · PHP 8 · JavaScript · SQL · AI APIs</text>

  <line x1="40" y1="234" x2="520" y2="234" stroke="{c_border}" stroke-width="1"/>
  <circle cx="46" cy="256" r="3.5" fill="{c_emerald}" class="pulse"/>
  <text x="58" y="260" font-family="{MONO_FONT}" font-size="10.5" fill="{c_sub}">Open to Software, Web &amp; AI Engineering Roles</text>
  <text x="520" y="260" text-anchor="end" font-family="{MONO_FONT}" font-size="10.5" fill="{c_muted}">Sri Lanka · @{esc_user}</text>

  <text x="552" y="38" font-family="{MONO_FONT}" font-size="9.5" letter-spacing="1" fill="{c_muted}">REQUEST PIPELINE</text>
  <path d="M 800 36 L 814 31 L 828 38 L 842 28 L 856 35 L 870 25 L 884 32 L 898 26 L 914 30" fill="none" stroke="{c_emerald}" stroke-width="1.6" class="wave"/>

  <path d="M 726 92 H 742 M 829 130 V 141 H 639 V 152 M 726 190 H 742" fill="none" stroke="{c_border_hi}" stroke-width="1.5"/>
  <path class="flow" d="M 726 92 H 742 M 829 130 V 141 H 639 V 152 M 726 190 H 742" fill="none" stroke="{c_accent}" stroke-width="1.7"/>
  {"".join(node_svg)}
  <text x="734" y="260" text-anchor="middle" font-family="{MONO_FONT}" font-size="9.5" letter-spacing="0.9" fill="{c_muted}">PRODUCTION WEB &amp; AI ARCHITECTURE</text>
</svg>
"""


def render_lifecycle(t: dict) -> str:
    """Section 2: 4-Stage Animated Engineering Lifecycle Diagram (960x185)."""
    w, h = 960, 185
    c_bg1 = t["bg_1"]
    c_bg2 = t["bg_2"]
    c_card = t["card"]
    c_border = t["border"]
    c_border_hi = t["border_hi"]
    c_text = t["text"]
    c_muted = t["muted"]
    c_accent = t["accent"]
    c_accent_2 = t["accent_2"]
    c_emerald = t["emerald"]
    c_amber = t["amber"]

    stages = [
        ("01 · ARCHITECT", "Domain &amp; API Design", "Contracts, schemas, RBAC", c_accent, "s1"),
        ("02 · ENGINEER", "Web &amp; Backend Code", "Node.js ESM, PHP 8.3 MVC", c_accent_2, "s2"),
        ("03 · INTEGRATE AI", "Search &amp; Automation", "FTS5, LLM APIs, contexts", c_emerald, "s3"),
        ("04 · VERIFY &amp; SHIP", "Resilience &amp; CI/CD", "Chaos tests, Merkle proofs", c_amber, "s4"),
    ]

    cards = []
    for idx, (step, title, sub, col, cls) in enumerate(stages):
        x = 28 + idx * 232
        cards.append(
            f'<rect x="{x}" y="52" width="210" height="106" rx="11" fill="{c_card}" stroke="{c_border_hi}" stroke-width="1.2"/>'
            f'<rect x="{x}" y="52" width="210" height="3" rx="1.5" fill="{col}"/>'
            f'<circle cx="{x + 193}" cy="70" r="3" fill="{col}" class="step {cls}"/>'
            f'<text x="{x + 15}" y="74" font-family="{MONO_FONT}" font-size="9.5" font-weight="700" letter-spacing="0.6" fill="{col}">{step}</text>'
            f'<text x="{x + 15}" y="103" font-family="{SANS_FONT}" font-size="14.5" font-weight="700" fill="{c_text}">{title}</text>'
            f'<text x="{x + 15}" y="126" font-family="{MONO_FONT}" font-size="10" fill="{c_muted}">{sub}</text>'
            f'<rect x="{x + 15}" y="140" width="180" height="3" rx="1.5" fill="{c_border}"/>'
            f'<rect x="{x + 15}" y="140" width="180" height="3" rx="1.5" fill="{col}" class="bar {cls}"/>'
        )

    wires = (
        f'<path d="M 238 105 H 260 M 470 105 H 492 M 702 105 H 724" fill="none" stroke="{c_border_hi}" stroke-width="1.5"/>'
        f'<path class="flow" d="M 238 105 H 260 M 470 105 H 492 M 702 105 H 724" fill="none" stroke="{c_accent}" stroke-width="1.8"/>'
    )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="4-Stage Software and AI Engineering Lifecycle">
  <defs>
    <linearGradient id="lifeBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{c_bg1}"/>
      <stop offset="100%" stop-color="{c_bg2}"/>
    </linearGradient>
  </defs>
  <style>
    .flow{{stroke-dasharray:4 8;animation:flow 1.8s linear infinite}}
    @keyframes flow{{to{{stroke-dashoffset:-24}}}}
    .step{{animation:pulse 4s ease-in-out infinite}}
    .s2{{animation-delay:1s}}.s3{{animation-delay:2s}}.s4{{animation-delay:3s}}
    @keyframes pulse{{0%,100%{{opacity:0.35}}50%{{opacity:1}}}}
    .bar{{transform-origin:left center;animation:grow 8s ease-in-out infinite}}
    @keyframes grow{{0%,100%{{opacity:0.45}}50%{{opacity:1}}}}
    @media(prefers-reduced-motion:reduce){{.flow,.step,.bar{{animation:none}}}}
  </style>
  <rect width="{w}" height="{h}" rx="16" fill="url(#lifeBg)" stroke="{c_border}" stroke-width="1.5"/>
  <text x="28" y="34" font-family="{MONO_FONT}" font-size="10.5" font-weight="600" letter-spacing="1.1" fill="{c_muted}">ENGINEERING WORKFLOW · FROM SPECIFICATION TO PRODUCTION</text>
  {wires}
  {"".join(cards)}
</svg>
"""


def render_projects(t: dict, projects: list[dict], updated: str) -> str:
    """Section 3: Dynamic 3x2 Showcase of Latest/Featured Public Repos (960x312)."""
    w, h = 960, 312
    c_bg1 = t["bg_1"]
    c_bg2 = t["bg_2"]
    c_card = t["card"]
    c_card_alt = t["card_alt"]
    c_border = t["border"]
    c_border_hi = t["border_hi"]
    c_text = t["text"]
    c_sub = t["subtext"]
    c_muted = t["muted"]

    icons = {
        "graph": '<circle cx="6" cy="18" r="2.5"/><circle cx="18" cy="18" r="2.5"/><circle cx="12" cy="6" r="2.5"/><path d="M7.5 16L11 8M16.5 16L13 8M8.5 18H15.5"/>',
        "flow": '<rect x="3" y="4" width="7" height="5" rx="1.5"/><rect x="14" y="15" width="7" height="5" rx="1.5"/><path d="M10 6.5H16V15M14 13L16 15L18 13"/>',
        "stream": '<path d="M3 14L7 10L11 15L16 7L21 12"/><circle cx="21" cy="12" r="2"/>',
        "shield": '<path d="M12 3L4 6.5V12C4 16.8 7.4 20.4 12 21.5C16.6 20.4 20 16.8 20 12V6.5L12 3Z"/><path d="M9 12L11 14L15 10"/>',
        "lock": '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8A4 4 0 0 1 16 8V11"/>',
        "ui": '<rect x="3" y="4" width="18" height="15" rx="2"/><path d="M3 9H21M9 9V19"/>',
    }

    cards = []
    for idx, proj in enumerate(projects[:6]):
        col_i = idx % 3
        row_i = idx // 3
        x = 28 + col_i * 308
        y = 52 + row_i * 124
        col = t.get(proj["color"], t["accent"])
        icon_svg = icons.get(proj["icon"], icons["ui"])
        tag = html.escape(f"{idx + 1:02d} · {proj['tag']}")
        title = html.escape(truncate(proj["title"], 22))
        desc = html.escape(truncate(proj["short"], 40))
        stack_str = html.escape(truncate(" · ".join(proj["stack"][:2]), 26))
        pushed = html.escape(proj["updated"])

        cards.append(
            f'<rect x="{x}" y="{y}" width="288" height="110" rx="11" fill="{c_card}" stroke="{c_border_hi}" stroke-width="1.2"/>'
            f'<rect x="{x}" y="{y}" width="288" height="2.5" rx="1.2" fill="{col}"/>'
            f'<rect x="{x + 14}" y="{y + 14}" width="30" height="30" rx="7" fill="{c_card_alt}" stroke="{c_border}" stroke-width="1"/>'
            f'<g transform="translate({x + 17}, {y + 17})" fill="none" stroke="{col}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{icon_svg}</g>'
            f'<text x="{x + 54}" y="{y + 26}" font-family="{MONO_FONT}" font-size="9" font-weight="700" letter-spacing="0.5" fill="{col}">{tag}</text>'
            f'<circle cx="{x + 271}" cy="{y + 22}" r="3" fill="{col}" class="dot"/>'
            f'<text x="{x + 54}" y="{y + 44}" font-family="{SANS_FONT}" font-size="14.5" font-weight="700" fill="{c_text}">{title}</text>'
            f'<text x="{x + 14}" y="{y + 68}" font-family="{SANS_FONT}" font-size="11.5" fill="{c_sub}">{desc}</text>'
            f'<rect x="{x + 14}" y="{y + 80}" width="182" height="20" rx="5" fill="{c_card_alt}" stroke="{c_border}" stroke-width="1"/>'
            f'<text x="{x + 22}" y="{y + 93.5}" font-family="{MONO_FONT}" font-size="9.5" fill="{c_muted}">{stack_str}</text>'
            f'<text x="{x + 274}" y="{y + 93.5}" text-anchor="end" font-family="{MONO_FONT}" font-size="9" fill="{c_muted}">{pushed}</text>'
        )

    esc_upd = html.escape(updated)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Auto-Synced Public Projects Showcase">
  <defs>
    <linearGradient id="projBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{c_bg1}"/>
      <stop offset="100%" stop-color="{c_bg2}"/>
    </linearGradient>
  </defs>
  <style>
    .dot{{animation:blink 3.2s ease-in-out infinite}}
    @keyframes blink{{50%{{opacity:0.35}}}}
    @media(prefers-reduced-motion:reduce){{.dot{{animation:none}}}}
  </style>
  <rect width="{w}" height="{h}" rx="16" fill="url(#projBg)" stroke="{c_border}" stroke-width="1.5"/>
  <text x="28" y="34" font-family="{MONO_FONT}" font-size="10.5" font-weight="600" letter-spacing="1.1" fill="{c_muted}">LATEST PUBLIC PLATFORMS · AUTO-SYNCED</text>
  <text x="932" y="34" text-anchor="end" font-family="{MONO_FONT}" font-size="10" fill="{c_muted}">LIVE REPO FEED · {esc_upd}</text>
  {"".join(cards)}
</svg>
"""


def render_stack(t: dict) -> str:
    """Section 4: 4-Column Vector Tech & AI Stack Matrix (960x235)."""
    w, h = 960, 235
    c_bg1 = t["bg_1"]
    c_bg2 = t["bg_2"]
    c_card = t["card"]
    c_card_alt = t["card_alt"]
    c_border = t["border"]
    c_border_hi = t["border_hi"]
    c_sub = t["subtext"]
    c_muted = t["muted"]
    c_accent = t["accent"]
    c_accent_2 = t["accent_2"]
    c_emerald = t["emerald"]
    c_amber = t["amber"]

    columns = [
        ("WEB &amp; FRONTEND", c_accent, ["JavaScript (ES6+)", "HTML5 &amp; CSS3", "Responsive UI", "Server-Sent Events", "Browser Web APIs"]),
        ("BACKEND &amp; SOFTWARE", c_accent_2, ["Node.js (ESM)", "PHP 8.3 OOP / MVC", "RESTful APIs", "State Machines", "RBAC Auth"]),
        ("AI &amp; KNOWLEDGE", c_emerald, ["LLM API Integration", "Prompt Engineering", "SQLite FTS5 Search", "Knowledge Graphs", "Workflow Agents"]),
        ("DATA &amp; DEVOPS", c_amber, ["SQLite PDO &amp; SQL", "RFC 6962 Merkle", "Chaos / API Testing", "GitHub Actions CI", "Git &amp; Versioning"]),
    ]

    col_svg = []
    for idx, (heading, col, skills) in enumerate(columns):
        x = 28 + idx * 232
        pills = []
        for s_idx, skill in enumerate(skills):
            py = 88 + s_idx * 23
            pills.append(
                f'<rect x="{x + 14}" y="{py}" width="182" height="19" rx="4.5" fill="{c_card_alt}" stroke="{c_border}" stroke-width="0.9"/>'
                f'<circle cx="{x + 24}" cy="{py + 9.5}" r="2.2" fill="{col}"/>'
                f'<text x="{x + 33}" y="{py + 13}" font-family="{MONO_FONT}" font-size="10" fill="{c_sub}">{skill}</text>'
            )

        col_svg.append(
            f'<rect x="{x}" y="52" width="210" height="162" rx="11" fill="{c_card}" stroke="{c_border_hi}" stroke-width="1.2"/>'
            f'<rect x="{x}" y="52" width="210" height="3" rx="1.5" fill="{col}"/>'
            f'<text x="{x + 14}" y="76" font-family="{MONO_FONT}" font-size="10" font-weight="700" letter-spacing="0.7" fill="{col}">{heading}</text>'
            f'{"".join(pills)}'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Technology and AI Engineering Stack Matrix">
  <defs>
    <linearGradient id="stackBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{c_bg1}"/>
      <stop offset="100%" stop-color="{c_bg2}"/>
    </linearGradient>
  </defs>
  <rect width="{w}" height="{h}" rx="16" fill="url(#stackBg)" stroke="{c_border}" stroke-width="1.5"/>
  <text x="28" y="34" font-family="{MONO_FONT}" font-size="10.5" font-weight="600" letter-spacing="1.1" fill="{c_muted}">TECHNOLOGY &amp; AI CAPABILITY MATRIX</text>
  {"".join(col_svg)}
</svg>
"""


def render_dashboard(t: dict, m: dict) -> str:
    """Section 5: Advanced Live GitHub Observatory (960x302)."""
    w, h = 960, 302
    c_bg1 = t["bg_1"]
    c_bg2 = t["bg_2"]
    c_card = t["card"]
    c_border = t["border"]
    c_text = t["text"]
    c_sub = t["subtext"]
    c_muted = t["muted"]
    c_accent = t["accent"]
    c_accent_2 = t["accent_2"]
    c_emerald = t["emerald"]
    c_amber = t["amber"]
    c_bar_bg = t["bar_bg"]

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
        kx = 28 + idx * 232
        ky = 50
        kpi_svg.append(
            f'<rect x="{kx}" y="{ky}" width="210" height="56" rx="9" fill="{c_card}" stroke="{c_border}" stroke-width="1.2"/>'
            f'<rect x="{kx}" y="{ky}" width="210" height="2.5" rx="1.2" fill="{col}"/>'
            f'<text x="{kx + 14}" y="{ky + 20}" font-family="{MONO_FONT}" font-size="9.5" letter-spacing="0.6" fill="{c_muted}">{label}</text>'
            f'<text x="{kx + 14}" y="{ky + 44}" font-family="{SANS_FONT}" font-size="20" font-weight="700" fill="{c_text}">{html.escape(val)}</text>'
        )

    max_kb = max((sz for _, sz, _ in m["repo_sizes"]), default=1)
    repo_bars = []
    for idx, (rname, rkb, rlang) in enumerate(m["repo_sizes"]):
        ry = 160 + idx * 24
        bar_w = max(14, int((rkb / max_kb) * 185))
        rcol = LANG_COLORS.get(rlang, c_accent)
        short_name = rname[:22]
        repo_bars.append(
            f'<text x="42" y="{ry}" font-family="{MONO_FONT}" font-size="10.5" fill="{c_sub}">{html.escape(short_name)}</text>'
            f'<rect x="206" y="{ry - 8}" width="185" height="7" rx="3.5" fill="{c_bar_bg}"/>'
            f'<rect x="206" y="{ry - 8}" width="{bar_w}" height="7" rx="3.5" fill="{rcol}"/>'
            f'<text x="454" y="{ry}" text-anchor="end" font-family="{MONO_FONT}" font-size="10" fill="{c_muted}">{rkb} KB</text>'
        )

    bar_x, bar_y, bar_w = 504, 152, 418
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
        lx = bar_x + col_idx * 214
        ly = 182 + row_idx * 20
        legend.append(
            f'<circle cx="{lx + 5}" cy="{ly - 4}" r="3.8" fill="{col}"/>'
            f'<text x="{lx + 15}" y="{ly}" font-family="{SANS_FONT}" font-size="12" font-weight="600" fill="{c_text}">{html.escape(lang)}</text>'
            f'<text x="{lx + 196}" y="{ly}" text-anchor="end" font-family="{MONO_FONT}" font-size="11" fill="{c_muted}">{pct:.1f}%</text>'
        )

    max_p = max(m["pulse"]) or 1
    spark_pts = []
    for idx, val in enumerate(m["pulse"]):
        sx = 504 + idx * 38
        sy = 266 - int((val / max_p) * 26)
        spark_pts.append(f"{sx},{sy}")
    spark_line = " ".join(spark_pts)
    spark_area = f"504,270 {spark_line} {504 + (len(m['pulse']) - 1) * 38},270"

    updated = html.escape(m["updated"])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Live GitHub Engineering Observatory">
  <defs>
    <linearGradient id="dashBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{c_bg1}"/>
      <stop offset="100%" stop-color="{c_bg2}"/>
    </linearGradient>
    <linearGradient id="sparkFill" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{c_accent}" stop-opacity="0.32"/>
      <stop offset="100%" stop-color="{c_accent}" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="dashLangClip">
      <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="10" rx="5"/>
    </clipPath>
  </defs>

  <rect width="{w}" height="{h}" rx="16" fill="url(#dashBg)" stroke="{c_border}" stroke-width="1.5"/>
  <text x="28" y="34" font-family="{MONO_FONT}" font-size="10.5" font-weight="600" letter-spacing="1.1" fill="{c_muted}">LIVE GITHUB OBSERVATORY</text>
  <text x="932" y="34" text-anchor="end" font-family="{MONO_FONT}" font-size="10" fill="{c_muted}">SYNCED {updated}</text>
  {"".join(kpi_svg)}

  <rect x="28" y="122" width="442" height="158" rx="11" fill="{c_card}" stroke="{c_border}" stroke-width="1.2"/>
  <text x="42" y="142" font-family="{MONO_FONT}" font-size="9.5" font-weight="600" letter-spacing="0.8" fill="{c_muted}">TOP REPOSITORIES BY FOOTPRINT</text>
  {"".join(repo_bars)}

  <rect x="488" y="122" width="444" height="158" rx="11" fill="{c_card}" stroke="{c_border}" stroke-width="1.2"/>
  <text x="504" y="142" font-family="{MONO_FONT}" font-size="9.5" font-weight="600" letter-spacing="0.8" fill="{c_muted}">LANGUAGE DISTRIBUTION (BY CODE BYTES)</text>
  <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="10" rx="5" fill="{c_bar_bg}"/>
  <g clip-path="url(#dashLangClip)">{"".join(segments)}</g>
  {"".join(legend)}
  <text x="504" y="232" font-family="{MONO_FONT}" font-size="9" letter-spacing="0.7" fill="{c_muted}">PUBLIC ACTIVITY PULSE</text>
  <polygon points="{spark_area}" fill="url(#sparkFill)"/>
  <polyline points="{spark_line}" fill="none" stroke="{c_accent}" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/>
</svg>
"""


def render_footer(t: dict) -> str:
    """Section 6: Animated Connect & Signature Banner (960x96)."""
    w, h = 960, 96
    c_bg1 = t["bg_1"]
    c_bg2 = t["bg_2"]
    c_border = t["border"]
    c_text = t["text"]
    c_muted = t["muted"]
    c_accent = t["accent"]
    c_accent_2 = t["accent_2"]
    c_emerald = t["emerald"]
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
  <style>
    .beacon{{animation:blink 2.8s ease-in-out infinite}}
    @keyframes blink{{50%{{opacity:0.3}}}}
    @media(prefers-reduced-motion:reduce){{.beacon{{animation:none}}}}
  </style>
  <rect width="{w}" height="{h}" rx="14" fill="url(#fBg)" stroke="{c_border}" stroke-width="1.5"/>
  <rect x="34" y="28" width="4" height="40" rx="2" fill="url(#fLine)"/>
  <text x="52" y="44" font-family="{SANS_FONT}" font-size="15.5" font-weight="700" fill="{c_text}">Available for Software Engineering, Web Application, and AI Systems roles.</text>
  <text x="52" y="67" font-family="{MONO_FONT}" font-size="11.5" fill="{c_muted}">{EMAIL}  ·  github.com/{esc_user}  ·  Sri Lanka</text>
  <circle cx="914" cy="48" r="4" fill="{c_emerald}" class="beacon"/>
</svg>
"""


def build_projects_table_html(projects: list[dict]) -> str:
    """Build the 2-column HTML project showcase table synced into README.md."""
    rows = []
    for i in range(0, len(projects), 2):
        cells = []
        for j in (0, 1):
            if i + j >= len(projects):
                cells.append('<td width="50%" valign="top"></td>')
                continue
            p = projects[i + j]
            num = f"{i + j + 1:02d}"
            title = html.escape(p["title"])
            url = html.escape(p["url"])
            desc = html.escape(p["desc"])
            tags = " ".join(f"<code>{html.escape(s)}</code>" for s in p["stack"])
            details_block = ""
            if p["bullets"]:
                bullets = "".join(f"\n          <li>{b}</li>" for b in p["bullets"])
                details_block = f"""
      <details>
        <summary><sub><b>Architecture &amp; Details</b> · Updated {html.escape(p['updated'])}</sub></summary>
        <br />
        <ul>{bullets}
        </ul>
      </details>"""
            cells.append(
                f"""    <td width="50%" valign="top">
      <h4>{num} · <a href="{url}">{title} ↗</a></h4>
      <p>{desc}</p>
      <p>{tags}</p>{details_block}
    </td>"""
            )
        rows.append("  <tr>\n" + "\n".join(cells) + "\n  </tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def sync_readme_projects(projects: list[dict]) -> None:
    """Update the <!-- PROJECTS:START --> ... <!-- PROJECTS:END --> block in README.md."""
    if not os.path.exists(README_PATH):
        return
    with open(README_PATH, "r", encoding="utf-8") as f:
        original = f.read()

    pattern = re.compile(r"<!-- PROJECTS:START -->.*?<!-- PROJECTS:END -->", re.DOTALL)
    if not pattern.search(original):
        return

    table_html = build_projects_table_html(projects)
    replacement = f"<!-- PROJECTS:START -->\n{table_html}\n<!-- PROJECTS:END -->"
    updated = pattern.sub(replacement, original)
    if updated != original:
        with open(README_PATH, "w", encoding="utf-8", newline="\n") as f:
            f.write(updated)
        print("Updated README.md dynamic projects block")


def main() -> None:
    os.makedirs(ASSETS_DIR, exist_ok=True)
    metrics = fetch_metrics()

    outputs = {}
    for mode, theme in THEMES.items():
        outputs[f"hero-{mode}.svg"] = render_hero(theme)
        outputs[f"lifecycle-{mode}.svg"] = render_lifecycle(theme)
        outputs[f"projects-{mode}.svg"] = render_projects(theme, metrics["featured_projects"], metrics["updated"])
        outputs[f"stack-{mode}.svg"] = render_stack(theme)
        outputs[f"dashboard-{mode}.svg"] = render_dashboard(theme, metrics)
        outputs[f"footer-{mode}.svg"] = render_footer(theme)

    for filename, content in outputs.items():
        path = os.path.join(ASSETS_DIR, filename)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        print(f"Generated {filename}")

    sync_readme_projects(metrics["featured_projects"])


if __name__ == "__main__":
    main()
