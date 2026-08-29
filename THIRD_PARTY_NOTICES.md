# Third-party notices

Goblin Guard is MIT-licensed. Its direct runtime and build dependencies are listed below for review; each remains subject to its own licence.

## JavaScript

| Package | Pinned version | Role |
| --- | ---: | --- |
| React | 19.2.0 | User interface |
| React DOM | 19.2.0 | Browser rendering |
| Vite | 6.4.2 | Development and production build |
| `@vitejs/plugin-react` | 5.0.4 | React build integration |
| `@phosphor-icons/react` | 2.1.10 | Interface icons |

The complete resolved JavaScript dependency graph is recorded in `package-lock.json`.

## Python

| Package | Pinned version | Role |
| --- | ---: | --- |
| FastAPI | 0.116.1 | Local evaluation API |
| HTTPX | 0.28.1 | FastAPI test client dependency |
| Uvicorn | 0.35.0 | Local ASGI server |

The application otherwise uses Python's standard library for Alpaca and OpenAI HTTP calls. No third-party source code is copied into this repository.

Before a public release, verify the resolved transitive licence inventory generated from the lockfile and Python environment; this document is not a substitute for each dependency's licence text.
