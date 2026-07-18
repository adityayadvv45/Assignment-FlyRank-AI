# Sales Report Backend

A small backend project for a Backend Engineering internship: users trigger sales
report generation, a **background task** builds a PDF, and the client polls for
the result. Built with **FastAPI, SQLite, SQLAlchemy, ReportLab, and
BackgroundTasks** (no Celery, no Redis, no Docker).

## Why this pattern?

Generating a PDF from a database query is slow enough that you don't want the
client's HTTP request to sit there waiting for it. So the API answers
immediately (`202 Accepted` + a `report_id`), a background task does the real
work after the response is sent, and the client polls a status endpoint until
the PDF is ready. This is the same accept-fast/work-in-background/report-status
shape used for anything slow in production backends (AI calls, video
transcoding, big exports, etc.) — just implemented here with FastAPI's built-in
`BackgroundTasks` instead of a full task queue like Celery.

## Project Structure

```
sales_report_backend/
├── app/
│   ├── main.py            # FastAPI app + all routes + CORS setup
│   ├── database.py        # SQLAlchemy engine/session setup
│   ├── models.py           # ORM models: Sale, Report
│   ├── schemas.py           # Pydantic request/response models
│   ├── crud.py              # DB queries (including the aggregation logic)
│   ├── pdf_generator.py     # ReportLab PDF building (pure function)
│   ├── report_worker.py     # The background task: query -> aggregate -> PDF -> save
│   └── seed_data.py         # Inserts sample sales rows on first run
├── frontend/
│   └── index.html           # Single-file dashboard (no build step, no framework)
├── reports/                 # Generated PDFs are saved here
├── requirements.txt
└── README.md
```

## Setup

```bash
# 1. Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the server
uvicorn app.main:app --reload
```

The app will:
- Create `sales.db` (SQLite) automatically on first run.
- Seed ~60 sample sales rows automatically on first run (skipped on later
  runs if data already exists).
- Create the `reports/` folder automatically if it doesn't exist.

Visit **http://127.0.0.1:8000/docs** for interactive Swagger docs.

## Frontend

A small single-file dashboard lives in `frontend/index.html` — plain HTML/CSS/JS,
no build step, no framework. It lets you trigger report generation and watch
each job move through `pending → processing → completed` live, without
reloading the page, plus a collapsible view of the raw sample sales data.

With the API already running (see Setup above), serve the frontend from a
second terminal:

```bash
cd frontend
python3 -m http.server 5500
```

Then open **http://127.0.0.1:5500**. You can also just double-click
`frontend/index.html` to open it directly as a `file://` URL — either way
works, since the backend has CORS enabled for local development
(`app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)` in `main.py`).

If your API runs somewhere other than `http://127.0.0.1:8000`, update the
`API_BASE` constant near the top of the `<script>` block in `index.html`.

## API Reference

### `POST /generate-report`
Starts generating a sales report in the background. Returns immediately.

```bash
curl -X POST http://127.0.0.1:8000/generate-report
```

Response (`202 Accepted`):
```json
{
  "report_id": 1,
  "status": "pending",
  "message": "Report generation started. Poll GET /reports/{id} for status."
}
```

### `GET /reports`
Lists every report ever generated, most recent first.

```bash
curl http://127.0.0.1:8000/reports
```

```json
[
  {
    "id": 1,
    "filename": "sales_report_1_1730000000.pdf",
    "status": "completed",
    "error_message": null,
    "created_at": "2025-01-01T10:00:00",
    "completed_at": "2025-01-01T10:00:02",
    "download_url": "/download/sales_report_1_1730000000.pdf"
  }
]
```

### `GET /reports/{id}`
Checks the status of a single report. Poll this after calling
`POST /generate-report` until `status` becomes `"completed"` (or `"failed"`).

```bash
curl http://127.0.0.1:8000/reports/1
```

### `GET /download/{filename}`
Downloads the generated PDF. Use the `download_url` from the report response.

```bash
curl -O http://127.0.0.1:8000/download/sales_report_1_1730000000.pdf
```

### `GET /sales` (bonus)
Lists the raw sample sales data the reports are built from.

## Report contents

Each PDF includes:
- **Total Sales** — sum of all order amounts
- **Total Orders** — count of all orders
- **Top Products** — top 5 products ranked by revenue, with quantity sold

## Design notes (things an interviewer might ask about)

- **Why BackgroundTasks and not Celery?** `BackgroundTasks` runs the job in the
  same process, right after the response is sent — no message broker, no
  separate worker process, nothing extra to install. It's the right tool for
  short, low-volume background jobs like this one. Celery/Redis/RQ become
  worth the extra infrastructure once you need jobs to survive a server
  restart, run on a separate machine, or run at real scale.
- **Idempotency.** Every call to `POST /generate-report` creates a brand new
  `Report` row with its own id, so there's no risk of two requests colliding
  on the same record. The report-building work itself is read-only against
  `sales`, so re-running it for the same `report_id` is always safe to repeat.
- **Failure handling.** If anything in the worker raises an exception (bad
  data, disk full, etc.), it's caught, the report is marked `failed` with an
  `error_message`, and it's logged with `[ALERT]` in the server console. In a
  real production system that log line would instead be a Slack/Sentry/
  PagerDuty call — the shape is the same, only the transport changes.
- **Why separate `pdf_generator.py` from `report_worker.py`?** `pdf_generator.py`
  is a pure function — give it numbers, get a PDF file. It has no idea a
  database exists. `report_worker.py` is the orchestrator — it fetches data,
  calls the pure function, and updates status. Keeping them apart makes the
  PDF-building logic easy to test on its own.

## Notes / limitations (by design, to keep this project small)

- SQLite + `Base.metadata.create_all` is used instead of a migration tool
  like Alembic — fine for a small project, not what you'd use in production.
- No authentication/JWT — out of scope per the project requirements.
- No retry queue — a failed report requires the client to call
  `POST /generate-report` again; there's no automatic re-attempt.
