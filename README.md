# Objectives

Run the complete local quality suite from this directory:

```sh
./verify.sh
```

One-time setup and focused commands are documented in [TESTING.md](TESTING.md).

Run backend and frontend together in dev mode:

```sh
./build_deploy.sh dev
```

Run them separately from the project root in two terminals:

```sh
# Terminal 1: backend
(cd backend && ./build_deploy.sh dev)

# Terminal 2: frontend
(cd frontend && ./build_deploy.sh dev)
```

Run the production build and deployment together:

```sh
./build_deploy.sh
```

Run the production build and deployment separately from the project root:

```sh
# Backend
(cd backend && ./build_deploy.sh)

# Frontend
(cd frontend && ./build_deploy.sh)
```
