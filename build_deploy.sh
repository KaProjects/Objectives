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

LOG_DIR="$(mktemp -d "${TMPDIR:-/tmp}/objectives-build.XXXXXX")"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"
backend_pid=""
frontend_pid=""
backend_status=""
frontend_status=""
dashboard_rendered=0
dashboard_rows=0
dashboard_width=0
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

clean_log_stream() {
  tr '\r\t' '\n ' \
    | sed $'s/\\^D\010\010//g' \
    | tr -d '\004\010' \
    | sed $'s|\033\\[[0-9;?]*[ -/]*[@-~]||g' \
    | sed '/^[[:space:]]*$/d'
}

clean_log() {
  clean_log_stream < "$1"
}

recent_clean_log() {
  local file="$1"
  local lines="$2"

  # Animated build output can grow quickly. Only clean a generous recent
  # window; the dashboard only needs enough data to fill its fixed-height pane.
  tail -c 131072 "$file" | clean_log_stream | tail -n "$lines"
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

terminal_height() {
  local size
  local height
  size="$(stty size < /dev/tty 2>/dev/null || true)"
  height="${size%% *}"
  if [[ ! "$height" =~ ^[0-9]+$ ]] || [[ $height -lt 12 ]]; then
    height="${LINES:-24}"
  fi
  if [[ ! "$height" =~ ^[0-9]+$ ]] || [[ $height -lt 12 ]]; then
    height=24
  fi
  printf '%s' "$height"
}

render_line() {
  local content="$1"
  local width="$2"
  local color="${3:-}"

  printf '\033[2K\r'
  [[ -n "$color" ]] && printf '%s' "$color"
  printf '%-*.*s' "$width" "$width" "$content"
  [[ -n "$color" ]] && printf '\033[0m'
  printf '\n'
}

render_dashboard() {
  local width
  local height
  local render_width
  local backend_title='BACKEND [RUNNING]'
  local frontend_title='FRONTEND [RUNNING]'
  local backend_failed=0
  local frontend_failed=0
  local red=''
  local separator
  local available_log_lines
  local backend_panel_lines
  local frontend_panel_lines
  local line
  local index
  local backend_lines=()
  local frontend_lines=()

  width="$(terminal_width)"
  height="$(terminal_height)"
  render_width=$((width - 1))
  available_log_lines=$((height - 4))
  backend_panel_lines=$((available_log_lines / 2))
  frontend_panel_lines=$((available_log_lines - backend_panel_lines))
  printf -v separator '%*s' "$render_width" ''
  separator="${separator// /-}"

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
  fi

  if [[ ! -t 1 ]]; then
    printf '%s\n' "$backend_title"
    clean_log "$BACKEND_LOG"
    printf '%s\n' "$separator"
    printf '%s\n' "$frontend_title"
    clean_log "$FRONTEND_LOG"
    return
  fi

  while IFS= read -r line; do
    backend_lines[${#backend_lines[@]}]="$line"
  done < <(recent_clean_log "$BACKEND_LOG" "$backend_panel_lines")

  while IFS= read -r line; do
    frontend_lines[${#frontend_lines[@]}]="$line"
  done < <(recent_clean_log "$FRONTEND_LOG" "$frontend_panel_lines")

  if [[ $dashboard_rendered -eq 0 \
      || $dashboard_rows -ne $height \
      || $dashboard_width -ne $width ]]; then
    printf '\033[2J\033[H'
  else
    printf '\033[H'
  fi

  if [[ $backend_failed -eq 1 ]]; then
    render_line "$backend_title" "$render_width" "$red"
  else
    render_line "$backend_title" "$render_width"
  fi

  for ((index = 0; index < backend_panel_lines; index++)); do
    line="${backend_lines[$index]-}"
    if [[ "$line" == *'ERROR:'* ]]; then
      render_line "$line" "$render_width" "$red"
    else
      render_line "$line" "$render_width"
    fi
  done

  render_line "$separator" "$render_width"

  if [[ $frontend_failed -eq 1 ]]; then
    render_line "$frontend_title" "$render_width" "$red"
  else
    render_line "$frontend_title" "$render_width"
  fi

  for ((index = 0; index < frontend_panel_lines; index++)); do
    line="${frontend_lines[$index]-}"
    if [[ "$line" == *'ERROR:'* ]]; then
      render_line "$line" "$render_width" "$red"
    else
      render_line "$line" "$render_width"
    fi
  done

  dashboard_rendered=1
  dashboard_rows=$height
  dashboard_width=$width
}

(
  # The parent launcher owns Ctrl+C and stops the complete process tree.
  # Keeping SIGINT away from this background branch prevents its direct child
  # from exiting before the parent can discover and terminate its descendants.
  trap '' INT
  cd "$ROOT_DIR/backend" || exit 1
  if [[ "$MODE" == "prod" && $USE_TTY_PROGRESS -eq 1 ]]; then
    script -q /dev/null env BUILDKIT_PROGRESS=tty ./build_deploy.sh "$MODE"
  else
    BUILDKIT_PROGRESS=plain ./build_deploy.sh "$MODE"
  fi
) >"$BACKEND_LOG" 2>&1 &
backend_pid=$!

(
  # See the backend branch above. Without this, npm can outlive the launcher
  # when Ctrl+C terminates the intermediate shell before cleanup inspects it.
  trap '' INT
  cd "$ROOT_DIR/frontend" || exit 1
  if [[ "$MODE" == "prod" && $USE_TTY_PROGRESS -eq 1 ]]; then
    script -q /dev/null env BUILDKIT_PROGRESS=tty ./build_deploy.sh "$MODE"
  else
    BUILDKIT_PROGRESS=plain ./build_deploy.sh "$MODE"
  fi
) >"$FRONTEND_LOG" 2>&1 &
frontend_pid=$!

if [[ -t 1 ]]; then
  printf '\033[?25l'
  cursor_hidden=1
fi

while [[ -z "$backend_status" || -z "$frontend_status" ]]; do
  if [[ -z "$backend_status" ]] && ! kill -0 "$backend_pid" 2>/dev/null; then
    wait "$backend_pid"
    backend_status=$?
  fi
  if [[ -z "$frontend_status" ]] && ! kill -0 "$frontend_pid" 2>/dev/null; then
    wait "$frontend_pid"
    frontend_status=$?
  fi

  # The development servers form one application. If either side exits or
  # fails to start, stop the other side instead of leaving the launcher
  # waiting indefinitely with only half of the application running.
  if [[ "$MODE" == "dev" ]]; then
    if [[ -n "$frontend_status" && -z "$backend_status" ]]; then
      terminate_process_tree "$backend_pid"
      wait "$backend_pid" 2>/dev/null || true
      backend_status=0
    elif [[ -n "$backend_status" && -z "$frontend_status" ]]; then
      terminate_process_tree "$frontend_pid"
      wait "$frontend_pid" 2>/dev/null || true
      frontend_status=0
    fi
  fi

  if [[ -t 1 ]]; then
    render_dashboard
  fi
  sleep 0.2
done

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
  if [[ -t 2 ]]; then
    printf '\033[31mBuild/deploy failed (backend=%d, frontend=%d).\033[0m\n' \
      "$backend_status" "$frontend_status" >&2
  else
    printf 'Build/deploy failed (backend=%d, frontend=%d).\n' \
      "$backend_status" "$frontend_status" >&2
  fi
  exit 1
fi
