# BRANCHES — xz

Журнал намерений создания веток под lunobot/; записи сверяются с GitHub.

27-09-2026 Лунобот-3 создаёт lunobot/19d368003c6c048e43dbec70/lunobot-3/20-lzma-vbr-2of3
(для unxed/zipper#20, часть 2/3 — вплетение метрики internal/redundancy в выбор
Matcher на границах параллельных блоков Writer2, PR #2 части 1/3 уже смержен и
ветка удалена).

## Ревизия удалённых веток (27-09-2026)

Дефолтная ветка репозитория — `master` (не `main`). Проверил все ветки через
`gh api repos/unxed/xz/branches` + `git log`/`git merge-base`/`git patch-id` в
клоне /tmp/xz-review. Было 7 веток (не считая master):

- `lunobot/19d368003c6c048e43dbec70/lunobot-3/20-lzma-vbr-1of3` — НЕ ТРОГАЛ,
  активный PR #2 (zipper#20, часть 1/3), только что пофикшен, ждёт CI.

Удалены 5 веток, все объективно без уникальной ценности относительно master:

1. **codex/coverage-ci** — 0 уникальных коммитов (`git log master..branch` пусто).
   PR #1 давно смержен (0f34630). Чистое удаление слитой ветки.

2. **lzma2-parallel-writer** (1 коммит `18407e2`, "add opt-in parallel LZMA2
   compression", Workers-конфиг в отдельном writer2_parallel.go) — функциональность
   полностью перекрыта master: параллельное сжатие LZMA2 уже реализовано глубже
   и раньше прямо в lzma/writer2.go (config.Concurrency, jobs/outCh channels,
   коммиты a1f9aa6, 588d7d3, c7806fe "optimize parallel compression of
   uncompressible data", b770495 "stop the LZMA2 workers when the writer is
   closed"). Reset()-методы у binTree/hashTable/encoderDict, на которые
   ссылается коммит ветки, уже есть в master. Ветка создана от старой точки
   (6ead826, релиз v0.5.17), не видела этот функционал. PR не открывался.

3. **speedup** (4 коммита от 17-09: read-ahead в range-декодере для LZMA2-чанков,
   копирование матчей через copy(), локальные переменные в tree codec, отказ от
   heap-аллокаций на операцию) — всё это уже в master, причём с regression-тестами
   и доп. фиксами: reader2.go уже делает read-ahead для LZMA2-чанков (exact=false,
   комментарий "br limits the input to the chunk, so the decoder may read ahead"),
   decoderdict.go копирует матчи через copy(), treecodecs.go использует те же
   локальные переменные (nrange/code/pos/limit/buf), в decoder.go нет
   heap-аллокаций в хот-пути. Плюс более поздние master-коммиты 568bdb2
   (regression-тесты read-ahead), 93cee7a/cd93cf4/2b9ea3f (фиксы вокруг
   read-ahead). Ветка создана от точки задолго до всей этой перф-работы
   (merge-base = 024f909, до 45cfa6b и других перф-коммитов). PR не открывался.

4. **xz-blocks** (3 коммита: blocks.go/ParseBlocks, ParallelReader, "fail after
   Close") — master уже содержит и ParseBlocks (fd355af, ещё 17-06), и более
   зрелый ParallelReader с sync.Pool для буферов/словарей и Close() у
   blockReader (a8cbb3e, 17-06). Ветка была создана от старой точки-релиза
   (6ead826), где этой работы ещё не было, и реализует то же самое заново, но
   слабее. Нашёл единственное реальное отличие: в ветке ParseBlocks
   дополнительно проверяет `n+1 != f.indexSize` (сверка длины индекса из
   футера) — в master этой конкретной проверки в ParseBlocks нет. Это очень
   локальная защита от повреждённого футера; readIndexBody и так проверяет
   CRC32 индекса, а аналог проверки "index size in footer wrong" есть в
   основном пути чтения (reader.go:216). Не тянет на самостоятельную ценность
   ветки в целом — она вся про уже смержённый функционал. PR не открывался.

5. **xz-filters** (3 коммита) — 2 из 3 коммитов (`8a85424` "read the branch
   conversion and delta filters", `b460c3a` "compress the filter testdata with
   a small dictionary") имеют идентичный patch-id с уже смержёнными master-
   коммитами `2006db6`/`db6a2aa` (те есть в истории master). Третий коммит
   (`2ed9af3`, "keep the simple filter reader buildable with Go 1.20", правит
   `min()` на `copy()` в simplefilter.go) устарел по сути: его посыл "go.mod
   требует go1.20" был неверен уже на момент создания коммита — go.mod на
   master требует go 1.25.5 с 04-07-2026 (коммит 45cfa6b, задолго до
   17-09-2026), а в Go 1.21+ есть builtin `min`. Уникальной ценности не несёт.
   PR не открывался.

Итог: ничего не подхватывал, PR не открывал (весь потенциально полезный код
уже на master, часто в более зрелом виде). Открытых находок по пункту 3
инструкции нет.
