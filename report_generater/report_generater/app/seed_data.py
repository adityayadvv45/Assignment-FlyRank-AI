"""
seed_data.py
------------
Inserts a batch of sample sales rows the first time the app runs, so there's
always something for /generate-report to aggregate. If sales already exist,
seeding is skipped (safe to call on every startup).
"""

import random
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import Sale

PRODUCTS = [
    ("Wireless Mouse", 15.99),
    ("Mechanical Keyboard", 49.99),
    ("USB-C Hub", 24.50),
    ("Laptop Stand", 32.00),
    ("Webcam 1080p", 39.99),
    ("Noise Cancelling Headphones", 89.99),
    ("Portable SSD 1TB", 74.99),
    ("Desk Lamp", 21.75),
    ("Monitor Arm", 45.00),
    ("Bluetooth Speaker", 29.99),
]


def seed_sales_data(db: Session, num_rows: int = 60):
    """
    Insert `num_rows` random sample sales if the table is currently empty.
    Idempotent-ish: running this again when data already exists is a no-op,
    so it's safe to call on every app startup without creating duplicates.
    """
    existing_count = db.query(Sale).count()
    if existing_count > 0:
        return  # already seeded, nothing to do

    today = datetime.utcnow()

    for _ in range(num_rows):
        product_name, unit_price = random.choice(PRODUCTS)
        quantity = random.randint(1, 10)
        total_amount = round(unit_price * quantity, 2)
        order_date = today - timedelta(days=random.randint(0, 30))

        sale = Sale(
            product_name=product_name,
            quantity=quantity,
            unit_price=unit_price,
            total_amount=total_amount,
            order_date=order_date,
        )
        db.add(sale)

    db.commit()
