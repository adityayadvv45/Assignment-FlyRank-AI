"""
models.py
---------
Two tables:

1. Sale   - the raw sales data we report on (the "sample sales data").
2. Report - metadata about each generated PDF report (status, filename,
            when it was created). This is what GET /reports lists, and
            what lets a client poll "is my report ready yet?".
"""

import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, Enum

from app.database import Base


class Sale(Base):
    """A single sales transaction."""

    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)  # quantity * unit_price
    order_date = Column(DateTime, default=datetime.utcnow)


class ReportStatus(str, enum.Enum):
    """Lifecycle of a generated report."""

    PENDING = "pending"      # background task queued, not started yet
    PROCESSING = "processing"  # background task is running right now
    COMPLETED = "completed"    # PDF generated successfully
    FAILED = "failed"          # something went wrong


class Report(Base):
    """Metadata for one generated sales report PDF."""

    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, nullable=True)
    status = Column(Enum(ReportStatus), default=ReportStatus.PENDING, nullable=False)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
