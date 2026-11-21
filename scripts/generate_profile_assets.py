"""Generate adaptive Dark/Light and Desktop/Mobile SVG assets for GitHub profile."""

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

PROFILE = {
    "name": "Pushpika Odisha",
    "handle": f"@{USERNAME}",
    "role": "Full-Stack & Systems Software Engineer",
    "tagline": "Building zero-dependency engines, resilient APIs, and interactive web systems.",
    "location": "Sri Lanka",
    "focus": "Node.js · PHP 8 · Systems · Graphics",
}

THEMES = {
    "dark": {
        "bg": "#0D1117",
        "card": "#161B22",
        "card_alt": "#1C2128",
        "border": "#30363D",
        "text": "#F0F6FC",
        "subtext": "#C9D1D9",
        "muted": "#8B949E",
        "accent": "#38BDF8",
        "accent_2": "#818CF8",
        "pill_bg": "#1F2937",
        "pill_border": "#374151",
        "grid": "#21262D",
        "bar_bg": "#21262D",
    },
    "light": {
        "bg": "#FFFFFF",
        "card": "#F6F8FA",
        "card_alt": "#FFFFFF",
        "border": "#D0D7DE",
        "text": "#1F2328",
        "subtext": "#32383F",
        "muted": "#656D76",
        "accent": "#0284C7",
        "accent_2": "#4F46E5",
        "pill_bg": "#EFF6FF",
        "pill_border": "#BFDBFE",
        "grid": "#EAECEF",
        "bar_bg": "#EAEEF2",
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

SANS_FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
MONO_FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"


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

    return {
        "public_repos": int(user.get("public_repos", len(repos))),
        "lang_count": len(top_langs),
        "stars": stars,
        "followers": int(user.get("followers", 0)),
        "top_langs": top_langs,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }


def render_hero(t: dict, mobile: bool = False) -> str:
    """Render the desktop or mobile hero SVG."""
    w, h = (540, 236) if mobile else (900, 210)
    pad = 28 if mobile else 44
    name_size = 28 if mobile else 36
    role_size = 15 if mobile else 17
    tag_size = 13 if mobile else 14

    c_bg = t["bg"]
    c_border = t["border"]
    c_text = t["text"]
    c_subtext = t["subtext"]
    c_muted = t["muted"]
    c_accent = t["accent"]
    c_accent_2 = t["accent_2"]
    c_pill_bg = t["pill_bg"]
    c_pill_border = t["pill_border"]
    c_grid = t["grid"]

    p_name = html.escape(PROFILE["name"])
    p_role = html.escape(PROFILE["role"])
    p_handle = html.escape(PROFILE["handle"])
    p_loc = html.escape(PROFILE["location"])
    p_tag = html.escape(PROFILE["tagline"])
    p_focus = html.escape(PROFILE["focus"])

    if mobile:
        tagline_svg = (
            f'<text x="{pad}" y="148" font-family="{SANS_FONT}" font-size="{tag_size}" fill="{c_muted}">'
            f'Zero-dependency engines, resilient APIs, &amp;</text>'
            f'<text x="{pad}" y="168" font-family="{SANS_FONT}" font-size="{tag_size}" fill="{c_muted}">'
            f'interactive web systems.</text>'
        )
        badge_y = 190
    else:
        tagline_svg = (
            f'<text x="{pad}" y="146" font-family="{SANS_FONT}" font-size="{tag_size}" fill="{c_muted}">'
            f'{p_tag}</text>'
        )
        badge_y = 166

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{p_name} — {p_role}">
  <defs>
    <linearGradient id="heroAccent" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{c_accent}"/>
      <stop offset="100%" stop-color="{c_accent_2}"/>
    </linearGradient>
    <pattern id="dotGrid" width="24" height="24" patternUnits="userSpaceOnUse">
      <circle cx="2" cy="2" r="1" fill="{c_grid}"/>
    </pattern>
  </defs>
  <rect width="{w}" height="{h}" rx="14" fill="{c_bg}" stroke="{c_border}" stroke-width="1.5"/>
  <rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="13" fill="url(#dotGrid)" opacity="0.8"/>
  <rect x="{pad}" y="30" width="64" height="4" rx="2" fill="url(#heroAccent)"/>
  <text x="{w - pad}" y="38" text-anchor="end" font-family="{MONO_FONT}" font-size="11" fill="{c_muted}">{p_handle} · {p_loc}</text>
  <text x="{pad}" y="82" font-family="{SANS_FONT}" font-size="{name_size}" font-weight="700" letter-spacing="-0.5" fill="{c_text}">{p_name}</text>
  <text x="{pad}" y="114" font-family="{SANS_FONT}" font-size="{role_size}" font-weight="600" fill="url(#heroAccent)">{p_role}</text>
  {tagline_svg}
  <rect x="{pad}" y="{badge_y}" width="262" height="24" rx="6" fill="{c_pill_bg}" stroke="{c_pill_border}" stroke-width="1"/>
  <circle cx="{pad + 13}" cy="{badge_y + 12}" r="3.5" fill="#22C55E"/>
  <text x="{pad + 24}" y="{badge_y + 16}" font-family="{MONO_FONT}" font-size="11" fill="{c_subtext}">{p_focus}</text>
</svg>
"""


def render_stats(t: dict, m: dict, mobile: bool = False) -> str:
    """Render the desktop or mobile GitHub metrics SVG."""
    w, h = (540, 332) if mobile else (900, 215)
    pad = 26 if mobile else 36

    c_card = t["card"]
    c_card_alt = t["card_alt"]
    c_border = t["border"]
    c_text = t["text"]
    c_muted = t["muted"]
    c_accent = t["accent"]
    c_bar_bg = t["bar_bg"]

    kpi_items = [
        ("REPOSITORIES", str(m["public_repos"])),
        ("LANGUAGES", str(m["lang_count"])),
        ("TOTAL STARS", str(m["stars"])),
        ("FOLLOWERS", str(m["followers"])),
    ]

    bar_x = pad if mobile else 455
    bar_w = (w - pad * 2) if mobile else 408
    bar_y = 186 if mobile else 62

    segments = []
    legend = []
    cursor_x = bar_x
    for idx, (lang, pct) in enumerate(m["top_langs"]):
        color = LANG_COLORS.get(lang, c_accent)
        seg_w = max(round((pct / 100.0) * bar_w), 4)
        if idx == len(m["top_langs"]) - 1:
            seg_w = max(bar_x + bar_w - cursor_x, 4)
        segments.append(
            f'<rect x="{cursor_x}" y="{bar_y}" width="{seg_w}" height="10" fill="{color}"/>'
        )
        cursor_x += seg_w

        row_y = (bar_y + 34 + idx * 22) if mobile else (96 + idx * 21)
        esc_lang = html.escape(lang)
        legend.append(
            f'<circle cx="{bar_x + 6}" cy="{row_y - 4}" r="4.5" fill="{color}"/>'
            f'<text x="{bar_x + 18}" y="{row_y}" font-family="{SANS_FONT}" font-size="12.5" font-weight="500" fill="{c_text}">{esc_lang}</text>'
            f'<text x="{bar_x + bar_w}" y="{row_y}" text-anchor="end" font-family="{MONO_FONT}" font-size="12" fill="{c_muted}">{pct:.1f}%</text>'
        )

    kpi_svg = []
    if mobile:
        col_w = (w - pad * 2 - 12) // 2
        for idx, (label, value) in enumerate(kpi_items):
            col = idx % 2
            row = idx // 2
            kx = pad + col * (col_w + 12)
            ky = 56 + row * 52
            kpi_svg.append(
                f'<rect x="{kx}" y="{ky}" width="{col_w}" height="44" rx="8" fill="{c_card_alt}" stroke="{c_border}" stroke-width="1"/>'
                f'<text x="{kx + 12}" y="{ky + 17}" font-family="{MONO_FONT}" font-size="9.5" fill="{c_muted}">{label}</text>'
                f'<text x="{kx + 12}" y="{ky + 36}" font-family="{SANS_FONT}" font-size="17" font-weight="700" fill="{c_text}">{value}</text>'
            )
        lang_title_y = 174
        divider = f'<line x1="{pad}" y1="158" x2="{w - pad}" y2="158" stroke="{c_border}" stroke-width="1"/>'
    else:
        col_w = 178
        for idx, (label, value) in enumerate(kpi_items):
            col = idx % 2
            row = idx // 2
            kx = pad + col * (col_w + 14)
            ky = 54 + row * 62
            kpi_svg.append(
                f'<rect x="{kx}" y="{ky}" width="{col_w}" height="52" rx="9" fill="{c_card_alt}" stroke="{c_border}" stroke-width="1"/>'
                f'<text x="{kx + 14}" y="{ky + 19}" font-family="{MONO_FONT}" font-size="10" fill="{c_muted}">{label}</text>'
                f'<text x="{kx + 14}" y="{ky + 42}" font-family="{SANS_FONT}" font-size="20" font-weight="700" fill="{c_text}">{value}</text>'
            )
        lang_title_y = 44
        divider = f'<line x1="428" y1="26" x2="428" y2="188" stroke="{c_border}" stroke-width="1"/>'

    clip_id = f"langBarClip_{'m' if mobile else 'd'}"
    updated = html.escape(m["updated"])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="GitHub Engineering Metrics">
  <defs>
    <clipPath id="{clip_id}">
      <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="10" rx="5"/>
    </clipPath>
  </defs>
  <rect width="{w}" height="{h}" rx="14" fill="{c_card}" stroke="{c_border}" stroke-width="1.5"/>
  <text x="{pad}" y="36" font-family="{MONO_FONT}" font-size="11" font-weight="600" letter-spacing="0.8" fill="{c_muted}">GITHUB OVERVIEW</text>
  {"".join(kpi_svg)}
  {divider}
  <text x="{bar_x}" y="{lang_title_y}" font-family="{MONO_FONT}" font-size="11" font-weight="600" letter-spacing="0.8" fill="{c_muted}">LANGUAGE DISTRIBUTION (BY BYTES)</text>
  <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="10" rx="5" fill="{c_bar_bg}"/>
  <g clip-path="url(#{clip_id})">{"".join(segments)}</g>
  {"".join(legend)}
  <text x="{pad}" y="{h - 14}" font-family="{MONO_FONT}" font-size="10.5" fill="{c_muted}">Auto-synced via GitHub Actions · {updated}</text>
</svg>
"""


def render_footer(t: dict) -> str:
    """Render a clean minimalist footer SVG."""
    w, h = 900, 96
    c_bg = t["bg"]
    c_border = t["border"]
    c_text = t["text"]
    c_muted = t["muted"]
    c_accent = t["accent"]
    c_accent_2 = t["accent_2"]
    esc_user = html.escape(USERNAME)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Open to engineering collaborations">
  <defs>
    <linearGradient id="footerAccent" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{c_accent}"/>
      <stop offset="100%" stop-color="{c_accent_2}"/>
    </linearGradient>
  </defs>
  <rect width="{w}" height="{h}" rx="14" fill="{c_bg}" stroke="{c_border}" stroke-width="1.5"/>
  <rect x="36" y="30" width="4" height="36" rx="2" fill="url(#footerAccent)"/>
  <text x="54" y="45" font-family="{SANS_FONT}" font-size="15" font-weight="600" fill="{c_text}">Open to software engineering roles, technical architecture, and open-source collaboration.</text>
  <text x="54" y="67" font-family="{MONO_FONT}" font-size="12" fill="{c_muted}">pushpikaodisha.dev@gmail.com  ·  github.com/{esc_user}</text>
</svg>
"""


def main() -> None:
    os.makedirs(ASSETS_DIR, exist_ok=True)
    metrics = fetch_github_metrics()

    outputs = {}
    for mode, theme in THEMES.items():
        outputs[f"hero-{mode}.svg"] = render_hero(theme, mobile=False)
        outputs[f"hero-{mode}-mobile.svg"] = render_hero(theme, mobile=True)
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
