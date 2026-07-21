#!/usr/bin/env bash

set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
PYTHON="$BACKEND_DIR/.venv/bin/python"
RUFF="$BACKEND_DIR/.venv/bin/ruff"

STEP_NAMES=()
STEP_RESULTS=()
STEP_DURATIONS=()
PASSED=0
FAILED=0
SKIPPED=0
MYSQL_CONTAINER=""
ORIGINAL_NODE_VERSION=""

if [[ -t 1 ]]; then
  GREEN='\033[32m'
  RED='\033[31m'
  YELLOW='\033[33m'
  BOLD='\033[1m'
  RESET='\033[0m'
else
  GREEN=''
  RED=''
  YELLOW=''
  BOLD=''
  RESET=''
fi

cleanup_mysql() {
  if [[ -n "$MYSQL_CONTAINER" ]]; then
    docker rm -f "$MYSQL_CONTAINER" >/dev/null 2>&1 || true
    MYSQL_CONTAINER=""
  fi
}

trap cleanup_mysql EXIT INT TERM

node_is_supported() {
  local executable="$1"

  "$executable" -e '
    const major = Number(process.versions.node.split(".")[0])
    process.exit(major >= 24 ? 0 : 1)
  ' >/dev/null 2>&1
}

select_compatible_node() {
  local candidate

  if command -v node >/dev/null 2>&1; then
    ORIGINAL_NODE_VERSION="$(node --version 2>/dev/null || true)"
    if node_is_supported "$(command -v node)"; then
      return 0
    fi
  fi

  for candidate in "$HOME"/.nvm/versions/node/v*/bin/node /opt/homebrew/bin/node /usr/local/bin/node; do
    [[ -x "$candidate" ]] || continue
    if node_is_supported "$candidate"; then
      export PATH="$(dirname "$candidate"):$PATH"
      printf 'Using %s from %s (active %s is unsupported).\n' \
        "$(node --version)" "$(dirname "$candidate")" "${ORIGINAL_NODE_VERSION:-Node.js not found}"
      return 0
    fi
  done
}

select_compatible_node

run_step() {
  local name="$1"
  shift
  local started status duration result

  printf '\n%s==> %s%s\n' "$BOLD" "$name" "$RESET"
  started=$(date +%s)

  "$@"
  status=$?
  duration=$(( $(date +%s) - started ))

  if [[ $status -eq 0 ]]; then
    result="PASS"
    PASSED=$((PASSED + 1))
    printf '%sPASS%s %s (%ss)\n' "$GREEN" "$RESET" "$name" "$duration"
  elif [[ $status -eq 125 ]]; then
    result="SKIP"
    SKIPPED=$((SKIPPED + 1))
    printf '%sSKIP%s %s (%ss)\n' "$YELLOW" "$RESET" "$name" "$duration"
  else
    result="FAIL"
    FAILED=$((FAILED + 1))
    printf '%sFAIL%s %s (%ss, exit %s)\n' "$RED" "$RESET" "$name" "$duration" "$status"
  fi

  STEP_NAMES+=("$name")
  STEP_RESULTS+=("$result")
  STEP_DURATIONS+=("$duration")
  return 0
}

require_backend_environment() {
  if [[ ! -x "$PYTHON" || ! -x "$RUFF" ]]; then
    printf 'Backend environment is missing. Run:\n'
    printf '  cd %s && python3 -m venv .venv\n' "$BACKEND_DIR"
    printf '  .venv/bin/python -m pip install -r requirements-dev.txt\n'
    return 127
  fi
}

backend_ruff() {
  require_backend_environment || return $?
  cd "$BACKEND_DIR" || return 1
  "$RUFF" check src devel test script
}

backend_sqlite_tests() {
  require_backend_environment || return $?
  cd "$BACKEND_DIR" || return 1
  "$PYTHON" test/run.py
}

