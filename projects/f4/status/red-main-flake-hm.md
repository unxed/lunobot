# red-main-flake-hm (не завершено)

Красный main unxed/f4 70586aaa3: прогон https://github.com/unxed/f4/actions/runs/36770446509, job «flake checks (Home Manager module)» (110075172075).
Причина: сетевой флейк, proxy.golang.org вернул stream error INTERNAL_ERROR при скачивании github.com/dsnet/compress. Не vendorHash (hash mismatch в логе нет).
Осталось: когда прогон станет completed, выполнить `gh run rerun 36770446509 -R unxed/f4 --failed`, проверить все job'ы. Если флейк повторится, добавить ретрай скачивания модулей в flake/CI (через песочницу и `land --fix-staging`).
Остановлено по слову владельца; rerun и land не выполнялись.
