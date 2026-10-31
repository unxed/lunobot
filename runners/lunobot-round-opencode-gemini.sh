#!/usr/bin/env bash
# lunobot-round-opencode-gemini.sh — круги Lunobot по схеме «роутер»: бесплатная модель opencode только
# запускает ОДНУ команду `aistudio drive` и пересказывает её вывод (не читает, не думает, не выбирает работу);
# ВСЁ мышление, включая чтение LUNOBOT.md и весь круг, делает Gemini (веб-интерфейс AI Studio, `aistudio`
# из unxed/AI, skills/aistudio-offload), а команды, которые он просит, выполняет сам движок.
# `--check` — только проверка предусловий (opencode, gh, aistudio, jq, flock) и выход.

set -euo pipefail

export LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUTF8=1
export NO_PROXY=127.0.0.1,localhost
# git никогда не спрашивает логин/пароль в терминале: без помощника gh push падает сразу, а не виснет
export GIT_TERMINAL_PROMPT=0

# ── настройки ─────────────────────────────────────────────────────────
# Роутер — бесплатная модель opencode (`opencode models | grep free`), переопределяется переменной.
# glm-5.3-flash-free: бесплатна сейчас, класс Flash/Haiku (LUNOBOT.md § 1: «легче» Sonnet/Terra ->
# Лунобот-2), а сама она только маршрутизирует: всю работу делает Gemini.
MODEL="${LUNOBOT_ROUTER_MODEL:-${LUNOBOT_MANAGER_MODEL:-opencode/glm-5.3-flash-free}}"   # provider/model#variant
MANAGER_ID="$(basename "${MODEL%%#*}")"   # id роутера для OFFLOAD_CALLER и подписи
SESSION_NAME="lunobot-2"               # имя сессии (Lunobot-2)
BOT_NUMBER=2                           # неизвестный/лёгкий класс -> 2; общий lock с muse и luna-high
ROUND_TIMEOUT=3600                     # Gemini медленнее: aistudio code до 900 с на попытку
AI_REPO="${AI_REPO:-${HOME}/AI-repo}"  # клон unxed/AI (агент drive-router для opencode)
export PATH="${HOME}/.npm-global/bin:${HOME}/.local/bin:${PATH}"
WORKDIR="${HOME}"
INTERVAL_MIN=15
MAX_RETRIES=3
RETRY_DELAY=60
TOKEN_LIMIT_WAIT=120                   # ожидание сброса квоты токенов (сек)
LOG_DIR="${HOME}/.lunobot/logs-opencode-gemini"
mkdir -p "${LOG_DIR}"
ACTIVE_PID=""
ACTIVE_PGID=""
ACTIVE_TAIL_PID=""
ACCOUNTING_REPO="${LUNOBOT_ACCOUNTING:-unxed/lunobot}"
CLAIMS_DIRTY=0   # 1 — круг запускался, а его захваты ещё не сняты

# ── ротация логов ────────────────────────────────────────────────────
rotate_logs() {
  find "${LOG_DIR}" -name 'round-*.log' -type f -printf '%T@ %p\n' 2>/dev/null \
    | sort -n | head -n -50 | cut -d' ' -f2- | xargs -r rm -f
  find "${LOG_DIR}" -name 'round-*.log' -type f -mtime +7 -exec gzip -f {} \; 2>/dev/null || true
}

# ── вспомогательные ──────────────────────────────────────────────────
log() { echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] $*" | tee -a "${LOG_DIR}/lunobot.log"; }

acquire_runner_lock() {
  mkdir -p "/tmp/lunobot-${BOT_NUMBER}"
  exec 9>"/tmp/lunobot-${BOT_NUMBER}/runner.lock"
  if ! flock -n 9; then
    log "ERROR: another Lunobot-${BOT_NUMBER} runner is already active on this node"
    return 1
  fi
}

# проверка на ошибку исчерпания токенов в выводе
check_token_limit() {
  local log_file="$1"
  # лог — opencode --format json: смотрим только события error и строки вне JSON (stderr), не текст тикетов в выводе инструментов
  jq -Rr '(fromjson? // null) as $j | if $j == null then . elif $j.type == "error" then ($j | tostring) else empty end' \
    "${log_file}" 2>/dev/null \
    | grep -qi -E "rate limit|token limit|quota exceeded|too many tokens|429 Too Many Requests|insufficient quota|billing"
}

# ожидание сброса квоты с прогресс-баром
wait_token_reset() {
  local wait_time="$1"
  log "Token limit hit. Waiting ${wait_time}s for quota reset..."
  local elapsed=0
  while (( elapsed < wait_time )); do
    printf "\r[%3d/%3ds] " $((wait_time - elapsed)) "${wait_time}"
    sleep 5
    ((elapsed += 5))
  done
  echo
  log "Quota wait complete, retrying..."
}

# ── после круга: снять захваты (LUNOBOT.md § 1: круг раннера — сессия, после него захватов нет)
# и записать метрики круга в журнал инстанса (journal.py, § 4 п. 6: рефлексия).
# Свежий одноразовый клон учёта, а не /tmp/lunobot-<N>/accounting: круг могли убить посреди git в нём.
release_claims() {
  local reason="$1" log_file="${2:-}" round_num="${3:-}" exit_code="${4:-}" duration="${5:-}" tmp rc=0
  tmp="$(mktemp -d "${TMPDIR:-/tmp}/lunobot-release.XXXXXX")" || return 1
  if timeout 120 gh repo clone "${ACCOUNTING_REPO}" "${tmp}/accounting" -- --depth=50 -q >/dev/null 2>&1 \
     && git -C "${tmp}/accounting" config user.name "Лунобот-${BOT_NUMBER}" \
     && git -C "${tmp}/accounting" config user.email lunobot@users.noreply.github.com \
     && timeout 120 python3 "${tmp}/accounting/tools/release.py" --number "${BOT_NUMBER}" --reason "${reason}" \
          2>&1 | tee -a "${LOG_DIR}/lunobot.log"; then
    CLAIMS_DIRTY=0
    if [[ -n "${log_file}" ]]; then
      timeout 120 python3 "${tmp}/accounting/tools/journal.py" round "${log_file}" --number "${BOT_NUMBER}" \
        --runner "$(basename "$0")" --model "${MODEL}" --round "${round_num}" --exit "${exit_code}" \
        --duration "${duration}" >>"${LOG_DIR}/lunobot.log" 2>&1 \
        || log "WARNING: round metrics not journaled"
    fi
  else
    rc=1
    log "WARNING: claims of Lunobot-${BOT_NUMBER} not released; janitor.py will drop them later"
  fi
  rm -rf -- "${tmp:?}"
  return "${rc}"
}

stop_active_round() {
  local signal_name="$1"
  local exit_status="$2"
  local self_pgid
  self_pgid="$(ps -o pgid= -p "$$" 2>/dev/null | tr -d ' ' || true)"
  trap - INT TERM
  log "Received ${signal_name}; stopping only this round's process group"

  if [[ -n "${ACTIVE_PGID}" && "${ACTIVE_PGID}" != "${self_pgid}" && "${ACTIVE_PGID}" != 1 ]]; then
    kill -TERM -- "-${ACTIVE_PGID}" 2>/dev/null || true
    sleep 2
    kill -KILL -- "-${ACTIVE_PGID}" 2>/dev/null || true
  elif [[ -n "${ACTIVE_PID}" ]]; then
    # Never signal our own terminal/process group if setsid did not isolate the child.
    kill -TERM "${ACTIVE_PID}" 2>/dev/null || true
    sleep 2
    kill -KILL "${ACTIVE_PID}" 2>/dev/null || true
  fi
  if [[ -n "${ACTIVE_PID}" ]]; then wait "${ACTIVE_PID}" 2>/dev/null || true; fi
  if [[ -n "${ACTIVE_TAIL_PID}" ]]; then
    kill -TERM "${ACTIVE_TAIL_PID}" 2>/dev/null || true
    wait "${ACTIVE_TAIL_PID}" 2>/dev/null || true
  fi
  if (( CLAIMS_DIRTY )); then
    release_claims "раннер остановлен (${signal_name})" || true
  fi
  exit "${exit_status}"
}

# ── предусловия: без них ни одного круга ──────────────────────────────
check_prereqs() {
  local bad=0 c
  for c in opencode gh jq flock curl git python3 timeout; do
    if ! command -v "${c}" >/dev/null 2>&1; then
      echo "MISSING: ${c} не найден в PATH" >&2; bad=1
    fi
  done
  if command -v gh >/dev/null 2>&1 && ! gh auth status >/dev/null 2>&1; then
    echo "MISSING: gh не авторизован — выполни: gh auth login" >&2; bad=1
  elif command -v gh >/dev/null 2>&1 && ! git config --global --get-regexp '^credential\..*helper' 2>/dev/null | grep -q 'gh auth git-credential'; then
    # без помощника git push по https спрашивает логин, хотя gh авторизован
    if gh auth setup-git >/dev/null 2>&1; then
      echo "NOTE: git настроен брать учётные данные у gh (gh auth setup-git)" >&2
    else
      echo "MISSING: git не берёт учётные данные у gh — выполни: gh auth setup-git" >&2; bad=1
    fi
  fi
  if ! command -v aistudio >/dev/null 2>&1; then
    echo "MISSING: aistudio не установлен — git clone https://github.com/unxed/AI ~/AI-repo && ~/AI-repo/skills/aistudio-offload/install.sh" >&2
    bad=1
  elif ! aistudio status 2>/dev/null | grep -q 'logged_in=True'; then
    cat >&2 <<'MSG'
MISSING: браузер оффлоадинга не залогинен в Google (aistudio status: logged_in=False).
  Запусти `aistudio login` (в фоне) и открой http://127.0.0.1:8766/ — войди в Google (клик по полю на картинке,
  текст в верхнее поле, Enter). На удалённой машине сначала на своём компьютере: ssh -L 8766:127.0.0.1:8766 <этот-хост>.
  Пароль за владельца не вводить. Альтернатива: `aistudio export-cookies > c.json` там, где вход есть,
  `aistudio import-cookies c.json` здесь (файл секретный, потом удалить).
MSG
    bad=1
  fi
  if command -v opencode >/dev/null 2>&1 && ! opencode models 2>/dev/null | grep -qxF "${MODEL%%#*}"; then
    echo "MISSING: модель ${MODEL%%#*} не найдена в 'opencode models' (задай LUNOBOT_ROUTER_MODEL=...)" >&2; bad=1
  fi
  return "${bad}"
}

