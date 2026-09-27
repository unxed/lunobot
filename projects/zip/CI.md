# CI — zip

Прогоны, которые запущены и результат которых не проверен. Формат — § 14.2 инструкции.

27-09-2026 16:35:00 Лунобот-3, тикет [#1](https://github.com/unxed/zip/issues/1) (регрессионный тест, код уже исправлен коммитом c321598), PR [#17](https://github.com/unxed/zip/pull/17), коммит `ef02bb8` (фикс gosec G115 в тесте), жду прогон

27-09-2026 04:41:14 Лунобот-3, тикет [#5](https://github.com/unxed/zip/issues/5) (Extractor не ограничивает суммарный объём распакованных данных — добавлен WithExtractorMaxTotalSize), PR [#16](https://github.com/unxed/zip/pull/16), коммит `db33f87`, жду прогон

27-09-2026 04:41:14 Лунобот-3, тикет [#6](https://github.com/unxed/zip/issues/6) (device nodes и uid/gid при распаковке под root теперь opt-in — WithExtractorDeviceNodes/WithExtractorPreserveOwner), PR [#18](https://github.com/unxed/zip/pull/18), коммит `4960fcf`, жду прогон

27-09-2026 18:35:00 Лунобот-3, кастомная задача (main красный на джобе Coverage, 11 непокрытых строк — добито тестами по явной просьбе владельца), PR [#19](https://github.com/unxed/zip/pull/19), коммит `f844b96`, жду прогон
