# CI — vtui

Прогоны, которые запущены и результат которых не проверен. Формат — § 14.2 инструкции.
10-10-2026 (Лунобот-1): поезд vtui #204 (только autocomplete, f4#1855) красный на Test (darwin/amd64): TestProtocol_PipeClosureTeardown «protocol session did not stop after pipe closure» (ожидание 1 с; рядом в логе стеки panic_bridge_test). Коммит поезда протокол не трогает; tick сделал первый перезапуск (run 38042110099). Если упадёт снова — разбирать как настоящую ошибку (Serve не выходит по EOF под нагрузкой или таймаут 1 с мал для macOS-раннера).
