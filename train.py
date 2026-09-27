#!/usr/bin/env python3
"""Staging и поезда (§ 7.2 инструкции): единственный путь рутинной работы в main.

    train.py land                      в рабочем клоне, на своей ветке поверх lunobot/staging
    train.py tick  <owner/repo> --sign "<подпись § 9>"
    train.py eject <owner/repo> <sha>... --reason "<ссылка на упавший job>"
    train.py bisect <owner/repo> --os <раннер> --cmd "<команда песочницы>"

land  — переносит твои коммиты (origin/lunobot/staging..HEAD) на вершину staging и пушит,
        с повторами при гонке. PR не открывает никогда.
tick  — идемпотентный шаг проводника; запускай в начале каждого круга. Поезд в пути: зелёный —
        вливает (fast-forward main, иначе merge-коммит), красный — печатает, кого выкидывать;
        поезда нет, а staging созрел — режет новый поезд и открывает за него PR.
bisect — вручную, когда падение платформенное/узкое и автоматический бисект (`go test ./...` на
        ОС упавшего job'а) его не ловит: свой раннер и своя команда. Результат разбирает tick.
eject — ревертит в staging коммиты-виновники красного поезда и закрывает его PR; следующий
        tick сразу режет новый поезд без них.

Коды возврата: 0 — всё штатно (в т.ч. «поезд ещё едет»), 1 — нужна работа человека/бота
(конфликт, красный поезд без выкидывания), 2 — ошибка использования.
"""
import json
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

STAGING = "lunobot/staging"
TRAIN_PREFIX = "lunobot/train/"
MIN_COMMITS = 5
MAX_AGE_MIN = 30
# Прогоны main здесь не отменяются никогда — решение владельца («Preserve every main run»).
PRESERVE_MAIN = {"unxed/vtui"}
TRAILER = re.compile(r"^(Touch|Lunobot-Task):\s*(.+)$", re.M)
CHECK = re.compile(r"^Проверить:\s*\n(.*?)(?:\n\s*\n[A-Z][\w-]+:|\Z)", re.M | re.S)


def run(*cmd, check=True, cwd=None):
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if check and p.returncode:
        sys.exit(f"{' '.join(cmd)}: {p.stderr.strip() or p.stdout.strip()}")
    return p


def api(path, *args, check=True):
    p = run("gh", "api", path, *args, check=check)
    return json.loads(p.stdout) if p.stdout.strip() else None


def land():
    run("git", "fetch", "-q", "origin", STAGING)
    commits = run("git", "log", "--format=%H%x00%B%x01", f"origin/{STAGING}..HEAD").stdout
    msgs = [c.split("\0", 1) for c in commits.split("\x01") if c.strip()]
    if not msgs:
        sys.exit("нечего приземлять: HEAD не впереди origin/lunobot/staging")
    bad = [sha[:9] for sha, body in msgs if not TRAILER.search(body)]
    if bad:
        sys.exit(f"коммиты без трейлера Touch:/Lunobot-Task: {', '.join(bad)} — проводник не "
                 "сможет разнести «Пробуйте!» по тикетам; допиши трейлер (git commit --amend)")
    for attempt in range(6):
        if run("git", "rebase", "-q", f"origin/{STAGING}", check=False).returncode:
            run("git", "rebase", "--abort", check=False)
            sys.exit("конфликт при переносе на staging — разреши его сам (git rebase "
                     "origin/lunobot/staging), это твой код, и запусти land снова")
        if run("git", "push", "-q", "origin", f"HEAD:{STAGING}", check=False).returncode == 0:
            print(f"приземлено в {STAGING}: {len(msgs)} коммит(ов), вершина "
                  f"{run('git', 'rev-parse', 'HEAD').stdout.strip()}")
            return 0
        time.sleep(2 + 3 * attempt)
        run("git", "fetch", "-q", "origin", STAGING)
    sys.exit("staging шесть раз подряд ушёл вперёд — повтори land чуть позже")


def train_pr(repo):
    prs = api(f"repos/{repo}/pulls?state=open&per_page=100")
    trains = [p for p in prs if p["head"]["ref"].startswith(TRAIN_PREFIX)]
    return trains[0] if trains else None