backend_mysql_tests() {
  if [[ "${SKIP_MYSQL:-0}" == "1" ]]; then
    printf 'Skipped because SKIP_MYSQL=1.\n'
    return 125
  fi

  require_backend_environment || return $?

  if ! command -v docker >/dev/null 2>&1; then
    printf 'Docker is not installed. Use SKIP_MYSQL=1 to omit this check.\n'
    return 127
  fi

  if ! docker info >/dev/null 2>&1; then
    printf 'Docker is installed, but its daemon is not running.\n'
    printf 'Start Docker, or use SKIP_MYSQL=1 to omit this check.\n'
    return 1
  fi

  local port="${MYSQL_TEST_PORT:-3307}"
  local ready=0
  local attempt
  MYSQL_CONTAINER="objectives-test-mysql-$$"

  docker run --name "$MYSQL_CONTAINER" --rm -d \
    -p "127.0.0.1:${port}:3306" \
    -e MYSQL_ROOT_PASSWORD=root-password \
    -e MYSQL_DATABASE=objectives_test \
    -e MYSQL_USER=objectives \
    -e MYSQL_PASSWORD=test-password \
    mysql:8.4 >/dev/null || return 1

  printf 'Waiting for disposable MySQL on port %s' "$port"
  for attempt in $(seq 1 60); do
    if docker exec "$MYSQL_CONTAINER" \
      mysqladmin ping -h 127.0.0.1 -uobjectives -ptest-password --silent >/dev/null 2>&1; then
      ready=1
      break
    fi
    printf '.'
    sleep 1
  done
  printf '\n'

  if [[ $ready -ne 1 ]]; then
    printf 'MySQL did not become ready within 60 seconds.\n'
    cleanup_mysql
    return 1
  fi

  cd "$BACKEND_DIR" || return 1
  TEST_DATABASE=mysql \
  MYSQL_TEST_HOST=127.0.0.1 \
  MYSQL_TEST_PORT="$port" \
  MYSQL_TEST_USER=objectives \
  MYSQL_TEST_PASSWORD=test-password \
  MYSQL_TEST_DATABASE=objectives_test \
    "$PYTHON" test/run.py
  local status=$?

  cleanup_mysql
  return $status
}

require_frontend_environment() {
  if ! command -v node >/dev/null 2>&1; then
    printf 'Node.js is missing. Install Node.js 24 or newer.\n'
    return 127
  fi

  if ! node_is_supported "$(command -v node)"; then
    printf 'Frontend checks require Node.js 24 or newer; current version: %s.\n' "$(node --version)"
    printf 'If you use nvm, run: nvm install 24 && nvm use 24\n'
    return 127
  fi

  if [[ ! -x "$FRONTEND_DIR/node_modules/.bin/vitest" || ! -x "$FRONTEND_DIR/node_modules/.bin/eslint" ]]; then
    printf 'Frontend dependencies are missing. Run:\n'
    printf '  cd %s && npm ci\n' "$FRONTEND_DIR"
    return 127
  fi
}

frontend_lint() {
  require_frontend_environment || return $?
  cd "$FRONTEND_DIR" || return 1
  npm run lint
}

frontend_component_tests() {
  require_frontend_environment || return $?
  cd "$FRONTEND_DIR" || return 1
  npm test
}

frontend_build() {
  require_frontend_environment || return $?
  cd "$FRONTEND_DIR" || return 1
  VITE_BACKEND_URL="${VITE_BACKEND_URL:-http://127.0.0.1:7777}" npm run build
}

frontend_browser_tests() {
  require_frontend_environment || return $?
  if [[ ! -x "$FRONTEND_DIR/node_modules/.bin/playwright" ]]; then
    printf 'Playwright is missing. Run: cd %s && npm ci\n' "$FRONTEND_DIR"
    return 127
  fi
  cd "$FRONTEND_DIR" || return 1
  npm run test:e2e
}

print_summary() {
  local index result color

  printf '\n%s================ CHECK SUMMARY ================%s\n' "$BOLD" "$RESET"
  for index in "${!STEP_NAMES[@]}"; do
    result="${STEP_RESULTS[$index]}"
    case "$result" in
      PASS) color="$GREEN" ;;
      FAIL) color="$RED" ;;
      *) color="$YELLOW" ;;
    esac
    printf '%s%-4s%s  %-42s %4ss\n' \
      "$color" "$result" "$RESET" "${STEP_NAMES[$index]}" "${STEP_DURATIONS[$index]}"
  done

  printf '\nPassed: %s  Failed: %s  Skipped: %s\n' "$PASSED" "$FAILED" "$SKIPPED"
}

printf '%sObjectives local checks%s\n' "$BOLD" "$RESET"
printf 'Workspace: %s\n' "$ROOT_DIR"

run_step 'Backend · Ruff' backend_ruff
run_step 'Backend · SQLite tests' backend_sqlite_tests
run_step 'Backend · MySQL compatibility tests' backend_mysql_tests
run_step 'Frontend · ESLint' frontend_lint
run_step 'Frontend · component tests' frontend_component_tests
run_step 'Frontend · production build' frontend_build
run_step 'Frontend · Playwright browser tests' frontend_browser_tests

print_summary

if [[ $FAILED -gt 0 ]]; then
  exit 1
fi
