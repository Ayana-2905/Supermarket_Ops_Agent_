from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)


def generate_invoice_pdf(bill):

    output_dir = Path("data/invoices")
    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    file_path = (
        output_dir
        / f"{bill.bill_number}.pdf"
    )

    document = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    story = []

    story.append(
        Paragraph(
            "<b>KiranaPilot</b>",
            styles["Title"]
        )
    )

    story.append(
        Paragraph(
            "GST Invoice",
            styles["Heading2"]
        )
    )

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            f"<b>Bill Number:</b> {bill.bill_number}",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            f"<b>Date:</b> "
            f"{bill.created_at.strftime('%d-%m-%Y %H:%M')}",
            styles["Normal"]
        )
    )

    story.append(
        Paragraph(
            f"<b>Payment:</b> {bill.payment_mode}",
            styles["Normal"]
        )
    )

    story.append(Spacer(1, 20))

    table_data = [
        [
            "Product",
            "Qty",
            "Price",
            "GST",
            "Total"
        ]
    ]

    for item in bill.items:

        product_name = (
            item.product.name
            if item.product
            else f"Product #{item.product_id}"
        )

        table_data.append(
            [
                product_name,
                str(item.quantity),
                f"₹{item.unit_price:.2f}",
                f"{item.gst_rate:.2f}%",
                f"₹{item.line_total:.2f}"
            ]
        )

    table = Table(
        table_data,
        colWidths=[
            180,
            50,
            80,
            60,
            80
        ]
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.black
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "ALIGN",
                    (1, 1),
                    (-1, -1),
                    "RIGHT"
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, 0),
                    8
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, 0),
                    8
                )
            ]
        )
    )

    story.append(table)

    story.append(Spacer(1, 20))

    summary = [
        ["Subtotal", f"₹{bill.subtotal:.2f}"],
        ["CGST", f"₹{bill.cgst:.2f}"],
        ["SGST", f"₹{bill.sgst:.2f}"],
        ["Total", f"₹{bill.total:.2f}"]
    ]

    summary_table = Table(
        summary,
        colWidths=[380, 100]
    )

    summary_table.setStyle(
        TableStyle(
            [
                (
                    "ALIGN",
                    (1, 0),
                    (-1, -1),
                    "RIGHT"
                ),
                (
                    "FONTNAME",
                    (0, -1),
                    (-1, -1),
                    "Helvetica-Bold"
                ),
                (
                    "LINEABOVE",
                    (0, -1),
                    (-1, -1),
                    1,
                    colors.black
                )
            ]
        )
    )

    story.append(summary_table)

    story.append(Spacer(1, 25))

    story.append(
        Paragraph(
            "Thank you for shopping with us!",
            styles["Normal"]
        )
    )

    document.build(story)

    return str(file_path)