# агент drive-router (opencode) из unxed/AI (справочно; сам круг запускается через `opencode run` с минимальным промптом)
install_router_agent() {
  local src="${AI_REPO}/skills/aistudio-offload/agents/opencode/drive-router.md"
  local dst="${HOME}/.config/opencode/agent/drive-router.md"
  if [[ -f "${src}" ]]; then
    mkdir -p "$(dirname "${dst}")"
    cmp -s "${src}" "${dst}" 2>/dev/null || cp -f "${src}" "${dst}"
  fi
}

# Жёсткий гейт роутера: плагин opencode (tool.execute.before) прогоняет каждый вызов инструмента
# через `aistudio guard` (режим роутера: разрешена одна команда `aistudio ...`, остальные инструменты блокируются; exit 2 — блок).
# Имена и аргументы инструментов opencode переводятся в формат Claude Code. Сбой гейта = блок (fail closed).
GATE_DIR="${HOME}/.lunobot/gate"
install_router_gate() {
  mkdir -p "${GATE_DIR}"
  cat >"${GATE_DIR}/router-gate.js" <<'JS'
import { spawnSync } from "node:child_process"
const TOOL = { bash: "Bash", write: "Write", edit: "Edit", multiedit: "MultiEdit", patch: "Edit", apply_patch: "Edit", notebookedit: "NotebookEdit" }
export const RouterGate = async ({ directory }) => ({
  "tool.execute.before": async (input, output) => {
    const tool = TOOL[String(input.tool).toLowerCase()] || input.tool
    const a = output.args || {}
    const ev = { tool_name: tool, cwd: directory || process.cwd(),
      tool_input: { command: a.command, file_path: a.filePath || a.file_path || a.path } }
    const r = spawnSync("aistudio", ["guard"], { input: JSON.stringify(ev), encoding: "utf8", timeout: 30000 })
    if (r.status !== 0) throw new Error((r.stderr || "ROUTER GATE: aistudio guard failed").trim())
  },
})
JS
  OPENCODE_CONFIG_CONTENT="{\"plugin\":[\"file://${GATE_DIR}/router-gate.js\"]}"
  export OPENCODE_CONFIG_CONTENT
}

