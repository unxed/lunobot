# goWidgets

- Код: https://github.com/unxed/goWidgets
- Задачи: тикеты и PR этого же репозитория
- PR: туда же, ветка -> PR -> мерж в main (branch protection требует зелёных `fast`, `linux`, `windows`, `macos` CI)
- Зависимости: нет внешних, только внутренние пакеты репозитория
- Язык общения: по языку автора тикета (ru/en)
- Отладка GitHub CI: да
- Диагностический workflow: `.github/workflows/fsref.yml` (FastStone reference), `ci-gui.yml` (GUI matrix)
- Режим публикации: PR (branch protection на `main`, нет поездов)
- Покрытие: Codecov не подключен; цель — 70 % по проекту, 80 % на своих изменениях.
- Особенности:
  - CGO_ENABLED=0 — hard invariant, все FFI через purego/syscall/js
  - FastStone 5.6 — строго версия 5.6 (sha256 в spec/REFERENCE-NOTES.md)
  - Wine в CI: winetricks cc580 mandatory
  - Web/WASM: ADR-0018 (backends/web/), Playwright в ci-gui.yml
  - Branch convention: `agent/<name>/<topic>` (AGENTS.md)
  - Docs-only пуши: CI пропускает (path-ignore: `**.md`, `docs/**`, `spec/**`)
  - filelist.md — не трогать вручную