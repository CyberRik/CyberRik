"""Regenerate the skyline header SVGs and the upstream-contributions list in README.md.

Runs daily from .github/workflows/build.yml. Locally:
    GITHUB_TOKEN=$(gh auth token) python scripts/build.py
Standard library only.
"""

import html
import json
import math
import random
import os
import re
import urllib.request
from pathlib import Path

USER = "CyberRik"
ROOT = Path(__file__).resolve().parent.parent
MIN_STARS = 200  # an upstream project, not a friend's or a hackathon repo

# Display names for upstream organisations, in the order they should appear.
ORGS = {
    "docling-project": ("Docling", "LF AI & Data"),
    "feast-dev": ("Feast", "LF AI & Data"),
    "meshery": ("Meshery", "CNCF"),
}

QUERY = """
query($q: String!) {
  search(query: $q, type: ISSUE, first: 100) {
    nodes { ... on PullRequest {
      number title url state merged mergedAt createdAt
      repository { name nameWithOwner stargazerCount owner { login } }
    } }
  }
  user(login: "%s") {
    repositories(ownerAffiliations: OWNER, privacy: PUBLIC) { totalCount }
    contributionsCollection { contributionCalendar { totalContributions weeks { contributionDays { contributionCount } } } }
  }
}
""" % USER


def fetch():
    token = os.environ["GITHUB_TOKEN"]
    body = json.dumps({"query": QUERY, "variables": {"q": f"author:{USER} is:pr -user:{USER}"}})
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body.encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": "profile-readme-build"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(data["errors"])
    return data["data"]


def split_title(t):
    """'fix(epub): drop x' -> ('epub', 'Drop x'); '[Docs] Fix y' -> ('Docs', 'Fix y')."""
    tag = None
    m = re.match(r"^\[([^\]]+)\]\s*", t)
    if m:
        tag, t = m.group(1), t[m.end():]
    m = re.match(r"^\w+(?:\(([^)]*)\))?!?:\s*", t)
    if m:
        tag, t = tag or m.group(1), t[m.end():]
    return tag, t[:1].upper() + t[1:]


def upstream_prs(data):
    prs = [
        p for p in data["search"]["nodes"]
        if p and p["repository"]["stargazerCount"] >= MIN_STARS
        and (p["merged"] or p["state"] == "OPEN")
    ]
    order = list(ORGS)
    prs.sort(key=lambda p: (
        order.index(p["repository"]["owner"]["login"]) if p["repository"]["owner"]["login"] in order else 99,
        not p["merged"],
        p["mergedAt"] or p["createdAt"],
    ))
    return prs


def render_list(prs):
    out, current = [], None
    for p in prs:
        owner = p["repository"]["owner"]["login"]
        if owner != current:
            current = owner
            name, foundation = ORGS.get(owner, (owner, ""))
            suffix = f" <sub>{foundation}</sub>" if foundation else ""
            out.append(f"\n**[{name}](https://github.com/{owner})**{suffix}\n")
        ref = f"{p['repository']['name']}#{p['number']}"
        status = "" if p["merged"] else " <sub><i>in review</i></sub>"
        tag, title = split_title(p["title"])
        tag = f"`{tag}` " if tag else ""
        out.append(f"- [{ref}]({p['url']}) {tag}{title}{status}")
    return "\n".join(out).strip()


# ---------------------------------------------------------------- header

# The header is a city drawn from the last WEEKS of the contribution calendar:
# one building per day, height ~ sqrt(contributions). Static on first paint;
# a few windows twinkle (off under prefers-reduced-motion).
WEEKS = 26
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI','Helvetica Neue',Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"

THEMES = {
    "dark": dict(sky=("#0b0f17", "#0d1a17"), fg="#f0f6fc", dim="#8b949e", accent="#3FCF8E",
                 tops=("#1a2420", "#1d6b4b", "#27a06b", "#3FCF8E", "#8ff0c4"), kl=.58, kr=.38,
                 ground="#121a17", window="#ffd57e", glow="#3FCF8E", glow_op=.22, stars=True, border="#30363d"),
    "light": dict(sky=("#ffffff", "#eaf6f0"), fg="#1f2328", dim="#59636e", accent="#1a7f5a",
                  tops=("#e3e9e6", "#9be9a8", "#40c463", "#30a14e", "#216e39"), kl=.82, kr=.66,
                  ground="#e8eeeb", window="#ffffff", glow="#40c463", glow_op=.18, stars=False, border="#d0d7de"),
}


