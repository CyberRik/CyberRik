"""Regenerate the profile card SVGs and the upstream-contributions list in README.md.

Runs daily from .github/workflows/build.yml. Locally:
    GITHUB_TOKEN=$(gh auth token) python scripts/build.py
Standard library only.
"""

import html
import json
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
    contributionsCollection { contributionCalendar { totalContributions } }
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


# ---------------------------------------------------------------- card

# An anchor, for Ancora and for durability. Rasterised once from a vector drawing
# into shaded ASCII; kept as a constant so the workflow needs no image libraries.
ART = r"""
            :*##*:
           -@@==@@=
           =@@==@@=
            :#@@#-
      :++++++*@@*++++++-
      -******#@@#******=
             :@@:
             :@@:
             :@@:
             :@@:
             :@@:
*#           :@@:           #*
@@%:         :@@:         :%@@
%%%@*-       :@@:       :*@%%%
   -@@=      :@@:      -@@=
    :%@#-    :@@:    -#@%:
      -#@@*=--@@=-=*@@%=
        .-*#@@@@@@#*=.
             =@@=
              ..
""".strip("\n").split("\n")

THEMES = {
    "dark": dict(bg="#0d1117", border="#30363d", fg="#e6edf3", dim="#6e7681", key="#3FCF8E",
                 art=("#a7f3d0", "#3FCF8E", "#14845a"),
                 blocks=("#0f3d2c", "#14845a", "#26a269", "#3FCF8E", "#7ee2b8", "#c9f5e0")),
    "light": dict(bg="#ffffff", border="#d0d7de", fg="#1f2328", dim="#8c959f", key="#1a7f5a",
                  art=("#26a269", "#1a7f5a", "#0b4a33"),
                  blocks=("#0b4a33", "#14845a", "#1a7f5a", "#26a269", "#3FCF8E", "#a7f3d0")),
}
KEY_W = 15
FONT = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
PROMPT = "ritankar@mondal:~$ "
COMMAND = "neofetch"


def card_lines(prs, data):
    merged = [p for p in prs if p["merged"]]
    review = [p for p in prs if not p["merged"]]
    orgs = {p["repository"]["owner"]["login"] for p in merged}
    names = [ORGS.get(o, (o,))[0] for o in ORGS if o in orgs]
    contrib = data["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    repos = data["user"]["repositories"]["totalCount"]
    return [
        ("title", "ritankar", "mondal"),
        ("rule", 15),
        ("kv", "Role", "AI engineer · LLM systems, retrieval, infra"),
        ("kv", "Education", "B.Tech, IIT Madras · class of 2027"),
        ("kv", "Previously", "Otsuka (Tokyo) · Gravton Labs · OctonData"),
        ("kv", "Building", "Ancora · TinyServe"),
        ("kv", "Upstream", " · ".join(names)),
        ("kv", "Languages", "Python · C++ · TypeScript"),
        ("kv", "Tools", "PyTorch · Temporal · Ray · FastAPI · OTel"),
        ("gap",),
        ("kv2", "Merged PRs", f"{len(merged)} upstream", "In review", str(len(review))),
        ("kv2", "Contributions", f"{contrib:,} / year", "Repos", str(repos)),
        ("gap",),
        ("kv", "Web", "ritankar-mondal.vercel.app"),
        ("kv", "Email", "ritankarmondal123@gmail.com"),
        ("gap",),
        ("blocks",),
    ]


def leader(key, width=KEY_W):
    return " " + "." * max(2, width - len(key) - 1) + " "


def mix(a, b, t):
    pa = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    pb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(pa, pb))


def gradient(stops, t):
    if t <= 0.5:
        return mix(stops[0], stops[1], t * 2)
    return mix(stops[1], stops[2], (t - 0.5) * 2)


