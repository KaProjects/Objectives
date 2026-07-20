#!/usr/bin/env bash

set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="${1:-prod}"
if [[ "$MODE" != "dev" && "$MODE" != "prod" ]]; then
  printf 'Usage: %s [dev|prod]\n' "${0##*/}" >&2
  exit 2
fi

USE_TTY_PROGRESS=0
if command -v script >/dev/null 2>&1 \
    && script -q /dev/null true </dev/null >/dev/null 2>&1; then
  USE_TTY_PROGRESS=1
fi

TERMINAL_SIZE="$(stty size < /dev/tty 2>/dev/null || true)"
TERMINAL_ROWS="${TERMINAL_SIZE%% *}"
if [[ ! "$TERMINAL_ROWS" =~ ^[0-9]+$ ]] || [[ $TERMINAL_ROWS -lt 12 ]]; then
  TERMINAL_ROWS=24
fi
MAX_PANEL_LINES=$((TERMINAL_ROWS - 6))
LOG_DIR="$(mktemp -d "${TMPDIR:-/tmp}/objectives-build.XXXXXX")"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"
backend_pid=""
frontend_pid=""
backend_status=""
frontend_status=""
dashboard_rendered=0
dashboard_height=0
cursor_hidden=0

show_cursor() {
  if [[ $cursor_hidden -eq 1 ]]; then
    printf '\033[?25h'
    cursor_hidden=0
  fi
}

children_of() {
  local parent_pid="$1"

  if command -v pgrep >/dev/null 2>&1; then
    pgrep -P "$parent_pid" 2>/dev/null || true
  else
    ps -eo pid=,ppid= 2>/dev/null \
      | awk -v parent_pid="$parent_pid" '$2 == parent_pid { print $1 }'
  fi
}

collect_process_tree() {
  local root_pid="$1"
  local child_pid

  for child_pid in $(children_of "$root_pid"); do
    collect_process_tree "$child_pid"
  done
  printf '%s\n' "$root_pid"
}

terminate_process_tree() {
  local root_pid="$1"
  local process_ids
  local process_id
  local attempt
  local processes_alive

  [[ -n "$root_pid" ]] || return
  process_ids="$(collect_process_tree "$root_pid")"

  for process_id in $process_ids; do
    kill -TERM "$process_id" 2>/dev/null || true
  done

  for ((attempt = 0; attempt < 20; attempt++)); do
    processes_alive=0
    for process_id in $process_ids; do
      if kill -0 "$process_id" 2>/dev/null; then
        processes_alive=1
        break
      fi
    done
    [[ $processes_alive -eq 0 ]] && return
    sleep 0.1
  done

  for process_id in $process_ids; do
    kill -KILL "$process_id" 2>/dev/null || true
  done
}

cleanup() {
  show_cursor
  rm -rf "$LOG_DIR"
}

stop_children() {
  trap - INT TERM
  terminate_process_tree "$backend_pid"
  terminate_process_tree "$frontend_pid"
  [[ -n "$backend_pid" ]] && wait "$backend_pid" 2>/dev/null || true
  [[ -n "$frontend_pid" ]] && wait "$frontend_pid" 2>/dev/null || true
  exit 130
}

trap cleanup EXIT
trap stop_children INT TERM

clean_log() {
  tr '\r' '\n' < "$1" \
    | sed $'s/\\^D\010\010//g' \
    | tr -d '\004\010' \
    | sed $'s|\033\\[[0-9;?]*[ -/]*[@-~]||g' \
    | sed '/^[[:space:]]*$/d'
}

terminal_width() {
  local size
  local width
  size="$(stty size < /dev/tty 2>/dev/null || true)"
  width="${size##* }"
  if [[ ! "$width" =~ ^[0-9]+$ ]] || [[ $width -lt 20 ]]; then
    width="${COLUMNS:-120}"
  fi
  if [[ ! "$width" =~ ^[0-9]+$ ]] || [[ $width -lt 20 ]]; then
    width=120
  fi
  printf '%s' "$width"
}

