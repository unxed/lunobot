# mcommander

- Задачи: тикеты https://github.com/blue-panels/mcommander (upstream; у бота там только `pull`, ни меток, ни мержа). Флот берёт
  только тикеты, заведённые владельцем или по unxed/f4#2115 (спека far2l compatibility, `docs/FAR2L_COMPAT.md` в f4);
  чужие тикеты upstream не триажит по существу и не исправляет без отдельного слова владельца (§ 2, § 3 «Делай только то, что просили»).
- Код: https://github.com/unxed/mcommander — форк blue-panels/mcommander (M-Commander, производный от Midnight Commander;
  C, сборка meson). Ветка по умолчанию `master`; issues в форке выключены (тикеты — только в upstream).
- PR: ветка `lunobot/pr/<ключ>` в форке от свежего upstream `master` → PR `unxed:lunobot/pr/<ключ>` → `blue-panels/mcommander:master`
  (`gh_post.py pr blue-panels/mcommander unxed:lunobot/pr/<ключ> master <файл>`); вливает мейнтейнер upstream, не бот.
  Влитый PR — «Пробуйте!» в тикет upstream; строки `CI.md`/`BRANCHES.md` снимает тот, кто увидел мерж.
- Как принимает upstream (из blue-panels/mcommander#347–#372, #423): мейнтейнер просит один PR на одну возможность поверх
  `master`, без стопок; часто переписывает возможность сам и закрывает PR форка (так вышло с #358 → #423, #349 → #403, #347 →
  #401/#402). Закрытый без мержа PR при влитой у него замене — не провал: сверь замену с требованием и отпишись в тикете.
  **far2l extensions мейнтейнер принимать отказался** (blue-panels/mcommander#347: «far2l extensions will not be added»);
  они целиком в открытом PR владельца blue-panels/mcommander#368 — его ведёт сам владелец: флот там не пишет и ветку не трогает (решение владельца 21-10-2026, вариант (а), постоянное правило; status/368.md). Не дублируй их новыми PR и не спорь в upstream — это решение
  владельца unxed/f4#2115 (уровень mcommander по спеке на `master` — без far2l extensions).
- Режим публикации: PR (`lunobot/staging` и `quick.yml` нет; `train.py` не применяется)
- Отладка GitHub CI: да (компилируемый C-проект; локально не собирать и не тестировать). Диагностика — push ветки
  `tmp/<4 hex узла>/<слаг>` в форк: `ci.yml` (сборки ubuntu/fedora/alpine/macos/solaris/termux/freebsd, `ci-man`) и
  `ci-ai-trailers.yml` идут на любой push; `ci-sandbox.yml` (pty-сценарии «Press the keys», `tests/misc/docker/ci.sh`) —
  `gh workflow run ci-sandbox.yml -R unxed/mcommander --ref <ветка> -f transports=local -f subjects=<…>`.
- Обязательные проверки PR: все job'ы `CI` и `AI trailers` на голове PR зелёные; `ci-sandbox` — когда правка задевает
  ввод/терминал (на PR он идёт только с меткой `sandbox`, ставит её мейнтейнер, поэтому гоняй его в форке сам и ссылку
  на зелёный прогон клади в описание PR). Полная матрица upstream — лёгкая или тяжёлая — не замерялась: до замера
  считай PR тяжёлым (§ 4, потолок (а)): на `master` upstream 24 check-run'а, `sandbox-debian-12` идёт около часа.
- **Сообщения коммитов БЕЗ упоминания ИИ**: `maint/check-ai-trailers.sh` (job `AI trailers`) красит коммит с
  `Co-Authored-By`/`Assisted-by`/`Signed-off-by`/`Generated-by`/`Helped-by`, где названы claude/anthropic/openai/codex/… ,
  и с подвалом «Generated with …». Трейлер атрибуции среды в коммиты этого проекта НЕ ставь (правило проекта сильнее);
  `Lunobot-Task:`/`Touch:` не нужны (поездов нет). В описании PR подвал допустим — проверяются только коммиты.
- Стиль коммита upstream: `<подсистема>: <Глагол с большой буквы …>` (`tty: Read a paste that comes as keys of the Win32
  input mode`, `clipboard: copy to the clipboard of the terminal by OSC 52`), тело — английский, по существу.
- Ветки владельца в форке (`far2l-*`, `far-mode-*`, `dnd-357*`, `DEV_far_alt_fast_find`, `resurrect*`, …) — ЧУЖИЕ (§ 6, § 7.3):
  не пушить, не ребейзить, не удалять. Под двумя из них открыты PR владельца в upstream: blue-panels/mcommander#368
  (`far2l-clipboard-348`: far2l extensions клиент+хост, буфер, DnD) и blue-panels/mcommander#418 (`DEV_far_alt_fast_find`:
  быстрый поиск Far по Alt+буква). Работа, которая их дополняет, — новая ветка поверх их головы и ссылка в тикете; менять их
  только по слову владельца (§ 7.3 «Гейт процесса вливания»).
- Язык общения: английский (upstream) — тикеты и PR; по языку автора тикета, если он пишет по-русски.
- Покрытие: цель не задана, процент не выдумывать.
- Уборка: `sweep.py`/`janitor.py` берут первый URL паспорта (upstream) — свои ветки `lunobot/pr/*` и `tmp/*` в форке убирает автор сам.
- Включение в `projects/INDEX.md`: последней строкой по прямому поручению владельца (unxed/lunobot#216); приоритет меняет владелец.

Паспорт создан 20-10-2026 по поручению владельца `account-216` (unxed/lunobot#216, unxed/f4#2115).
