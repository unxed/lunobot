# Красный поезд unxed/f4#1906

13-10-2026: `train.py tick-all` обнаружил падение PR поезда #1906, run https://github.com/unxed/f4/actions/runs/38443908327: `Test (windows/amd64 rest)` / `Run Tests`. В логе упали `TestShowEditor_UTF8BOMIsNotDisplayedOrLostOnSave/mapped` и `TestMappedEditor_EditsAndSaves`.

`tick-all` запустил автоматический бисект; последний запуск сообщил «бисект ещё идёт». Причина пока не подтверждена — не делать вывод о виновном коммите по логу полного прогона.

Осталось: после завершения бисекта снова вызвать `train.py tick-all`; применить его результат по § 7.2 п. 5 (либо исправить/перезапустить поезд, либо закрыть его, если виноват `main`), затем снять захват и удалить этот status-файл.
