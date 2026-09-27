# xz #2 (PR) - CI tracking

- Тикет-источник: https://github.com/unxed/zipper/issues/20 (VBR-эвристики
  сжатия LZMA); подробности изучения кода и разбивки на части — в
  ../zipper/CI.md
- PR: https://github.com/unxed/xz/pull/2
- Branch: lunobot/19d368003c6c048e43dbec70/lunobot-3/20-lzma-vbr-1of3
- Содержимое: новый пакет internal/redundancy (метрики Entropy и
  DuplicateRatio + Analyze/EstimateRedundancy), юнит-тесты. Никаких
  изменений в lzma-энкодере, WriterConfig/Writer2Config — пакет не
  подключён к реальному выбору параметров сжатия (это часть 2/3).
- Local checks before push: none — go test/go vet не запускались локально
  (политика "no local builds"), оставлено CI (go-test-platforms.yml:
  go test -race ./... на Linux/Windows, GOARCH=386; coverage.yml).
- Per process note: пушнул ветку и открыл PR, затем остановился — CI не
  опрашивался в этом шаге. Следующий шаг — проверить
  https://github.com/unxed/xz/actions по этому PR.
- Status: awaiting CI.
