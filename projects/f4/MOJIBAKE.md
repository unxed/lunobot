# Испорченные комментарии в unxed/f4

Пишет janitor (`janitor.py`, шаг 4). Эти комментарии дошли до GitHub с «?» на месте букв. Восстанови текст правкой того же комментария через `gh_post.py edit unxed/f4 <id> <файл>`, а строки «тело тикета/PR» — через `gh_post.py pr-body` или `gh_post.py issue-body` (команда указана в строке), по ASCII-остову, соседним сообщениям и учёту — строка пропадёт на следующем проходе janitor. LUNOBOT.md § 2.

- https://github.com/unxed/f4/pull/1969 (#1969, тело тикета/PR, unxed, 2026-10-15T20:36:58Z): в тексте буквальные \n вместо переводов строк; чинить: `gh_post.py pr-body unxed/f4 1969 <файл>`
- https://github.com/unxed/f4/issues/1966 (#1966, тело тикета/PR, tarlabnor, 2026-10-15T20:27:14Z): в тексте буквальные \n вместо переводов строк; чинить: `gh_post.py issue-body unxed/f4 1966 <файл>`