def rollup(repo, number):
    out = run("gh", "pr", "view", str(number), "--repo", repo,
              "--json", "statusCheckRollup").stdout
    checks = json.loads(out)["statusCheckRollup"]
    pending = [c for c in checks if c.get("status", "COMPLETED") != "COMPLETED"
               or c.get("state") == "PENDING"]
    failed = [c for c in checks if (c.get("conclusion") or c.get("state"))
              in ("FAILURE", "TIMED_OUT", "STARTUP_FAILURE", "ERROR", "ACTION_REQUIRED")]
    cancelled = [c for c in checks if c.get("conclusion") == "CANCELLED"]
    return checks, pending, failed, cancelled


def compare(repo, base, head):
    return api(f"repos/{repo}/compare/{base}...{head}")


def tickets(repo, commits):
    """{ключ: [тексты «Проверить»]} по трейлерам коммитов поезда."""
    out = {}
    for c in commits:
        msg = c["commit"]["message"]
        if len(c.get("parents", [])) > 1:
            continue
        chk = CHECK.search(msg)
        for kind, val in TRAILER.findall(msg):
            key = val.strip()
            if kind == "Touch" and key.startswith("#"):
                key = f"{repo}{key}"
            out.setdefault(key, [])
            if chk:
                out[key].append(chk.group(1).strip())
    return out


def cut(repo, sign):
    main_sha = api(f"repos/{repo}/branches/main")["commit"]["sha"]
    staging = api(f"repos/{repo}/branches/{STAGING}", check=False)
    if not staging or "commit" not in staging:
        sys.exit(f"нет ветки {STAGING} в {repo}")
    cmp = compare(repo, main_sha, staging["commit"]["sha"])
    if cmp["behind_by"]:
        r = run("gh", "api", f"repos/{repo}/merges", "-f", f"base={STAGING}", "-f", "head=main",
                "-f", "commit_message=Merge main into lunobot/staging", check=False)
        if r.returncode:
            print(f"main не вливается в staging без конфликта — срочная работа (§ 5 п. 2): "
                  f"разреши вручную в клоне и запушь в {STAGING}\n{r.stderr.strip()}")
            return 1
        print("влил main в staging (там были коммиты мимо поезда)")
        return tick(repo, sign)
    own = [c for c in cmp["commits"] if len(c["parents"]) == 1]
    if not own:
        print("staging не впереди main — резать нечего")
        return 0
    oldest = min(datetime.fromisoformat(c["commit"]["committer"]["date"].replace("Z", "+00:00"))
                 for c in own)
    age = (datetime.now(timezone.utc) - oldest).total_seconds() / 60
    if len(own) < MIN_COMMITS and age < MAX_AGE_MIN:
        print(f"staging: {len(own)} коммит(ов), старшему {age:.0f} мин — поезд ещё не созрел "
              f"(порог {MIN_COMMITS} коммитов или {MAX_AGE_MIN} мин)")
        return 0
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    project = repo.split("/")[1]
    branch = f"{TRAIN_PREFIX}{project}/{stamp}"
    api(f"repos/{repo}/git/refs", "-f", f"ref=refs/heads/{branch}",
        "-f", f"sha={staging['commit']['sha']}")
    tk = tickets(repo, own)
    short = [k.replace(f"{repo}#", "#") for k in tk]
    title = f"Поезд {project} {stamp}: " + (", ".join(short) if short else f"{len(own)} коммитов")
    body = [f"Поезд из `{STAGING}` ({len(own)} коммитов). Собран `train.py` — отдельных "
            "бот-PR больше нет, всё рутинное едет так (LUNOBOT.md § 7.2).", ""]
    for key, texts in tk.items():
        body.append(f"### {key}")
        body += texts or ["(автор не оставил блока «Проверить:»)"]
        if key.startswith(f"{repo}#"):
            body.append(f"\nTouch #{key.split('#')[1]}")
        elif "#" in key:
            body.append(f"\nTouch {key}")
        body.append("")
    body.append(sign)
    body.append("\n🤖 Generated with [Claude Code](https://claude.com/claude-code)")
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write("\n".join(body)[:65000])
    url = run("gh", "pr", "create", "--repo", repo, "--base", "main", "--head", branch,
              "--title", title[:250], "--body-file", f.name).stdout.strip()
    print(f"поезд отправлен: {url} ({len(own)} коммитов, {len(tk)} тикетов/задач)")
    return 0


