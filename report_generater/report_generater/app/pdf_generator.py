"""
pdf_generator.py
----------------
Pure PDF-building logic using ReportLab. This module does NOT touch the
database or the Report table - it just takes already-aggregated numbers
and produces a PDF file on disk. Keeping it "pure" like this makes it easy
to test in isolation and easy to reuse if the aggregation source ever
changes.
"""

from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def generate_sales_report_pdf(
    filepath: str,
    total_sales: float,
    total_orders: int,
    top_products: list,
):
    """
    Build a professional-looking sales report PDF and save it to `filepath`.

    Args:
        filepath: full path (including filename) to write the PDF to.
        total_sales: sum of all sale amounts.
        total_orders: count of all orders.
        top_products: list of (product_name, total_quantity, total_revenue)
                       tuples, already sorted by revenue descending.
    """
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=22,
        spaceAfter=6,
        textColor=colors.HexColor("#1F2937"),
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#6B7280"),
        spaceAfter=20,
    )
    section_heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=14,
        spaceBefore=18,
        spaceAfter=10,
        textColor=colors.HexColor("#1F2937"),
    )

    elements = []

    # --- Header ---------------------------------------------------------
    elements.append(Paragraph("Sales Report", title_style))
    generated_on = datetime.utcnow().strftime("%B %d, %Y at %H:%M UTC")
    elements.append(Paragraph(f"Generated on {generated_on}", subtitle_style))

    # --- Summary metrics table -------------------------------------------
    elements.append(Paragraph("Summary", section_heading_style))

    summary_data = [
        ["Metric", "Value"],
        ["Total Sales", f"${total_sales:,.2f}"],
        ["Total Orders", f"{total_orders:,}"],
    ]
    summary_table = Table(summary_data, colWidths=[8 * cm, 8 * cm])
    summary_table.setStyle(_summary_table_style())
    elements.append(summary_table)

    # --- Top products table ----------------------------------------------
    elements.append(Paragraph("Top Products", section_heading_style))

    if top_products:
        product_data = [["Rank", "Product", "Quantity Sold", "Revenue"]]
        for rank, (name, qty, revenue) in enumerate(top_products, start=1):
            product_data.append(
                [str(rank), name, str(qty), f"${revenue:,.2f}"]
            )

        product_table = Table(
            product_data, colWidths=[2 * cm, 7 * cm, 3.5 * cm, 3.5 * cm]
        )
        product_table.setStyle(_product_table_style())
        elements.append(product_table)
    else:
        elements.append(Paragraph("No sales data available.", styles["Normal"]))

    elements.append(Spacer(1, 24))
    footer_style = ParagraphStyle(
        "Footer", parent=styles["Normal"], fontSize=8, textColor=colors.grey
    )
    elements.append(
        Paragraph("Generated automatically by Sales Report Backend.", footer_style)
    )

    doc.build(elements)


def _summary_table_style() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
            ("TOPPADDING", (0, 1), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ]
    )


def _product_table_style() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (2, 0), (-1, -1), "CENTER"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D1D5DB")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
            ("TOPPADDING", (0, 1), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ]
    )
