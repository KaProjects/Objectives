# Testing and automated checks

## Run everything

After completing the one-time backend and frontend setup below, run every
check from the repository root with:

```sh
./check.sh
```

The script runs all checks even if one fails, then prints a combined summary
and returns a non-zero exit code when any check failed. By default it starts a
disposable MySQL 8.4 container, runs the complete backend suite against it, and
removes the container afterward.

For a faster run without the MySQL compatibility check:

```sh
SKIP_MYSQL=1 ./check.sh
```

## Backend setup

The production container uses Python 3.12. Use that version for the closest
local match when it is available:

```sh
cd backend
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
```

### Backend lint and SQLite tests

```sh
cd backend
.venv/bin/ruff check src devel test script
.venv/bin/python test/run.py
```

The API tests use Flask's in-process test client. They do not start a server or
open a TCP port. SQL and Firebase fixtures are reset before every API test.

Standard `unittest` discovery and individual tests also work:

```sh
cd backend
.venv/bin/python -m unittest discover -s test -t .
.venv/bin/python test/run.py test_tasks_api.TestTasksApi.test_create_task
.venv/bin/python -m unittest test.test_tasks_api.TestTasksApi.test_create_task
```

Ruff only reports problems by default. Apply its safe automatic fixes
explicitly with:

```sh
.venv/bin/ruff check --fix src devel test script
```

### Run the backend suite against disposable MySQL

Start an isolated MySQL container:

```sh
docker run --name objectives-test-mysql --rm -d \
  -p 3307:3306 \
  -e MYSQL_ROOT_PASSWORD=root-password \
  -e MYSQL_DATABASE=objectives_test \
  -e MYSQL_USER=objectives \
  -e MYSQL_PASSWORD=test-password \
  mysql:8.4
```

Wait until it is ready:

```sh
docker exec objectives-test-mysql \
  mysqladmin ping -h 127.0.0.1 -uobjectives -ptest-password --silent
```

Then run the same complete suite against MySQL:

```sh
cd backend
TEST_DATABASE=mysql \
MYSQL_TEST_HOST=127.0.0.1 \
MYSQL_TEST_PORT=3307 \
MYSQL_TEST_USER=objectives \
MYSQL_TEST_PASSWORD=test-password \
MYSQL_TEST_DATABASE=objectives_test \
.venv/bin/python test/run.py
```

Stop and remove the disposable server:

```sh
docker stop objectives-test-mysql
```

> **Warning:** the test runner drops and recreates tables in
> `MYSQL_TEST_DATABASE`. Never point these variables at development or
> production data.

## Frontend setup

Frontend linting and browser tests require Node.js 18 or newer. Node.js 22 LTS
is recommended. When the active Node.js is too old, `check.sh` automatically
uses a compatible installation from nvm when one is already installed.

```sh
cd frontend
npm ci
npx playwright install chromium
```

The Playwright browser installation is required once per machine, and again
after some Playwright upgrades.

### Frontend checks

```sh
cd frontend
npm run lint
npm test
npm run build
npm run test:e2e
```

ESLint is configured with a zero-warning policy, so `npm run lint` fails when
either an error or warning is introduced.

The Playwright tests start Vite automatically and mock the backend at the
browser network boundary. A running backend and production credentials are not
required.

Useful focused commands:

```sh
# One Vitest file
npm test -- test/components/Ideas.test.js

# One Playwright test by title
npm run test:e2e -- --grep "idea CRUD"

# Watch component tests while developing
npm run test:watch

# Run browser tests with a visible browser
npm run test:e2e:headed

# Apply ESLint's safe automatic fixes
npm run lint:fix
```
