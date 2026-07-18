"""
main.py
-------
FastAPI application entry point. Defines all routes:

    POST /generate-report      -> kicks off background PDF generation
    GET  /reports              -> list all generated reports
    GET  /reports/{id}         -> check a single report's status
    GET  /download/{filename}  -> download a completed PDF
    GET  /sales                -> (bonus) view the raw sample sales data

Run with:
    uvicorn app.main:app --reload
"""

import os

from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import Base, engine, SessionLocal, get_db
from app.models import ReportStatus
from app.report_worker import run_generate_report
from app.seed_data import seed_sales_data

REPORTS_DIR = "reports"

# Create tables on startup (fine for SQLite + a small project; a real
# project would use Alembic migrations instead).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sales Report Backend",
    description="Generates sales report PDFs in the background using FastAPI BackgroundTasks.",
    version="1.0.0",
)

# Allow the standalone frontend (opened as a local file, or served from a
# different port like a simple `python -m http.server`) to call this API
# from the browser. Wide open here since this is a local internship project;
# a real deployment would restrict allow_origins to the actual frontend URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Seed sample sales data (only if the table is empty) and ensure the
    reports/ folder exists."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    db = SessionLocal()
    try:
        seed_sales_data(db)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

@app.post("/generate-report", response_model=schemas.GenerateReportResponse, status_code=202)
def generate_report(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Starts generating a sales report PDF in the background.

    Returns immediately with a report_id and status=PENDING. The actual
    PDF is built afterwards by run_generate_report(); poll
    GET /reports/{report_id} to see when it's COMPLETED (or FAILED).
    """
    report = crud.create_report(db)

    # Schedule the slow work to run AFTER this response is sent.
    background_tasks.add_task(run_generate_report, report.id)

    return schemas.GenerateReportResponse(
        report_id=report.id,
        status=report.status,
        message="Report generation started. Poll GET /reports/{id} for status.",
    )


# ---------------------------------------------------------------------------
# Report listing / status
# ---------------------------------------------------------------------------

@app.get("/reports", response_model=list[schemas.ReportOut])
def list_reports(db: Session = Depends(get_db)):
    """Lists all reports ever generated, most recent first."""
    reports = crud.get_all_reports(db)
    return [_to_report_out(r) for r in reports]


@app.get("/reports/{report_id}", response_model=schemas.ReportOut)
def get_report_status(report_id: int, db: Session = Depends(get_db)):
    """Check a single report's status (pending/processing/completed/failed)."""
    report = crud.get_report(db, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return _to_report_out(report)


def _to_report_out(report) -> schemas.ReportOut:
    """Converts a Report ORM object into a ReportOut, adding a download_url
    only once the PDF actually exists (status == COMPLETED)."""
    download_url = None
    if report.status == ReportStatus.COMPLETED and report.filename:
        download_url = f"/download/{report.filename}"

    return schemas.ReportOut(
        id=report.id,
        filename=report.filename,
        status=report.status,
        error_message=report.error_message,
        created_at=report.created_at,
        completed_at=report.completed_at,
        download_url=download_url,
    )


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

@app.get("/download/{filename}")
def download_report(filename: str):
    """Downloads a generated PDF by filename."""
    # Basic safety: prevent path traversal (e.g. "../../etc/passwd").
    safe_filename = os.path.basename(filename)
    filepath = os.path.join(REPORTS_DIR, safe_filename)

    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="Report file not found")

    return FileResponse(
        path=filepath,
        media_type="application/pdf",
        filename=safe_filename,
    )


# ---------------------------------------------------------------------------
# Bonus: view raw sample sales data
# ---------------------------------------------------------------------------

@app.get("/sales", response_model=list[schemas.SaleOut])
def list_sales(db: Session = Depends(get_db)):
    """Lists the raw sample sales rows the reports are built from."""
    return crud.get_all_sales(db)


@app.get("/")
def root():
    return {
        "message": "Sales Report Backend is running.",
        "docs": "/docs",
    }
