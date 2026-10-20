# vtui: вершина staging без quick после «Merge main into lunobot/staging»

Найдено 20-10-2026 21:52 UTC (Лунобот-1, node 19d368003c6c048e43dbec70; LNX), круг tick-all.

Факт: `lunobot/staging` vtui = `2d86accf9` (Touch: unxed/f4#285, quick 39497667903 зелёный) + `274822fea` «Merge main into lunobot/staging» (сделал `train.py cut()` через REST `merges`). Дифф слияния к первому родителю пуст, поэтому push-триггер `quick` (paths-ignore) не сработал; `pick_green` не берёт `2d86accf9` (отстаёт от main), а запустить quick вручную нельзя: в `quick.yml` vtui нет `workflow_dispatch` (422). Поезд не режется, пока в staging не приземлят коммит с не-doc файлом. Тот же класс — 10-10-2026 и 14-10-2026 (комментарии в `ensure_quick_on_tip`).

Дальше (готовые задачи воркеру):
1. СДЕЛАНО 20-10-2026 21:55 UTC (Лунобот-1, node 19d368003c6c048e43dbec70; LNX): приземлено `2688cde8f201188d2e385b2b61670d56467504cc` в lunobot/staging, пуш запускает quick на новой вершине. Было: [land] unxed/vtui: добавить `workflow_dispatch:` в `on:` `.github/workflows/quick.yml` (как в unxed/f4), коммит с `Lunobot-Task: vtui-quick-dispatch`, пустой `Проверить:`, `train.py land` — этот пуш сам запускает quick на новой вершине и снимает застой.
2. ВЛИТО 20-10-2026 22:56 UTC после review (ef27875, правка ревьюера: свой не зелёный quick вершины отключает покрытие родителем). Было: ЖАЛОБА ОТКРЫТА 20-10-2026 22:00 UTC: https://github.com/unxed/lunobot/pull/217 (ветка complaint/merge-tip-no-quick, 2d71267), ждёт review отдельным субагентом перед вливанием. Было: Жалоба § 12 (PR в unxed/lunobot, ветка `complaint/merge-tip-no-quick`): в `train.py` `pick_green`/`ensure_quick_on_tip` считать зелёным слияние main в staging, если его дифф к первому родителю пуст или только из paths-ignore, а у первого родителя quick зелёный; регрессионный тест в `test_train.py`; прогон на реальных данных vtui в описании PR.
3. После 1 — проверить `train.py health unxed/vtui`, что поезд нарезан.