render_dashboard() {
  local width
  local backend_title='BACKEND [RUNNING]'
  local frontend_title='FRONTEND [RUNNING]'
  local backend_failed=0
  local frontend_failed=0
  local red=''
  local reset=''
  local separator=' | '
  local separator_width=${#separator}
  local backend_width
  local frontend_width
  local panel_lines
  local line
  local backend_line
  local frontend_line
  local index
  local backend_lines=()
  local frontend_lines=()
  width="$(terminal_width)"
  backend_width=$(((width - separator_width) / 2))
  frontend_width=$((width - separator_width - backend_width))

  if [[ -n "$backend_status" ]]; then
    if [[ $backend_status -eq 0 ]]; then
      backend_title='BACKEND [FINISHED]'
    else
      backend_title='BACKEND [FAILED]'
      backend_failed=1
    fi
  fi
  if [[ -n "$frontend_status" ]]; then
    if [[ $frontend_status -eq 0 ]]; then
      frontend_title='FRONTEND [FINISHED]'
    else
      frontend_title='FRONTEND [FAILED]'
      frontend_failed=1
    fi
  fi
  if [[ -t 1 ]]; then
    red=$'\033[31m'
    reset=$'\033[0m'
  fi

  while IFS= read -r line; do
    backend_lines[${#backend_lines[@]}]="$line"
  done < <(clean_log "$BACKEND_LOG" | tail -n "$MAX_PANEL_LINES")

  while IFS= read -r line; do
    frontend_lines[${#frontend_lines[@]}]="$line"
  done < <(clean_log "$FRONTEND_LOG" | tail -n "$MAX_PANEL_LINES")

  panel_lines=${#backend_lines[@]}
  if [[ ${#frontend_lines[@]} -gt $panel_lines ]]; then
    panel_lines=${#frontend_lines[@]}
  fi
  if [[ $panel_lines -lt 1 ]]; then
    panel_lines=1
  fi

  if [[ $dashboard_rendered -eq 1 ]]; then
    printf '\033[%dA' "$dashboard_height"
  fi

  [[ -t 1 ]] && printf '\033[2K\r'
  if [[ $backend_failed -eq 1 ]]; then
    printf '%s%-*.*s%s' "$red" "$backend_width" "$backend_width" "$backend_title" "$reset"
  else
    printf '%-*.*s' "$backend_width" "$backend_width" "$backend_title"
  fi
  printf '%s' "$separator"
  if [[ $frontend_failed -eq 1 ]]; then
    printf '%s%.*s%s' "$red" "$frontend_width" "$frontend_title" "$reset"
  else
    printf '%.*s' "$frontend_width" "$frontend_title"
  fi
  printf '\n'

  for ((index = 0; index < panel_lines; index++)); do
    backend_line="${backend_lines[$index]-}"
    frontend_line="${frontend_lines[$index]-}"
    [[ -t 1 ]] && printf '\033[2K\r'
    if [[ "$backend_line" == *'ERROR:'* ]]; then
      printf '%s%-*.*s%s' "$red" "$backend_width" "$backend_width" "$backend_line" "$reset"
    else
      printf '%-*.*s' "$backend_width" "$backend_width" "$backend_line"
    fi
    printf '%s' "$separator"
    if [[ "$frontend_line" == *'ERROR:'* ]]; then
      printf '%s%.*s%s' "$red" "$frontend_width" "$frontend_line" "$reset"
    else
      printf '%.*s' "$frontend_width" "$frontend_line"
    fi
    printf '\n'
  done

  dashboard_rendered=1
  dashboard_height=$((panel_lines + 1))
}

(
  cd "$ROOT_DIR/backend" || exit 1
  if [[ $USE_TTY_PROGRESS -eq 1 ]]; then
    script -q /dev/null env BUILDKIT_PROGRESS=tty ./build_deploy.sh "$MODE"
  else
    BUILDKIT_PROGRESS=plain ./build_deploy.sh "$MODE"
  fi
) >"$BACKEND_LOG" 2>&1 &
backend_pid=$!

(
  cd "$ROOT_DIR/frontend" || exit 1
  if [[ $USE_TTY_PROGRESS -eq 1 ]]; then
    script -q /dev/null env BUILDKIT_PROGRESS=tty ./build_deploy.sh "$MODE"
  else
    BUILDKIT_PROGRESS=plain ./build_deploy.sh "$MODE"
  fi
) >"$FRONTEND_LOG" 2>&1 &
frontend_pid=$!

if [[ -t 1 ]]; then
  printf '\033[?25l'
  cursor_hidden=1

  while [[ -z "$backend_status" || -z "$frontend_status" ]]; do
    if [[ -z "$backend_status" ]] && ! kill -0 "$backend_pid" 2>/dev/null; then
      wait "$backend_pid"
      backend_status=$?
    fi
    if [[ -z "$frontend_status" ]] && ! kill -0 "$frontend_pid" 2>/dev/null; then
      wait "$frontend_pid"
      frontend_status=$?
    fi
    render_dashboard
    sleep 0.2
  done
fi

if [[ -z "$backend_status" ]]; then
  wait "$backend_pid"
  backend_status=$?
fi

if [[ -z "$frontend_status" ]]; then
  wait "$frontend_pid"
  frontend_status=$?
fi

render_dashboard
show_cursor

if [[ $backend_status -ne 0 || $frontend_status -ne 0 ]]; then
  printf '\n'
  if [[ -t 2 ]]; then
    printf '\033[31mBuild/deploy failed (backend=%d, frontend=%d).\033[0m\n' \
      "$backend_status" "$frontend_status" >&2
  else
    printf 'Build/deploy failed (backend=%d, frontend=%d).\n' \
      "$backend_status" "$frontend_status" >&2
  fi
  exit 1
fi
