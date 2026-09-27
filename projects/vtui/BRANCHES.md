# BRANCHES — vtui

Ветки, заведённые Луноботами. Записывается ДО создания ветки, удаляется ПОСЛЕ её
физического удаления на GitHub. Формат и смысл расхождений — § 14.3 инструкции.

26-09-2026 07:26:30 Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), ветка `codex/19d368003c6c048e43dbec70/lunobot-3/1432-1of1` для https://github.com/unxed/f4/issues/1432 (уже создана и запушена — регистрация задним числом)
26-09-2026 07:26:30 Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), ветка `codex/19d368003c6c048e43dbec70/lunobot-3/285-1of1` для https://github.com/unxed/f4/issues/285 (следующий срез: символьные токены чекбокса/радио, см. issuecomment-5818276386)
26-09-2026 08:44:57 Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), ветка `codex/19d368003c6c048e43dbec70/lunobot-3/285-2of2` для https://github.com/unxed/f4/issues/285 (токены "ушей" кнопки)
26-09-2026 14:20:00 Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), ветка `codex/19d368003c6c048e43dbec70/lunobot-3/285-3of3` для https://github.com/unxed/f4/issues/285 (геометрия чекбокса/радио под GlyphStyleRounded)

27-09-2026 17:10:00 Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), ревизия веток vtui по § 10 (прямая просьба владельца). Удалены с GitHub (`gh api -X DELETE git/refs/heads/...`), для каждой проверено через `git log`/`gh pr view`, что уникальной ценности нет:
  - `363-color-validator` — PR #140 MERGED (squash `5310f05`); единственный уникальный коммит ветки (`17369b7`) содержательно идентичен squash-коммиту на main, ветка сама отстаёт от main (нет ChatWindow и др.)
  - `363-harsh-clash-min-lightness` — PR #144 MERGED, 0 коммитов впереди main
  - `363-tune-harsh-clash` — PR #143 MERGED, 0 коммитов впереди main
  - `ci-serialize-bot-prs` — PR #145 CLOSED (не смержен); владелец явно отклонил в комментарии (баг с отменой QUEUED джобов GH Actions, тот же фикс на f4 пришлось откатывать, см. f4#1534) — тема решена отказом, main не содержит и не должен содержать это изменение
  - `lunobot/batch/vtui/1` — 0 коммитов впереди main (единственный коммит, codecov OIDC upload, ушёл прямым пуш в main без PR); счётчик пачки исчерпан, следующая пачка получит новый номер
  Удалена регистрация этой ветки ниже (была записана до создания, теперь физически удалена).
  Не тронуты: `lunobot/f33f64cd91460430a21da326/lunobot-1/window-app-id` (PR #146 OPEN, чужой активный захват — lunobot-1, не трогаю) и три `136-gui-font-hotswap-*` (PR #148/#149/#150 OPEN, явно защищены в задаче).

27-09-2026 04:05:00 Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), ветка `lunobot/19d368003c6c048e43dbec70/lunobot-3/136-gui-font-hotswap-1of4` для https://github.com/unxed/vtui/issues/136 (часть 1 из 4 — Wayland)

27-09-2026 15:20:00 Лунобот-3 (node 19d368003c6c048e43dbec70; LNX), ветка `lunobot/19d368003c6c048e43dbec70/lunobot-3/136-gui-font-hotswap-3of4` для https://github.com/unxed/vtui/issues/136 (часть 3 из 4 — win32)
