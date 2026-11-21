"""Trading News Tracker: erstellt ein tägliches Briefing als Webseite.

Ablauf:
1. Alle Quellen aus config.toml gleichzeitig abrufen
2. Jeden Artikel nach deinen Themen und Schwerpunkten bewerten
3. Doppelte Meldungen entfernen, pro Thema die besten behalten
4. Daraus die Seite site/index.html bauen

Starten:  python briefing.py
"""

from __future__ import annotations

import html
import re
import tomllib
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from pathlib import Path
from zoneinfo import ZoneInfo

import feedparser

ROOT = Path(__file__).parent
CONFIG = ROOT / "config.toml"
OUTPUT = ROOT / "site" / "index.html"
TEMPLATE = ROOT / "template.html"
LOCAL_TZ = ZoneInfo("Asia/Shanghai")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) TradingNewsTracker/1.0"


@dataclass
class Article:
    title: str
    link: str
    source: str
    published: datetime
    summary: str
    source_topic: str
    scores: dict[str, int] = field(default_factory=dict)
    topic: str = ""
    score: int = 0


@dataclass
class SourceStatus:
    name: str
    ok: bool
    count: int
    error: str = ""


# ---------------------------------------------------------------- Abruf

def fetch(source: dict) -> tuple[list[dict], SourceStatus]:
    """Lädt einen Feed. Fehler werden gemeldet, brechen aber nichts ab."""
    try:
        req = urllib.request.Request(source["url"], headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
        feed = feedparser.parse(data)
        if not feed.entries:
            return [], SourceStatus(source["name"], False, 0, "keine Artikel im Feed")
        return feed.entries, SourceStatus(source["name"], True, len(feed.entries))
    except Exception as exc:  # noqa: BLE001 – jede Störung nur melden
        return [], SourceStatus(source["name"], False, 0, str(exc)[:80])


def clean_text(raw: str, limit: int) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", raw or ""))
    text = re.sub(r"\s+", " ", text).strip()
    # Standard-Floskeln mancher Feeds entfernen
    text = re.sub(r"The post .* appeared first on .*$", "", text).strip()
    if len(text) > limit:
        text = text[:limit].rsplit(" ", 1)[0] + " …"
    return text


def entry_date(entry) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        value = entry.get(key)
        if value:
            return datetime(*value[:6], tzinfo=timezone.utc)
    return None


def to_articles(entries, source: dict, cfg: dict) -> list[Article]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=cfg["settings"]["max_age_hours"])
    articles = []
    for e in entries:
        published = entry_date(e)
        if not published or published < cutoff:
            continue
        title = clean_text(e.get("title", ""), 300)
        source_name = source["name"]
        # Google News hängt " - Quelle" an den Titel: als Quelle anzeigen
        if source["url"].startswith("https://news.google.com") and " - " in title:
            title, source_name = title.rsplit(" - ", 1)
        summary = clean_text(e.get("summary", ""), cfg["settings"]["summary_chars"])
        if summary.lower().startswith(title.lower()[:40]):
            summary = ""  # Google News wiederholt nur den Titel
        articles.append(Article(title, e.get("link", "#"), source_name, published,
                                summary, source["topic"]))
    return articles


# ---------------------------------------------------------------- Bewertung

def keyword_pattern(word: str) -> re.Pattern:
    # Kurze Wörter (z. B. "ai") nur als ganzes Wort, längere am Wortanfang,
    # damit "sanction" auch "sanctions" findet.
    end = r"\b" if len(word) <= 3 else ""
    return re.compile(r"\b" + re.escape(word) + end, re.IGNORECASE)


def score_articles(articles: list[Article], cfg: dict) -> None:
    focus = [(keyword_pattern(w), p) for w, p in cfg["focus"].items()]
    topics = {t["id"]: [(keyword_pattern(w), p) for w, p in t["keywords"].items()]
              for t in cfg["topics"]}
    excludes = {t["id"]: [keyword_pattern(w) for w in t.get("exclude", [])]
                for t in cfg["topics"]}
    for a in articles:
        title, body = a.title, a.summary
        def points(patterns):
            # Treffer im Titel zählen doppelt
            return sum(p * (2 if rx.search(title) else 1 if rx.search(body) else 0)
                       for rx, p in patterns)
        bonus = points(focus)
        for tid, patterns in topics.items():
            if any(rx.search(title) or rx.search(body) for rx in excludes[tid]):
                continue
            s = points(patterns)
            if s == 0 and tid != a.source_topic:
                continue
            s += bonus + (2 if tid == a.source_topic else 0)
            a.scores[tid] = s
        if a.scores:
            a.topic, a.score = max(a.scores.items(), key=lambda kv: kv[1])


