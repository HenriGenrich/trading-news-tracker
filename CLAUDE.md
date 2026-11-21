# Trading News Tracker

Ein tägliches Briefing zu Nachrichten aus Handel, Wirtschaft und Politik, mit Schwerpunkt China.

- GitHub: https://github.com/HenriGenrich/trading-news-tracker
- Beschreibung (englisch): *A daily briefing on topics that interest me*

## Warum dieses Projekt
Henri bewirbt sich für eine duale Ausbildung in Hongkong (Kaufmann im Groß- und Außenhandel bzw. Logistikkaufmann). Das Projekt soll zeigen, dass er sich auch außerhalb der Schule für Handel, Logistik und China interessiert. Er soll es in der Bewerbung vorzeigen können.

## Themen (von Henri festgelegt)
1. **Geopolitik**
2. **Geoökonomie**
3. **Warenhandel**, Schwerpunkt China und Arktis, besonders Agrarrohstoffe (Weizen, Soja usw.)
4. **Maritimer Handel**, Schwerpunkt China und Arktis (z. B. Seewege, Häfen, Schifffahrt)
5. **Neue Erfindungen in der Logistik**
6. **Zukunftstechnologien** allgemein, z. B. Quantencomputer

## Stand
- 2026-11-21: Repository angelegt und lokal geklont. Bisher gibt es nur die README.
- 2026-11-21: Themen festgelegt (siehe oben).
- 2026-11-21: Erste Version gebaut (Variante A, ohne KI). `briefing.py` liest die Quellen aus `config.toml`, bewertet Artikel nach Stichwörtern, behält pro Thema die Top 5 und baut `site/index.html` (Vorlage: `template.html`). GitHub Actions (`.github/workflows/daily-briefing.yml`) baut jeden Tag um 6:00 Uhr Peking und veröffentlicht auf GitHub Pages.
- Ideen für später: KI-Zusammenfassung oben drauf, Archiv alter Briefings, Schiffsdaten (alter Collector).
- Python 3.12+ nötig (tomllib). Lokal starten: `python briefing.py`- Früher gab es einen ersten Versuch mit einer anderen KI (Qwen), der nur halb funktioniert hat. Dieses Projekt fängt neu an.

## Was beim alten Versuch schlecht war (nicht wiederholen)
- Die Artikel waren nicht gut, also unpassend oder wenig relevant.
- RSS-Feeds waren nicht abrufbar.
- Das Briefing war umständlich zu lesen.
- Es war keine echte Automatisierung und keine Erleichterung. Die KI direkt zu fragen wäre genauso schnell gewesen.

Alter Code: `Desktop\Trade Monitor\AI_Tracking_Project\rss_aggregator.py`. Feed-Test vom 2026-11-21: Nur 5 von 19 Feeds lieferten Artikel (WorldCargo News, Freightos, Supply Chain Dive, Pandaily, China Economic Review). Die anderen gaben 403/404 zurück oder waren leer, auch High North News, Barents Observer, The Diplomat, SCMP, Maritime Executive und mining.com. Für jede neue Quelle zuerst die Feed-URL testen.

## Zusammenarbeit
- Auf Deutsch schreiben, locker. Englische Begriffe oder Texte sind gern gesehen, Henri will sein Englisch verbessern.
- Am Anfang kurze Vorschläge machen, dann gezielt auf Henris Fragen eingehen.
- Das Projekt soll erkennbar Henris eigenes sein. Claude hilft beim Recherchieren, Strukturieren und Umsetzen. Themen, Einschätzungen und Schlüsse kommen von Henri.
- Henri hat schon mit VS Code und Python gearbeitet, Git ist neu für ihn. Git-Schritte kurz erklären, bei Python nicht bei null anfangen.
- Commits und Pushes auf GitHub nur nach Henris OK.

## Hinweise
- Der Projektordner liegt auf dem OneDrive-Desktop. Falls OneDrive Git-Dateien sperrt, den Ordner verschieben.
- Eine Kopie dieser Datei liegt im Obsidian-Vault unter `Claude\Projekte\Trading News Tracker.md`.
