"""
crud.py
-------
All direct database access lives here, so routes and the background worker
don't write raw SQLAlchemy queries inline. Keeping queries in one place makes
them easy to find, test, and change later.
"""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Sale, Report, ReportStatus


# ---------------------------------------------------------------------------
# Sale queries
# ---------------------------------------------------------------------------

def get_all_sales(db: Session):
    """Return every sale row. Used mainly for debugging/inspection."""
    return db.query(Sale).all()


def get_total_sales(db: Session) -> float:
    """Sum of total_amount across all sales. Returns 0.0 if there are none."""
    total = db.query(func.sum(Sale.total_amount)).scalar()
    return round(total or 0.0, 2)


def get_total_orders(db: Session) -> int:
    """Count of sale rows (each row = one order line)."""
    return db.query(func.count(Sale.id)).scalar() or 0


def get_top_products(db: Session, limit: int = 5):
    """
    Top-selling products by total revenue, descending.
    Returns a list of tuples: (product_name, total_quantity, total_revenue)
    """
    results = (
        db.query(
            Sale.product_name,
            func.sum(Sale.quantity).label("total_quantity"),
            func.sum(Sale.total_amount).label("total_revenue"),
        )
        .group_by(Sale.product_name)
        .order_by(func.sum(Sale.total_amount).desc())
        .limit(limit)
        .all()
    )
    return results


# ---------------------------------------------------------------------------
# Report queries
# ---------------------------------------------------------------------------

def create_report(db: Session) -> Report:
    """Insert a new Report row with status=PENDING and return it."""
    report = Report(status=ReportStatus.PENDING)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_report(db: Session, report_id: int) -> Report | None:
    return db.query(Report).filter(Report.id == report_id).first()


def get_all_reports(db: Session):
    """All reports, most recent first."""
    return db.query(Report).order_by(Report.created_at.desc()).all()


def update_report_status(
    db: Session,
    report_id: int,
    status: ReportStatus,
    filename: str | None = None,
    error_message: str | None = None,
    completed_at=None,
):
    """
    Update a report's status (and optionally filename / error / completion
    time) in one place. Called by the background worker as the job
    progresses: PENDING -> PROCESSING -> COMPLETED (or FAILED).
    """
    report = get_report(db, report_id)
    if report is None:
        return None

    report.status = status
    if filename is not None:
        report.filename = filename
    if error_message is not None:
        report.error_message = error_message
    if completed_at is not None:
        report.completed_at = completed_at

    db.commit()
    db.refresh(report)
    return report
