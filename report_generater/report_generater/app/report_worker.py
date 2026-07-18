"""
report_worker.py
-----------------
The background task itself. This is what FastAPI's BackgroundTasks runs
after the request has already returned a response to the client.

Flow:
    PENDING -> PROCESSING -> (build PDF) -> COMPLETED
                          (any exception along the way) -> FAILED

Notes on the non-negotiables (see the earlier bg-jobs discussion):
- Idempotency: each call to /generate-report creates its own new Report
  row with its own id, so re-running this worker for the same report_id
  twice just re-generates the same PDF onto the same filename - safe to
  repeat, no double-counting anywhere since it's read-only against `sales`.
- Retries: BackgroundTasks has no built-in retry queue (that's the trade-off
  vs. Celery/BullMQ). We keep the failure path explicit instead: any
  exception is caught, logged into report.error_message, and the status
  is set to FAILED so the client can see it via GET /reports and decide
  to call POST /generate-report again.
- Alerts: for a small internship project, "alerting" is a clear FAILED
  status + printed log line. In a real system this is where you'd call
  Slack/Sentry/PagerDuty instead of `print`.
"""

import os
import traceback
from datetime import datetime

from app import crud
from app.database import SessionLocal
from app.models import ReportStatus
from app.pdf_generator import generate_sales_report_pdf

REPORTS_DIR = "reports"


def run_generate_report(report_id: int):
    """
    Entry point called by BackgroundTasks. Opens its OWN database session
    because the request's session is closed by the time this runs -
    background tasks execute after the response has been sent.
    """
    db = SessionLocal()
    try:
        _process_report(db, report_id)
    finally:
        db.close()


def _process_report(db, report_id: int):
    # Mark as processing so GET /reports shows live progress.
    crud.update_report_status(db, report_id, status=ReportStatus.PROCESSING)

    try:
        # 1. Query + aggregate ------------------------------------------------
        total_sales = crud.get_total_sales(db)
        total_orders = crud.get_total_orders(db)
        top_products = crud.get_top_products(db, limit=5)

        # 2. Build the PDF ------------------------------------------------------
        os.makedirs(REPORTS_DIR, exist_ok=True)
        filename = f"sales_report_{report_id}_{int(datetime.utcnow().timestamp())}.pdf"
        filepath = os.path.join(REPORTS_DIR, filename)

        generate_sales_report_pdf(
            filepath=filepath,
            total_sales=total_sales,
            total_orders=total_orders,
            top_products=top_products,
        )

        # 3. Mark completed -------------------------------------------------
        crud.update_report_status(
            db,
            report_id,
            status=ReportStatus.COMPLETED,
            filename=filename,
            completed_at=datetime.utcnow(),
        )

    except Exception as exc:
        # Something went wrong anywhere above - record it and "alert".
        error_message = f"{type(exc).__name__}: {exc}"
        print(f"[ALERT] Report {report_id} failed: {error_message}")
        print(traceback.format_exc())

        crud.update_report_status(
            db,
            report_id,
            status=ReportStatus.FAILED,
            error_message=error_message,
        )