runner_deadline_instructions() {
  local start_epoch="$1"
  local cutoff_epoch=$((start_epoch + ROUND_TIMEOUT - 10))
  local persist_epoch=$((cutoff_epoch - 240))
  printf 'The runner will forcibly stop this round at about %s; treat %s as the persistence deadline. Pass both deadlines to every worker, do not start a step that cannot be safely parked, and push completed work by the persistence deadline.' \
    "$(date -u -d "@${cutoff_epoch}" '+%Y-%m-%d %H:%M:%S UTC')" "$(date -u -d "@${persist_epoch}" '+%Y-%m-%d %H:%M:%S UTC')"
}

# Файл задачи круга пишет САМ РАННЕР (одинарные кавычки: обратные апострофы и $( ) не выполняются оболочкой).
# Подстановка только @…@ через ${var//…/…} (результат подстановки заново не раскрывается).
TASK_TEMPLATE=$(cat <<'TASK'
Ты — Лунобот-@BOT@ (id узла: @NODE@). Ты — Google Gemini, ты думаешь и решаешь сам; команды в оболочке за тебя выполняет движок, ты просишь их по одной (протокол выше). Подпись (LUNOBOT.md, modules/writing.md): роутер — @MANAGER@ (только запускает движок), исполнитель — модель Gemini из строки answered by в логе драйва.

ЗАДАЧА: сделай ОДИН полный круг Лунобота по инструкции LUNOBOT.md (она приложена к этому запросу): сначала OWNER_QUEUE.md, tick-all, выбери работу по § 5, сделай один шаг, запиши в учёт, рефлексия через journal.py (§ 4 п. 6). Режим одного круга из скрипта-раннера: потолок воркеров (б) на этот круг — 1. Рабочий каталог — пустая рабочая папка; репозитории клонируй туда (gh repo clone). Незаконченное оставь запушенной веткой с записью в status (§ 7.5); в конце круга освободи свои захваты (release.py). @DEADLINE@ Не начинай шаг, который нельзя безопасно припарковать. Если делать нечего или ты заблокирован — ответь действием blocked с причиной; не придумывай работу.
TASK
)

