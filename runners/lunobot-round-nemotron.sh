#!/usr/bin/env bash
# lunobot-round-nemotron.sh — один круг Lunobot через opencode + Nemotron 3 Ultra Free

set -euo pipefail

export LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUTF8=1
export NO_PROXY=127.0.0.1,localhost

# ── настройки ─────────────────────────────────────────────────────────
MODEL="opencode/nemotron-3-ultra-free"
SESSION_NAME="lunobot-1"
BOT_NUMBER=1
WORKDIR="${HOME}"
INTERVAL_MIN=15
MAX_RETRIES=3
RETRY_DELAY=60
TOKEN_LIMIT_WAIT=120
LOG_DIR="${HOME}/.lunobot/logs"
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

check_token_limit() {
  local log_file="$1"
  # лог — opencode --format json: смотрим только события error и строки вне JSON (stderr), не текст тикетов в выводе инструментов
  jq -Rr '(fromjson? // null) as $j | if $j == null then . elif $j.type == "error" then ($j | tostring) else empty end' \
    "${log_file}" 2>/dev/null \
    | grep -qi -E "rate limit|token limit|quota exceeded|too many tokens|429 Too Many Requests|insufficient quota|billing"
}

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

# ── один чистый круг Lunobot ─────────────────────────────────────────
run_round() {
  local round_num="$1"
  local ts="$(date -u '+%Y%m%d-%H%M%S')"
  local log_file="${LOG_DIR}/round-${round_num}-${ts}.log"
  local started=${SECONDS}

  log "=== Round ${round_num} START ==="

  log "Fetching LUNOBOT.md ..."
  mkdir -p /tmp/lunobot-1
  curl -fsSL "https://raw.githubusercontent.com/unxed/lunobot/refs/heads/main/LUNOBOT.md" \
    -o "/tmp/lunobot-1/LUNOBOT.md" || { log "ERROR: cannot fetch LUNOBOT.md"; return 1; }

  local prompt="Ты — Лунобот-1 (Nemotron 3 Ultra). Сделай ОДИН полный круг работы по инструкции из /tmp/lunobot-1/LUNOBOT.md: проверь OWNER_QUEUE.md, tick-all, выбери работу по §5, сделай шаг, запиши в учёт, rétro. Не останавливайся, пока круг не завершён. Режим одного круга из скрипта-раннера: потолок воркеров (б) на этот круг — 1 (LUNOBOT.md § 5): одновременно работает не больше одного воркера, менеджер не в счёт; освободился — следующую задачу тому же воркеру (ПЕРЕДАЙ ВОРКЕРУ), второго не запускай. После круга раннер снимет все захваты твоего id (release.py, LUNOBOT.md § 1): незаконченное оставь запушенной веткой с записью в status (§ 7.5), не в /tmp. В ретро запиши рефлексию круга (journal.py, § 4 п. 6). Ответь кратко итогом круга."

  log "Starting opencode (model: ${MODEL}) ..."
  cd "${WORKDIR}"
  # --standalone: own private server, no external dependency
  # Stream output to the terminal and log while preserving the command status.
  setsid timeout --foreground 1800 opencode run \
    --model "${MODEL}" \
    --title "Lunobot-1 round ${round_num}" \
    --auto \
    --standalone \
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

  if check_token_limit "${log_file}"; then
    log "DETECTED: Token limit / rate limit in round output"
    wait_token_reset "${TOKEN_LIMIT_WAIT}"
    return 2
  fi

  if [[ ${exit_code} -eq 124 ]]; then
    log "WARNING: round ${round_num} timed out (30 min)"
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
  acquire_runner_lock || exit 1
  log "=== Lunobot-Nemotron runner started (PID $$) ==="
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
        0) break ;;
        2) log "Token limit retry (not counted against MAX_RETRIES)" ;;
        *) log "Round ${round} failed (attempt ${attempt}/${MAX_RETRIES})"
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

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
