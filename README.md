# Task API

A CRUD API for managing a to-do list, built with **FastAPI** + **PostgreSQL**, fully containerized with **Docker Compose**.

> FlyRank Internship — Backend Track — Week 3 — Postgres + Docker

Builds on Week 2's in-memory CRUD API by swapping the storage layer for real Postgres, running the whole stack with one command, and proving data survives a restart.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Framework-009688)
![Postgres](https://img.shields.io/badge/PostgreSQL-16-336791)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)

---

## Table of Contents

- [What Changed From Week 2](#what-changed-from-week-2--honestly)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Endpoints](#endpoints)
- [Config](#config)
- [Persistence Proof](#persistence-proof)
- [Running Without Docker](#running-without-docker-in-memory-mode-week-2-behavior)
- [Project Structure](#project-structure)
- [Stretch Goals](#stretch-goals)

---

## What changed from Week 2 — honestly

Week 2's `main.py` had everything inline: routes read and wrote a global Python list directly. There was no interface to swap behind, so before "just swapping storage" was possible, the layering the assignment assumes had to be introduced:

| File | Role |
|---|---|
| `app/models.py` | The `Task` shape every layer agrees on |
| `app/repository.py` | The `TaskRepository` interface |
| `app/memory_repo.py` | Week 2's logic, moved behind that interface, unchanged in behavior |
| `app/service.py` | Business rules (title validation, 404s), talks only to the interface |
| `app/postgres_repo.py` | **New this week** — implements the same interface against real Postgres |
| `app/main.py` | Routes now call `service`, not a data structure directly |

**That refactor was a one-time cost.** Once the interface existed, going from `InMemoryTaskRepository` to `PostgresTaskRepository` touched exactly one line of wiring in `app/main.py`:

```python
if _storage == "postgres":
    from app.postgres_repo import PostgresTaskRepository
    repository = PostgresTaskRepository()
else:
    repository = InMemoryTaskRepository()
```

`app/service.py` and every route in `app/main.py` are byte-for-byte unchanged by the swap. That's what this week was actually testing.

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐
│   Client    │─────▶│  app/main.py │─────▶│  app/service.py │
│ (curl/UI)   │      │   (routes)   │      │ (business rules)│
└─────────────┘      └──────────────┘      └────────┬─────────┘
                                                      │
                                          TaskRepository interface
                                                      │
                             ┌────────────────────────┴───────────────────────┐
                             │                                                │
                    ┌────────▼─────────┐                             ┌────────▼─────────┐
                    │ memory_repo.py    │                             │ postgres_repo.py │
                    │ (in-process list) │                             │ (asyncpg/Postgres)│
                    └────────────────────┘                             └────────┬─────────┘
                                                                                  │
                                                                          ┌───────▼───────┐
                                                                          │  Postgres DB  │
                                                                          │  (db service) │
                                                                          └───────────────┘
```

## Quick Start

```bash
git clone https://github.com/adityayadvv45/Assignment-FlyRank-AI.git
cd Assignment-FlyRank-AI
cp .env.example .env      # already gitignored — safe to edit
docker compose up --build
```

This starts two containers:

- **`db`** — Postgres 16, with `db/init.sql` creating the `tasks` table and seeding it on first boot; data persists in a named volume (`a2_pgdata`)
- **`app`** — the FastAPI service, waits for `db`'s healthcheck before starting

| Service | URL |
|---|---|
| API | http://localhost:8000 |
| Interactive docs (Swagger) | http://localhost:8000/docs |

## Endpoints

| Method | Path | Description | Success | Errors |
|---|---|---|---|---|
| GET | `/` | API info (also reports which storage is active) | 200 | — |
| GET | `/health` | Health check | 200 | — |
| GET | `/tasks` | List tasks (`?done=`, `?search=`) | 200 | — |
| GET | `/tasks/{id}` | Get one task | 200 | 404 |
| POST | `/tasks` | Create a task (`{"title": "..."}`) | 201 | 400 |
| PUT | `/tasks/{id}` | Update title and/or done | 200 | 400, 404 |
| DELETE | `/tasks/{id}` | Delete a task | 204 | 404 |
| GET | `/stats` | Task counts | 200 | — |
| POST | `/reset` | Re-seed the 3 example tasks | 200 | — |

**Example:**

```bash
curl -s -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Write the README"}'
```

```json
{
  "id": 4,
  "title": "Write the README",
  "done": false
}
```

## Config

Everything is driven by `.env` (gitignored; see `.env.example`):

| Variable | Meaning |
|---|---|
| `POSTGRES_USER` | db username |
| `POSTGRES_PASSWORD` | db password |
| `POSTGRES_DB` | db name |
| `DATABASE_URL` | full connection string the app uses |
| `STORAGE` | `memory` or `postgres` (auto-defaults to `postgres` if `DATABASE_URL` is set) |

## Persistence proof

How this was checked (redo this and paste the actual terminal output / screenshot below before submitting):

```bash
docker compose up --build -d

curl -s -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" -d '{"title":"Survive a restart"}'
curl -s http://localhost:8000/tasks

docker compose down          # NOT `down -v` — that deletes the volume
docker compose up -d

curl -s http://localhost:8000/tasks   # "Survive a restart" is still there
```

<!-- paste your actual output here -->

## Running without Docker (in-memory mode, Week 2 behavior)

```bash
pip install -r requirements.txt
STORAGE=memory uvicorn app.main:app --reload
```

## Project Structure

```
Assignment-FlyRank-AI/
├── app/
│   ├── main.py            # FastAPI routes
│   ├── service.py         # business rules
│   ├── repository.py      # TaskRepository interface
│   ├── memory_repo.py     # in-memory implementation
│   ├── postgres_repo.py   # Postgres implementation
│   └── models.py          # Task schema
├── db/
│   └── init.sql           # table creation + seed data
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Stretch goals

Not yet done:

- [ ] Redis service in `docker-compose.yml` + a `/health/redis` ping endpoint
- [ ] `EXPLAIN ANALYZE` before/after adding an index on `tasks.done` or `tasks.title` (once the table has enough seeded rows to matter)

## License

No license specified — assignment repo for the FlyRank internship.gh seeded rows to matter.
