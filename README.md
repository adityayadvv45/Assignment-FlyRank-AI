# Task API

A small in-memory CRUD API for managing a to-do list, built with FastAPI.
Built for FlyRank Internship — Backend Track — Week 2 — Assignment A1.

## How to install & run

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

The server starts at `http://localhost:8000`. Interactive Swagger UI docs are at
`http://localhost:8000/docs`.

## Endpoints

| Method | Path          | Description                          | Success | Errors        |
|--------|---------------|--------------------------------------|---------|---------------|
| GET    | `/`           | API info                             | 200     | —             |
| GET    | `/health`     | Health check                         | 200     | —             |
| GET    | `/tasks`      | List all tasks (supports `?done=` and `?search=`) | 200 | — |
| GET    | `/tasks/{id}` | Get one task                         | 200     | 404           |
| POST   | `/tasks`      | Create a task (`{"title": "..."}`)   | 201     | 400 (missing/empty title) |
| PUT    | `/tasks/{id}` | Update a task's title and/or done    | 200     | 400, 404      |
| DELETE | `/tasks/{id}` | Delete a task                        | 204     | 404           |
| GET    | `/stats`      | Task counts (extra)                  | 200     | —             |
| POST   | `/reset`      | Reset to the 3 example tasks (extra) | 200     | —             |

## Example curl output

```
$ curl -i -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d '{"title":"Buy milk"}'
HTTP/1.1 201 Created
content-type: application/json

{"id":4,"title":"Buy milk","done":false}
```

## Swagger screenshot

_(add your screenshot of `/docs` here after running "Try it out" on the full CRUD cycle)_

## Notes

- Data is stored in memory only — restarting the server resets it back to the 3 example
  tasks (or you can call `POST /reset` at any time).
- No database is used yet — that's next week.
