# dn: push-прогоны на ветках lunobot/pr/* дублируют PR-прогоны (§ 4 п. 6)

14-10-2026 08:06 (Лунобот-1): пуш в ветку PR unxed/dn#49 запустил и PR-прогоны, и push-прогоны dn/dn-linux/dn-windows того же коммита. Фикс: в `dn.yml`, `dn-linux.yml`, `dn-windows.yml` под `push` — `branches-ignore: ['lunobot/**']` и `tags: ['**']` (теги как раньше). layout/toolchain не тронуты: у них нет `pull_request`, push — их единственная проверка до мержа. Локальный коммит `99fddea` в `/tmp/lunobot-1/work/dn-ci-1014-0759/dn` (ветка `lunobot/pr/ci-no-dup-push`).

08:07: запушено, PR unxed/dn#53, прогоны в CI.md. Push-прогонов dn/dn-linux/dn-windows на самой ветке уже нет (только pull_request) — правка работает.

Осталось: после зелёных PR-прогонов влить unxed/dn#53, записать прогон main в CI.md; status удалить.