def train_commits(repo, pr):
    return [c for c in compare(repo, pr["base"]["sha"], pr["head"]["sha"])["commits"]
            if len(c["parents"]) == 1]


def guess_os(name):
    n = (name or "").lower()
    if "windows" in n:
        return "windows-11-arm" if "arm64" in n else "windows-latest"
    if "darwin" in n or "macos" in n:
        return "macos-15-intel" if "amd64" in n else "macos-latest"
    if "arm64" in n:
        return "ubuntu-24.04-arm"
    return "ubuntu-latest"


def bisect(repo, pr, os_label, cmd):
    """Параллельный бисект: по ветке и прогону песочницы на КАЖДЫЙ префикс поезда сразу."""
    for i, c in enumerate(train_commits(repo, pr)):
        ref = f"bisect/{pr['number']}/{i:02d}-{c['sha'][:9]}"
        api(f"repos/{repo}/git/refs", "-f", f"ref=refs/heads/{ref}", "-f", f"sha={c['sha']}",
            check=False)
        run("gh", "workflow", "run", "sandbox.yml", "--repo", repo, "--ref", ref,
            "-f", f"os={os_label}", "-f", f"command={cmd}")
    print(f"бисект запущен: {os_label}, `{cmd}` — результат разберёт следующий tick")


def bisect_refs(repo, n):
    refs = api(f"repos/{repo}/git/matching-refs/heads/bisect/{n}/") or []
    return sorted(r["ref"].removeprefix("refs/heads/") for r in refs)


def drop_bisect(repo, refs):
    for ref in refs:
        api(f"repos/{repo}/git/refs/heads/{ref}", "-X", "DELETE", check=False)


def red(repo, pr, failed):
    """Красный поезд. Виновника определяет механика, не суждение бота:
    1) один перезапуск упавших job'ов — флейк отсеивается сам;
    2) снова красный — параллельный бисект песочницей по префиксам поезда;
    3) первый падающий префикс — виновник, выкидывается автоматически;
    4) бисект ничего не воспроизвёл — ещё один полный перезапуск; красный и после него —
       срочная задача одному боту (§ 5 п. 2), staging при этом не замораживается."""
    n = pr["number"]
    names = [c.get("name") or c.get("context") for c in failed]
    print(f"поезд #{n} КРАСНЫЙ: {', '.join(names)}")
    refs = bisect_refs(repo, n)
    if refs:
        verdict = []
        for ref in refs:
            runs = api(f"repos/{repo}/actions/runs?branch={ref}&event=workflow_dispatch")["workflow_runs"]
            verdict.append((ref, runs[0] if runs else None))
        if any(r is None or r["status"] != "completed" for _, r in verdict):
            print("бисект ещё идёт")
            return 0
        bad = [ref for ref, r in verdict if r["conclusion"] != "success"]
        drop_bisect(repo, refs)
        if bad:
            sha = next(c["sha"] for c in train_commits(repo, pr)
                       if c["sha"].startswith(bad[0].rsplit("-", 1)[1]))
            print(f"бисект: первый падающий префикс {bad[0]} — виновник {sha[:9]}")
            return eject(repo, [sha], f"бисект по {pr['html_url']}, первым падает {sha[:9]}")
        attempt = attempts(failed)
        if attempt < 3:
            rerun(failed)
            print("бисект не воспроизвёл падение ни на одном префиксе — похоже на флейк/"
                  "платформу; поезд перезапущен ещё раз")
            return 0
        print("красный и после бисекта и двух перезапусков — срочная задача одному боту "
              "(§ 5 п. 2): разобрать падение; остальные продолжают приземлять в staging")
        return 1
    if attempts(failed) < 2:
        rerun(failed)
        print("первый перезапуск упавших job'ов — отсеиваем флейк")
        return 0
    bisect(repo, pr, guess_os(names[0]), "go test -count=1 ./...")
    return 0


def attempts(failed):
    out = 1
    for c in failed:
        m = re.search(r"github\.com/([^/]+/[^/]+)/actions/runs/(\d+)", c.get("detailsUrl") or "")
        if m:
            r = api(f"repos/{m.group(1)}/actions/runs/{m.group(2)}", check=False)
            if r:
                out = max(out, r.get("run_attempt", 1))
    return out


