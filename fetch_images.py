#!/usr/bin/env python3
"""Скачать картинки из тикета или комментария GitHub, чтобы их можно было посмотреть (Read).

Картинки из вложений (`https://github.com/user-attachments/assets/<id>`) прокси облачной среды
не пускает: «sessions are bound to their configured repositories». Но API репозитория отдаёт
тело с подписанными ссылками (`private-user-images.githubusercontent.com/...?jwt=...`,
живут минуты), и они скачиваются. Скрипт берёт тело тикета или комментария в виде HTML
(`Accept: application/vnd.github.full+json`), достаёт из него ссылки на картинки и сохраняет
файлы в каталог (по умолчанию /tmp/lunobot-1/img/<repo>-<номер>/).

    python3 fetch_images.py <owner/repo> <номер тикета>            # картинки тикета и всех его комментариев
    python3 fetch_images.py <owner/repo> <номер тикета> --comment <id>   # одного комментария
    python3 fetch_images.py <owner/repo> <номер тикета> --since 2026-10-08T00:00:00Z

Печатает пути файлов; их открывает Read (он показывает изображения).
Ссылки подписаны на несколько минут: скачивать надо сразу, не складывать ссылки в учёт.
"""
import html
import json
import os
import re
import subprocess
import sys
import urllib.request

FULL = ["-H", "Accept: application/vnd.github.full+json"]
SRC = re.compile(r'<img[^>]+src="([^"]+)"')


def gh_json(path):
    out = subprocess.run(["gh", "api", path, *FULL], capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        raise SystemExit(f"gh api {path}: {out.stderr.strip()[:300]}")
    return json.loads(out.stdout)


def urls_of(body_html):
    return [html.unescape(u) for u in SRC.findall(body_html or "")
            if "private-user-images" in u or "user-attachments" in u or "githubusercontent" in u]


def download(url, path):
    # Идёт без заголовка авторизации GitHub: подпись уже в ссылке.
    with urllib.request.urlopen(url, timeout=60) as resp, open(path, "wb") as f:
        f.write(resp.read())


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    repo, number = argv[0], argv[1]
    comment = argv[argv.index("--comment") + 1] if "--comment" in argv else None
    since = argv[argv.index("--since") + 1] if "--since" in argv else None
    out_dir = os.path.join("/tmp/lunobot-1/img", f"{repo.replace('/', '-')}-{number}")
    os.makedirs(out_dir, exist_ok=True)

    sources = []
    if comment:
        c = gh_json(f"repos/{repo}/issues/comments/{comment}")
        sources.append((f"comment-{comment}", c.get("body_html")))
    else:
        issue = gh_json(f"repos/{repo}/issues/{number}")
        if not since or (issue.get("created_at") or "") >= since:
            sources.append(("issue", issue.get("body_html")))
        page = 1
        while True:
            q = f"repos/{repo}/issues/{number}/comments?per_page=100&page={page}" + (f"&since={since}" if since else "")
            batch = gh_json(q)
            for c in batch:
                sources.append((f"comment-{c['id']}", c.get("body_html")))
            if len(batch) < 100:
                break
            page += 1

    saved = 0
    for label, body in sources:
        for i, url in enumerate(urls_of(body), 1):
            path = os.path.join(out_dir, f"{label}-{i}.png")
            try:
                download(url, path)
            except Exception as err:  # noqa: BLE001 — ссылка могла протухнуть или быть чужой
                print(f"не скачалось {label}#{i}: {err}", file=sys.stderr)
                continue
            saved += 1
            print(path)
    if not saved:
        print("картинок нет", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