def render_card(lines, theme):
    c = THEMES[theme]
    e = html.escape
    pad, fs, cw, w = 32, 14, 8.4, 850
    lh, art_lh = 22, 18
    t0 = 1.1  # seconds: output starts appearing once the command is typed
    rows = []

    def reveal(i, step=0.055):
        return f' class="r" style="animation-delay:{t0 + i * step:.2f}s"'

    # prompt + typed command, one keystroke at a time
    py = pad + 14
    keys = "".join(f'<tspan class="k" style="animation-delay:{0.3 + i * 0.09:.2f}s">{ch}</tspan>'
                   for i, ch in enumerate(COMMAND))
    rows.append(f'<text x="{pad}" y="{py}"><tspan fill="{c["key"]}">{e(PROMPT)}</tspan>'
                f'<tspan fill="{c["fg"]}">{keys}</tspan></text>')

    # art
    top = py + 34
    for i, line in enumerate(ART):
        col = gradient(c["art"], i / (len(ART) - 1))
        rows.append(f'<text x="{pad}" y="{top + i * art_lh}" fill="{col}"{reveal(i, 0.03)}>{e(line)}</text>')
    art_bottom = top + (len(ART) - 1) * art_lh

    # info
    x = pad + 33 * cw
    y = top
    n = 0
    for ln in lines:
        kind = ln[0]
        if kind == "gap":
            y += lh // 2
            continue
        r = reveal(n)
        n += 1
        if kind == "title":
            rows.append(f'<text x="{x}" y="{y}"{r} font-weight="700"><tspan fill="{c["key"]}">{e(ln[1])}</tspan>'
                        f'<tspan fill="{c["fg"]}">@</tspan><tspan fill="{c["key"]}">{e(ln[2])}</tspan></text>')
        elif kind == "rule":
            rows.append(f'<text x="{x}" y="{y}" fill="{c["dim"]}"{r}>{"─" * ln[1]}</text>')
        elif kind == "kv":
            _, k, v = ln
            rows.append(f'<text x="{x}" y="{y}"{r}><tspan fill="{c["key"]}">{e(k)}</tspan>'
                        f'<tspan fill="{c["dim"]}">{leader(k)}</tspan><tspan fill="{c["fg"]}">{e(v)}</tspan></text>')
        elif kind == "kv2":
            _, k, v, k2, v2 = ln
            left = f"{k}{leader(k)}{v}"
            gap = " " * max(2, 34 - len(left))
            rows.append(f'<text x="{x}" y="{y}"{r}><tspan fill="{c["key"]}">{e(k)}</tspan>'
                        f'<tspan fill="{c["dim"]}">{leader(k)}</tspan><tspan fill="{c["fg"]}">{e(v)}{gap}</tspan>'
                        f'<tspan fill="{c["key"]}">{e(k2)}</tspan><tspan fill="{c["dim"]}">{leader(k2, 11)}</tspan>'
                        f'<tspan fill="{c["fg"]}">{e(v2)}</tspan></text>')
        elif kind == "blocks":
            sq = 24
            blocks = "".join(f'<rect x="{x + i * (sq + 4):.1f}" y="{y - 13}" width="{sq}" height="16" rx="2" fill="{col}"/>'
                             for i, col in enumerate(c["blocks"]))
            rows.append(f'<g{r}>{blocks}</g>')
        y += lh

    # closing prompt with a blinking cursor
    end_y = max(y - lh, art_bottom) + 40
    done = t0 + n * 0.055 + 0.2
    rows.append(f'<text x="{pad}" y="{end_y}" class="r" style="animation-delay:{done:.2f}s">'
                f'<tspan fill="{c["key"]}">{e(PROMPT)}</tspan></text>')
    rows.append(f'<text x="{pad}" y="{end_y}" class="cursor" style="animation-delay:{done:.2f}s,{done:.2f}s">'
                f'<tspan fill="none">{e(PROMPT)}</tspan><tspan fill="{c["key"]}">█</tspan></text>')

    h = end_y + pad - 6
    body = "\n  ".join(rows)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Ritankar Mondal: AI engineer working on LLM systems, retrieval and infrastructure">
  <style>
    text {{ white-space: pre; }}
    .r {{ opacity: 0; animation: in .35s ease-out forwards; }}
    .k {{ fill-opacity: 0; animation: key 0s forwards; }}
    .cursor {{ opacity: 0; animation: in 0s forwards, blink 1.1s step-end infinite; }}
    @keyframes in {{ to {{ opacity: 1; }} }}
    @keyframes key {{ to {{ fill-opacity: 1; }} }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{
      .r, .cursor {{ animation: none; opacity: 1; }}
      .k {{ animation: none; fill-opacity: 1; }}
    }}
  </style>
  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="12" fill="{c["bg"]}" stroke="{c["border"]}"/>
  <g font-family="{FONT}" font-size="{fs}">
  {body}
  </g>
</svg>
"""


def main():
    data = fetch()
    prs = upstream_prs(data)
    lines = card_lines(prs, data)
    for theme in THEMES:
        (ROOT / "assets" / f"card-{theme}.svg").write_text(render_card(lines, theme), encoding="utf-8", newline="\n")

    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    block = f"<!-- upstream:start -->\n{render_list(prs)}\n<!-- upstream:end -->"
    text = re.sub(r"<!-- upstream:start -->.*?<!-- upstream:end -->", lambda _: block, text, flags=re.S)
    readme.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