def rerun(failed):
    for c in failed:
        m = re.search(r"github\.com/([^/]+/[^/]+)/actions/runs/(\d+)", c.get("detailsUrl") or "")
        if m:
            run("gh", "run", "rerun", m.group(2), "--failed", "--repo", m.group(1), check=False)


def tick(repo, sign):
    pr = train_pr(repo)
    if not pr:
        return cut(repo, sign)
    n, head = pr["number"], pr["head"]["sha"]
    checks, pending, failed, cancelled = rollup(repo, n)
    if failed:
        return red(repo, pr, failed)
    if pending:
        print(f"поезд #{n} в пути: {len(pending)} из {len(checks)} проверок ещё идут")
        return 0
    if cancelled:
        runs = {re.search(r"/runs/(\d+)", c.get("detailsUrl", "") or "") for c in cancelled}
        for m in runs - {None}:
            run("gh", "run", "rerun", m.group(1), "--failed", "--repo", repo, check=False)
        print(f"поезд #{n}: {len(cancelled)} проверок отменены (не упали) — перезапустил")
        return 0
    ff = run("gh", "api", "-X", "PATCH", f"repos/{repo}/git/refs/heads/main",
             "-f", f"sha={head}", "-F", "force=false", check=False)
    if ff.returncode == 0:
        how = "fast-forward"
        if repo not in PRESERVE_MAIN:
            time.sleep(5)
            for r in api(f"repos/{repo}/actions/runs?branch=main&head_sha={head}")["workflow_runs"]:
                if r["event"] == "push" and r["status"] != "completed":
                    run("gh", "run", "cancel", str(r["id"]), "--repo", repo, check=False)
        api(f"repos/{repo}/git/refs/heads/{pr['head']['ref']}", "-X", "DELETE", check=False)
    else:
        run("gh", "pr", "merge", str(n), "--repo", repo, "--merge", "--delete-branch")
        how = "merge-коммит (main ушёл вперёд — прогон main не отменять, § 7.3)"
    print(f"поезд #{n} ВЛИТ ({how}). Теперь по каждому тикету — «Пробуйте!» с текстом ниже "
          "и подписью (§ 7.3, § 9), TRIAGE → проверяют:")
    for key, texts in tickets(repo, compare(repo, pr["base"]["sha"], head)["commits"]).items():
        print(f"--- {key}")
        for t in texts:
            print(t)
    return 0


def eject(repo, shas, reason):
    pr = train_pr(repo)
    with tempfile.TemporaryDirectory() as d:
        run("git", "clone", "-q", "--filter=blob:none", "--branch", STAGING,
            f"https://github.com/{repo}.git", d)
        for sha in shas:
            r = run("git", "revert", "--no-edit", sha, cwd=d, check=False)
            if r.returncode:
                sys.exit(f"revert {sha} не лёг чисто — ревертни руками в клоне staging")
            msg = run("git", "log", "-1", "--format=%B", cwd=d).stdout
            run("git", "commit", "-q", "--amend", "-m",
                f"{msg.rstrip()}\n\nВыкинут из поезда: {reason}", cwd=d)
        run("git", "push", "-q", "origin", f"HEAD:{STAGING}", cwd=d)
    if pr:
        drop_bisect(repo, bisect_refs(repo, pr["number"]))
        run("gh", "pr", "close", str(pr["number"]), "--repo", repo, "--delete-branch",
            "--comment", f"Красный поезд; выкинуты из staging: {', '.join(s[:9] for s in shas)} "
            f"({reason}). Следующий поезд режется без них.")
    print("выкинуто; авторам — вернуть тикет в работу с этой ссылкой (§ 7.2)")
    return 0


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    cmd, rest = argv[0], argv[1:]
    opt = lambda k: rest[rest.index(k) + 1] if k in rest else None
    if cmd == "land":
        return land()
    if cmd == "tick" and rest and opt("--sign"):
        return tick(rest[0], opt("--sign"))
    if cmd == "bisect" and rest and opt("--os") and opt("--cmd"):
        pr = train_pr(rest[0])
        if not pr:
            sys.exit("поезда в пути нет")
        bisect(rest[0], pr, opt("--os"), opt("--cmd"))
        return 0
    if cmd == "eject" and len(rest) >= 2 and opt("--reason"):
        shas = [a for a in rest[1:rest.index("--reason")]]
        return eject(rest[0], shas, opt("--reason"))
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
