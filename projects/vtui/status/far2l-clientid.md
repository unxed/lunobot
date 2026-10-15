# vtui: clientID far2l-расширений (§ 5 п. 5а.9)

15-10-2026 03:49 (Лунобот-1, node 19d368003c6c048e43dbec70): локальный коммит c1fa4e5 в клоне /tmp/lunobot-1/vtui (ветка lunobot-local-clientid), ещё не приземлён. Новый файл far2l_clientid.go (случайный ID в os.UserConfigDir()/<AppName>/far2l-client-id, 0600; без каталога — случайный на процесс), тесты far2l_clientid_test.go, far2l_extensions.go использует far2lClientID() вместо константы.

Осталось: прогон песочницы (go vet, go test ./ -run Far2lClientID, golangci-lint обоих профилей) по ветке tmp/19d3/vtui-clientid, затем `train.py land` из /tmp/lunobot-1/vtui; удалить этот файл и пункт 9 из § 5 п. 5а инструкции (жалоба по § 12).