def similar(a: str, b: str) -> bool:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() > 0.75


def select(articles: list[Article], cfg: dict) -> dict[str, list[Article]]:
    s = cfg["settings"]
    ranked = sorted((a for a in articles if a.score >= s["min_score"]),
                    key=lambda a: (a.score, a.published), reverse=True)
    chosen: list[Article] = []
    for a in ranked:
        if not any(similar(a.title, c.title) for c in chosen):
            chosen.append(a)
    result = {t["id"]: [] for t in cfg["topics"]}
    # Ein Thema kann mit eigenem per_topic die allgemeine Zahl überschreiben
    limits = {t["id"]: t.get("per_topic", s["per_topic"]) for t in cfg["topics"]}
    for a in chosen:
        picked = result[a.topic]
        same_source = sum(p.source == a.source for p in picked)
        if len(picked) < limits[a.topic] and same_source < s["per_source"]:
            picked.append(a)
    return result


# ---------------------------------------------------------------- Webseite

def render(selection, statuses, cfg) -> str:
    now = datetime.now(LOCAL_TZ)
    weekdays = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    nav, sections = [], []
    for t in cfg["topics"]:
        items = selection[t["id"]]
        nav.append(f'<a href="#{t["id"]}">{html.escape(t["title"])} <span>{len(items)}</span></a>')
        cards = []
        for a in items:
            age_h = int((datetime.now(timezone.utc) - a.published).total_seconds() // 3600)
            age = "gerade eben" if age_h < 1 else f"vor {age_h} Std."
            summary = f"<p>{html.escape(a.summary)}</p>" if a.summary else ""
            cards.append(
                f'<article><a class="title" href="{html.escape(a.link)}" target="_blank" rel="noopener">'
                f'{html.escape(a.title)}</a>{summary}'
                f'<div class="meta">{html.escape(a.source)} · {age}</div></article>')
        body = "".join(cards) or '<p class="empty">Heute keine passenden Meldungen.</p>'
        sections.append(f'<section id="{t["id"]}"><h2>{html.escape(t["title"])}</h2>{body}</section>')

    ok = sum(s.ok for s in statuses)
    broken = [s for s in statuses if not s.ok]
    health = f"{ok} von {len(statuses)} Quellen erreichbar."
    if broken:
        health += " Ausgefallen: " + ", ".join(
            f'<span title="{html.escape(s.error)}">{html.escape(s.name)}</span>' for s in broken)

    return (TEMPLATE.read_text(encoding="utf-8")
            .replace("{{DATE}}", f"{weekdays[now.weekday()]}, {now:%d.%m.%Y}")
            .replace("{{TIME}}", now.strftime("%H:%M"))
            .replace("{{NAV}}", "".join(nav))
            .replace("{{SECTIONS}}", "".join(sections))
            .replace("{{HEALTH}}", health))


# ---------------------------------------------------------------- Hauptprogramm

def main() -> None:
    cfg = tomllib.loads(CONFIG.read_text(encoding="utf-8"))
    sources = cfg["sources"]
    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(fetch, sources))

    articles, statuses = [], []
    for source, (entries, status) in zip(sources, results):
        statuses.append(status)
        articles += to_articles(entries, source, cfg)
        mark = "OK  " if status.ok else "FEHLER"
        print(f"{mark} {status.name}: {status.count or status.error}")

    score_articles(articles, cfg)
    selection = select(articles, cfg)
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(render(selection, statuses, cfg), encoding="utf-8")
    total = sum(len(v) for v in selection.values())
    print(f"\n{len(articles)} aktuelle Artikel gelesen, {total} ins Briefing übernommen.")
    print(f"Fertig: {OUTPUT}")


if __name__ == "__main__":
    main()