# ── один чистый круг Lunobot ─────────────────────────────────────────
run_round() {
  local round_num="$1"
  local ts="$(date -u '+%Y%m%d-%H%M%S')"
  local log_file="${LOG_DIR}/round-${round_num}-${ts}.log"
  local started=${SECONDS}

  log "=== Round ${round_num} START ==="

  # 1) качаем свежую инструкцию; отдельный opencode run создаёт чистый контекст.
  log "Fetching LUNOBOT.md ..."
  mkdir -p "/tmp/lunobot-${BOT_NUMBER}"
  curl -fsSL "https://raw.githubusercontent.com/unxed/lunobot/refs/heads/main/LUNOBOT.md" \
    -o "/tmp/lunobot-${BOT_NUMBER}/LUNOBOT.md" || { log "ERROR: cannot fetch LUNOBOT.md"; return 1; }

  # 2) id узла из tools/node.py репозитория (без клона: скачиваем один файл)
  local node_id="unknown"
  curl -fsSL "https://raw.githubusercontent.com/unxed/lunobot/refs/heads/main/tools/node.py" \
    -o "/tmp/lunobot-${BOT_NUMBER}/node.py" 2>/dev/null \
    && node_id="$(python3 "/tmp/lunobot-${BOT_NUMBER}/node.py" 2>/dev/null || echo unknown)"

  # 3) файл задачи круга пишет сам раннер; роутеру достаётся только команда запуска
  local task_file="/tmp/lunobot-${BOT_NUMBER}/round-task.md"
  local work_dir="/tmp/lunobot-${BOT_NUMBER}/work"
  local drive_log="${LOG_DIR}/drive-${round_num}-${ts}"
  rm -rf -- "${work_dir:?}"; mkdir -p "${work_dir}" "${drive_log}"
  local task="${TASK_TEMPLATE}"
  task="${task//@BOT@/${BOT_NUMBER}}"
  task="${task//@NODE@/${node_id}}"
  task="${task//@MANAGER@/${MANAGER_ID}}"
  task="${task//@DEADLINE@/$(runner_deadline_instructions "$(date -u +%s)")}"
  printf '%s\n' "${task}" >"${task_file}"
  local drive_timeout=$((ROUND_TIMEOUT - 120))
  local prompt="Run exactly this one command and output its stdout verbatim, nothing else: OFFLOAD_CALLER=${MANAGER_ID} timeout ${drive_timeout} aistudio drive --task-file ${task_file} -f /tmp/lunobot-${BOT_NUMBER}/LUNOBOT.md -C ${work_dir} --deadline-min $((drive_timeout / 60 - 2)) --log ${drive_log}"

  log "Starting opencode router (model: ${MODEL}) -> aistudio drive ..."
  cd "${WORKDIR}"
  # Stream output to the terminal and log while preserving the command status.
  OFFLOAD_CALLER="${MANAGER_ID}" setsid timeout --foreground "${ROUND_TIMEOUT}" opencode run \
    --model "${MODEL}" \
    --title "Lunobot-${BOT_NUMBER} round ${round_num}" \
    --auto \
    --format json \
    -- "$prompt" \
    >"${log_file}" 2>&1 &
  ACTIVE_PID=$!
  CLAIMS_DIRTY=1
  ACTIVE_PGID="$(ps -o pgid= -p "${ACTIVE_PID}" 2>/dev/null | tr -d ' ' || true)"
  # лог — JSON (стоимость и токены по шагам для journal.py); в терминал — текст, вызовы инструментов, ошибки
  tail --pid="${ACTIVE_PID}" -n +1 -f "${log_file}" | jq -Rr --unbuffered '
    (fromjson? // null) as $j
    | if $j == null then .
      elif $j.type == "text" then ($j.part.text // empty)
      elif $j.type == "tool_use" then "▶ \($j.part.tool // "tool") \(($j.part.state.input // {}) | tostring | .[0:200])"
      elif $j.type == "step_finish" then "· шаг: $\($j.part.cost // 0)"
      elif $j.type == "error" then "ERROR \($j | tostring | .[0:300])"
      else empty end' &
  ACTIVE_TAIL_PID=$!
  local exit_code=0
  if wait "${ACTIVE_PID}"; then
    exit_code=0
  else
    exit_code=$?
  fi
  ACTIVE_PID=""
  ACTIVE_PGID=""
  wait "${ACTIVE_TAIL_PID}" 2>/dev/null || true
  ACTIVE_TAIL_PID=""
  release_claims "круг ${round_num} раннера $(basename "$0") окончен (код ${exit_code})" \
    "${log_file}" "${round_num}" "${exit_code}" "$((SECONDS - started))" || true

  # проверка на token limit
  if check_token_limit "${log_file}"; then
    log "DETECTED: Token limit / rate limit in round output"
    wait_token_reset "${TOKEN_LIMIT_WAIT}"
    return 2  # специальный код для token limit
  fi

  if [[ ${exit_code} -eq 124 ]]; then
    log "WARNING: round ${round_num} timed out (${ROUND_TIMEOUT}s)"
    return 1
  elif [[ ${exit_code} -ne 0 ]]; then
    log "ERROR: opencode exited with code ${exit_code}"
    return 1
  fi

  log "=== Round ${round_num} DONE ==="
  return 0
}

# ── основной цикл ────────────────────────────────────────────────────
main() {
  if [[ "${1:-}" == "--check" ]]; then
    check_prereqs && echo "OK: предусловия выполнены (роутер ${MODEL}, Лунобот-${BOT_NUMBER})"
    exit $?
  fi
  check_prereqs || { echo "Предусловия не выполнены — раунды не запускаются." >&2; exit 1; }
  acquire_runner_lock || exit 1
  install_router_agent
  install_router_gate
  log "=== Lunobot-opencode-gemini runner started (PID $$) ==="
  log "Model: ${MODEL}, interval: ${INTERVAL_MIN} min, logs: ${LOG_DIR}"

  rotate_logs

  local round=1
  while true; do
    local attempt=1
    while (( attempt <= MAX_RETRIES )); do
      local rc=0
      if run_round "${round}"; then
        rc=0
      else
        rc=$?
      fi
      case $rc in
        0) break ;;                    # успех
        2)                             # token limit — не считаем за попытку, просто ждём и ретраим
          log "Token limit retry (not counted against MAX_RETRIES)"
          ;;
        *)                             # обычная ошибка
          log "Round ${round} failed (attempt ${attempt}/${MAX_RETRIES})"
          if (( attempt < MAX_RETRIES )); then
            log "Retrying in ${RETRY_DELAY}s ..."
            sleep "${RETRY_DELAY}"
          fi
          ((attempt++))
          ;;
      esac
    done

    if (( attempt > MAX_RETRIES )); then
      log "ERROR: round ${round} failed after ${MAX_RETRIES} attempts, continuing anyway"
    fi

    rotate_logs
    log "Sleeping ${INTERVAL_MIN} minutes until next round ..."
    sleep $(( INTERVAL_MIN * 60 ))
    ((round++))
  done
}

trap 'stop_active_round INT 130' INT
trap 'stop_active_round TERM 143' TERM

# защита от запуска main при source
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
