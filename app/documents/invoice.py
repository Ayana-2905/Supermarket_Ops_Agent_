from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)


# ---------------------------------------------------------
# FONTS
# ---------------------------------------------------------

REGULAR_FONT = Path("C:/Windows/Fonts/segoeui.ttf")
BOLD_FONT = Path("C:/Windows/Fonts/segoeuib.ttf")

pdfmetrics.registerFont(
    TTFont("SegoeUI", str(REGULAR_FONT))
)

pdfmetrics.registerFont(
    TTFont("SegoeUI-Bold", str(BOLD_FONT))
)


# ---------------------------------------------------------
# INVOICE PDF
# ---------------------------------------------------------

def generate_invoice_pdf(bill) -> str:

    output_dir = Path("generated")
    output_dir.mkdir(exist_ok=True)

    file_path = output_dir / f"{bill.bill_number}.pdf"

    document = SimpleDocTemplate(
        str(file_path),
        pagesize=A4,
        rightMargin=35,
        leftMargin=35,
        topMargin=35,
        bottomMargin=35
    )

    styles = getSampleStyleSheet()

    normal_style = ParagraphStyle(
        "InvoiceNormal",
        parent=styles["Normal"],
        fontName="SegoeUI",
        fontSize=10
    )

    title_style = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Title"],
        fontName="SegoeUI-Bold",
        alignment=TA_CENTER,
        fontSize=18,
        spaceAfter=15
    )

    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontName="SegoeUI",
        alignment=TA_CENTER,
        fontSize=9
    )

    story = []

    # -----------------------------------------------------
    # HEADER
    # -----------------------------------------------------

    story.append(
        Paragraph(
            "GST TAX INVOICE",
            title_style
        )
    )

    story.append(
        Paragraph(
            f"<b>Bill Number:</b> {bill.bill_number}",
            normal_style
        )
    )

    story.append(
        Paragraph(
            f"<b>Status:</b> {bill.status}",
            normal_style
        )
    )

    story.append(
        Paragraph(
            f"<b>Payment Mode:</b> "
            f"{bill.payment_mode or 'N/A'}",
            normal_style
        )
    )

    story.append(Spacer(1, 18))

    # -----------------------------------------------------
    # ITEMS TABLE
    # -----------------------------------------------------

    table_data = [
        [
            "Product",
            "Qty",
            "Price",
            "GST",
            "CGST",
            "SGST",
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
                f"{item.quantity:g}",
                f"₹{item.unit_price:.2f}",
                f"{item.gst_rate:.2f}%",
                f"₹{item.cgst:.2f}",
                f"₹{item.sgst:.2f}",
                f"₹{item.line_total:.2f}"
            ]
        )

    items_table = Table(
        table_data,
        repeatRows=1,
        colWidths=[
            120,
            40,
            60,
            45,
            55,
            55,
            65
        ]
    )

    items_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "SegoeUI-Bold"
                ),
                (
                    "FONTNAME",
                    (0, 1),
                    (-1, -1),
                    "SegoeUI"
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    9
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
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                )
            ]
        )
    )

    story.append(items_table)

    story.append(Spacer(1, 18))

    # -----------------------------------------------------
    # TOTALS
    # -----------------------------------------------------

    totals_data = [
        ["Subtotal", f"₹{bill.subtotal:.2f}"],
        ["CGST", f"₹{bill.cgst:.2f}"],
        ["SGST", f"₹{bill.sgst:.2f}"],
        ["Grand Total", f"₹{bill.total:.2f}"]
    ]

    totals_table = Table(
        totals_data,
        colWidths=[100, 100],
        hAlign="RIGHT"
    )

    totals_table.setStyle(
        TableStyle(
            [
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, -1),
                    "SegoeUI"
                ),
                (
                    "FONTNAME",
                    (0, -1),
                    (-1, -1),
                    "SegoeUI-Bold"
                ),
                (
                    "ALIGN",
                    (1, 0),
                    (1, -1),
                    "RIGHT"
                ),
                (
                    "LINEABOVE",
                    (0, -1),
                    (-1, -1),
                    1,
                    colors.black
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                )
            ]
        )
    )

    story.append(totals_table)

    story.append(Spacer(1, 25))

    story.append(
        Paragraph(
            "Thank you for shopping with us.",
            footer_style
        )
    )

    document.build(story)

    return str(file_path)