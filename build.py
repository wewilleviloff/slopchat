#!/usr/bin/env python3
"""
Build script for slopchat Pages deployment.

Reads analysis artifacts from the repo root and produces a static site in ./dist:
  - index.html            minimal navigation page with stats (from index.template.html)
  - assets/stats.json     computed statistics
  - infographics/*.html   copied infographic pages
  - graph/*               relationship-graph SVG + DOT source
  - export/*              Telegram chat export (HTML/CSS/JS/images, media skipped)

Usage:  python3 build.py
Then deploy ./dist to GitHub Pages (branch gh-pages or the Pages "Deploy from a
branch" workflow pointed at dist, or actions/upload-pages-artifact).
"""

import json
import os
import re
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")


def load(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return f.read()


def load_json(name):
    return json.loads(load(name))


def count_html_in_export():
    export_dir = os.path.join(ROOT, "ChatExport_2026-10-31")
    n = 0
    for dirpath, _dirs, files in os.walk(export_dir):
        n += sum(1 for fn in files if fn.endswith(".html"))
    return n


BACK_LINK = '<a href="../index.html" style="position:fixed;top:10px;right:12px;z-index:99;' \
            'font:12px ui-monospace,Menlo,monospace;color:#8ab4f8;background:rgba(13,15,18,.85);' \
            'border:1px solid #23272f;border-radius:6px;padding:5px 10px;' \
            'text-decoration:none">← навигация</a>'


def copy_infographic(src, dst_href):
    """Copy an infographic page into dist and inject a back-to-index link."""
    with open(os.path.join(ROOT, src), encoding="utf-8") as f:
        html = f.read()
    m = re.search(r"<body[^>]*>", html)
    if m:
        html = html[: m.end()] + "\n" + BACK_LINK + html[m.end():]
    else:
        html = BACK_LINK + html
    with open(os.path.join(DIST, dst_href), "w", encoding="utf-8") as f:
        f.write(html)


def compute_stats():
    people = [l.strip() for l in load("chat_people.txt").splitlines() if l.strip()]
    weird = load_json("weird_index.json")
    rating = load_json("rating_table.json")  # [name, msgs, ru%, night%, ..., patriot_score, ...]
    graph = load_json("graph.json")
    pair_reply = graph.get("pair_reply", {})

    top_weird = sorted(weird.items(), key=lambda kv: -kv[1])[:5]
    top_patriot = sorted(rating, key=lambda r: -r[7])[:5]
    most_active = sorted(rating, key=lambda r: -r[1])[:5]

    return {
        "generated": "2026-11-01",
        "period": "29.03–31.10.2026",
        "chat": "NOCHNOY DOZOR CHAT / slopchat",
        "participants": len(people),
        "rated_weirdness": len(weird),
        "rated_patriotism": len(rating),
        "reply_pairs": len(pair_reply),
        "reply_chain_messages": sum(pair_reply.values()),
        "export_pages": count_html_in_export(),
        "top_weird": [[k, v] for k, v in top_weird],
        "top_patriot": [[r[0], r[7]] for r in top_patriot],
        "most_active": [[r[0], r[1]] for r in most_active],
    }


PAGES = [
    {
        "href": "infographics/patriotism.html",
        "title": "Рейтинг патриотичности",
        "desc": "🇷🇺 Кто на самом деле тянет одеяло к себе",
        "src": "patriotism_infographic.html",
    },
    {
        "href": "infographics/weirdness.html",
        "title": "Рейтинг «шизонутости»",
        "desc": "🎪 Отбитость участников чата в цифрах",
        "src": "slopchat_weirdness_rating.html",
    },
    {
        "href": "infographics/shizone.html",
        "title": "Рейтинг шизонутости (v2)",
        "desc": "🔥 Обновлённая версия рейтинга",
        "src": "shizone_infographic.html",
    },
    {
        "href": "infographics/relations.html",
        "title": "Карта отношений",
        "desc": "🕸 Кто с кем переписывается чаще всего",
        "src": "slopchat_relations.html",
    },
    {
        "href": "graph/make_graph.dot.svg",
        "title": "Граф связей (SVG)",
        "desc": "📈 Статичная визуализация графа ответов",
        "files": ["make_graph.dot.svg", "make_graph.dot.png", "make_graph.dot"],
    },
    {
        "href": "export/messages.html",
        "title": "Экспорт чата",
        "desc": "💬 Полный HTML-экспорт переписки Telegram",
        "dir": "ChatExport_2026-10-31",
    },
]


def render_index(stats):
    tpl_path = os.path.join(ROOT, "index.template.html")
    html = load(tpl_path)

    def fmt(n):
        return f"{n:,}".replace(",", " ")

    cards = []
    for p in PAGES:
        cards.append(
            '<a class="card" href="%s"><h2>%s</h2><p>%s</p></a>'
            % (p["href"], p["title"], p["desc"])
        )

    replacements = {
        "{{PERIOD}}": stats["period"],
        "{{GENERATED}}": stats["generated"],
        "{{N_PARTICIPANTS}}": fmt(stats["participants"]),
        "{{N_REPLY_PAIRS}}": fmt(stats["reply_pairs"]),
        "{{N_REPLY_MSGS}}": fmt(stats["reply_chain_messages"]),
        "{{N_EXPORT_PAGES}}": fmt(stats["export_pages"]),
        "{{CARDS}}": "\n      ".join(cards),
        "{{TOP_WEIRD}}": json.dumps(stats["top_weird"], ensure_ascii=False),
        "{{TOP_PATRIOT}}": json.dumps(stats["top_patriot"], ensure_ascii=False),
        "{{MOST_ACTIVE}}": json.dumps(stats["most_active"], ensure_ascii=False),
    }
    for k, v in replacements.items():
        html = html.replace(k, v)
    return html


def main():
    if os.path.exists(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)

    stats = compute_stats()

    # assets
    assets = os.path.join(DIST, "assets")
    os.makedirs(assets)
    with open(os.path.join(assets, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    # infographics
    info_dir = os.path.join(DIST, "infographics")
    os.makedirs(info_dir)
    for p in PAGES:
        if "src" in p:
            copy_infographic(p["src"], p["href"])
        if "files" in p:
            gdir = os.path.join(DIST, "graph")
            os.makedirs(gdir, exist_ok=True)
            for fn in p["files"]:
                shutil.copy2(os.path.join(ROOT, fn), os.path.join(gdir, fn))
        if "dir" in p:
            edir = os.path.join(DIST, "export")
            shutil.copytree(os.path.join(ROOT, p["dir"]), edir,
                            ignore=shutil.ignore_patterns("media", "videos", "files"))
            # inject back-link into export pages
            for dirpath, _dirs, files in os.walk(edir):
                for fn in files:
                    if not fn.endswith(".html"):
                        continue
                    fp = os.path.join(dirpath, fn)
                    with open(fp, encoding="utf-8") as f:
                        html = f.read()
                    m = re.search(r"<body[^>]*>", html)
                    if m:
                        html = html[: m.end()] + "\n" + BACK_LINK + html[m.end():]
                        with open(fp, "w", encoding="utf-8") as f:
                            f.write(html)

    # index
    with open(os.path.join(DIST, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_index(stats))

    # Pages deployment helpers
    open(os.path.join(DIST, ".nojekyll"), "w").close()

    total = 0
    nfiles = 0
    for dirpath, _dirs, files in os.walk(DIST):
        for fn in files:
            fp = os.path.join(dirpath, fn)
            total += os.path.getsize(fp)
            nfiles += 1
    print("Built %s: %d files, %.1f MB" % (DIST, nfiles, total / 1e6))


if __name__ == "__main__":
    main()