def shade(h, k):
    r, g, b = (int(h[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % (int(r * k), int(g * k), int(b * k))


def render_header(weeks, theme):
    c = THEMES[theme]
    rnd = random.Random(11)
    W, H = 900, 320
    total = sum(sum(w) for w in weeks)
    mx = max(max(w) for w in weeks) or 1
    s = 10.5                     # half-width of a cell's top face
    ox, oy = 560, 128            # screen position of week 0, day 0
    parts, twinkles = [], []

    def lvl(n):
        if not n:
            return 0
        q = n / mx
        return 1 if q < .15 else 2 if q < .35 else 3 if q < .6 else 4

    cells = sorted(((wi + di, wi, di, n) for wi, w in enumerate(weeks) for di, n in enumerate(w)))
    for _, wi, di, n in cells:
        x = ox + (wi - di) * s
        y = oy + (wi + di) * s * .5
        h = 2.5 + (math.sqrt(n / mx) * 118 if n else 0)
        top = c["tops"][lvl(n)]
        L, R = shade(top, c["kl"]), shade(top, c["kr"])
        parts.append(f'<path d="M{x:.1f} {y-h:.1f}l{s:.1f} {s/2:.1f}l{-s:.1f} {s/2:.1f}l{-s:.1f} {-s/2:.1f}z" fill="{top}"/>'
                     f'<path d="M{x-s:.1f} {y-h+s/2:.1f}l{s:.1f} {s/2:.1f}v{h:.1f}l{-s:.1f} {-s/2:.1f}z" fill="{L}"/>'
                     f'<path d="M{x:.1f} {y-h+s:.1f}l{s:.1f} {-s/2:.1f}v{h:.1f}l{-s:.1f} {s/2:.1f}z" fill="{R}"/>')
        # windows: two columns per face, rows every 7px
        if h > 16:
            for face in (-1, 1):
                for col in (.28, .64):
                    for k in range(int((h - 8) // 7)):
                        if rnd.random() > .42:
                            continue
                        u = col * s
                        wx = x + face * u
                        wy = y - h + s + 4 + k * 7 - (u / 2 if face == 1 else -u / 2) + (0 if face == 1 else -s / 2)
                        if face == -1:
                            wy = y - h + s / 2 + 4 + k * 7 + (s - u) / 2
                            wx = x - s + (s - u)
                        d = f'M{wx:.1f} {wy:.1f}l{face*1.9:.1f} {-0.95 if face == 1 else 0.95:.2f}v2.4l{-face*1.9:.1f} {0.95 if face == 1 else -0.95:.2f}z'
                        if rnd.random() < .12:
                            twinkles.append(f'<path class="tw" style="animation-delay:-{rnd.uniform(0, 6):.1f}s" d="{d}" fill="{c["window"]}"/>')
                        else:
                            parts.append(f'<path d="{d}" fill="{c["window"]}" opacity="{rnd.uniform(.55, .95):.2f}"/>')

    stars = ""
    if c["stars"]:
        stars = "".join(f'<circle cx="{rnd.uniform(420, 890):.0f}" cy="{rnd.uniform(12, 150):.0f}" r="{rnd.choice((.6, .8, 1.1))}" '
                        f'fill="#c9d1d9" opacity="{rnd.uniform(.2, .65):.2f}"/>' for _ in range(46))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Ritankar Mondal, AI engineer. The skyline is built from GitHub contributions over the past six months.">
  <style>
    .tw {{ animation: tw 6s ease-in-out infinite; }}
    @keyframes tw {{ 0%, 100% {{ opacity: .95; }} 45% {{ opacity: .15; }} 55% {{ opacity: .15; }} }}
    @media (prefers-reduced-motion: reduce) {{ .tw {{ animation: none; }} }}
  </style>
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c['sky'][0]}"/><stop offset="1" stop-color="{c['sky'][1]}"/></linearGradient>
    <radialGradient id="glow" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="{c['glow']}" stop-opacity="{c['glow_op']}"/><stop offset="1" stop-color="{c['glow']}" stop-opacity="0"/></radialGradient>
    <clipPath id="card"><rect width="{W}" height="{H}" rx="14"/></clipPath>
  </defs>
  <g clip-path="url(#card)">
    <rect width="{W}" height="{H}" fill="url(#sky)"/>
    {stars}
    <ellipse cx="690" cy="215" rx="260" ry="120" fill="url(#glow)"/>
    {''.join(parts)}
    {''.join(twinkles)}
  </g>
  <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="14" fill="none" stroke="{c['border']}"/>
  <g font-family="{SANS}">
    <text x="44" y="70" font-size="12" font-weight="600" letter-spacing="2.4" fill="{c['accent']}">AI ENGINEER</text>
    <text x="44" y="114" font-size="40" font-weight="700" letter-spacing="-.6" fill="{c['fg']}">Ritankar Mondal</text>
    <text x="44" y="148" font-size="16" fill="{c['dim']}">LLM systems, retrieval, and the</text>
    <text x="44" y="170" font-size="16" fill="{c['dim']}">runtimes under them.</text>
  </g>
  <g font-family="{MONO}" font-size="12" fill="{c['dim']}">
    <text x="44" y="262">IIT Madras · ex-Otsuka, Tokyo</text>
    <text x="44" y="282"><tspan fill="{c['accent']}">{total:,}</tspan> contributions in 26 weeks, as a skyline</text>
  </g>
</svg>
"""


def main():
    data = fetch()
    prs = upstream_prs(data)
    cal = data["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = [[d["contributionCount"] for d in w["contributionDays"]] for w in cal["weeks"]][-WEEKS:]
    for theme in THEMES:
        (ROOT / "assets" / f"header-{theme}.svg").write_text(render_header(weeks, theme), encoding="utf-8", newline="\n")

    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    block = f"<!-- upstream:start -->\n{render_list(prs)}\n<!-- upstream:end -->"
    text = re.sub(r"<!-- upstream:start -->.*?<!-- upstream:end -->", lambda _: block, text, flags=re.S)
    readme.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
