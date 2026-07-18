"""
schemas.py
----------
Pydantic models used for request validation and API responses.
Kept separate from the SQLAlchemy models (models.py) - that's a standard
FastAPI convention: ORM models describe the DB table, schemas describe
what goes over the wire.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models import ReportStatus


class SaleOut(BaseModel):
    """Response shape for a single sale record."""

    id: int
    product_name: str
    quantity: int
    unit_price: float
    total_amount: float
    order_date: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportOut(BaseModel):
    """Response shape for a report's metadata (used by GET /reports)."""

    id: int
    filename: Optional[str] = None
    status: ReportStatus
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    download_url: Optional[str] = None  # filled in by the route, not the DB

    model_config = ConfigDict(from_attributes=True)


class GenerateReportResponse(BaseModel):
    """
    Response returned immediately by POST /generate-report.
    Mirrors the 202-Accepted pattern: we hand back a report_id right away,
    the PDF itself is built afterwards in the background.
    """

    report_id: int
    status: ReportStatus
    message: str
