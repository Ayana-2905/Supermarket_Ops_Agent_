from datetime import datetime, timedelta
from pathlib import Path

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches, Pt


from sqlalchemy import select

from app.infrastructure.database.database import SessionLocal
from app.infrastructure.database.models import Bill


GENERATED_DIR = Path("generated")
GENERATED_DIR.mkdir(exist_ok=True)


def generate_sales_analysis_deck(days: int = 7) -> str:
    db = SessionLocal()

    try:
        end = datetime.utcnow()
        start = end - timedelta(days=days)

        bills = db.scalars(
            select(Bill).where(
                Bill.status == "FINALIZED",
                Bill.finalized_at >= start,
                Bill.finalized_at <= end
            ).order_by(Bill.finalized_at)
        ).all()

        daily_sales = {}

        for bill in bills:
            date = bill.finalized_at.strftime("%Y-%m-%d")

            daily_sales.setdefault(
                date,
                {
                    "sales": 0.0,
                    "bills": 0
                }
            )

            daily_sales[date]["sales"] += float(bill.total)
            daily_sales[date]["bills"] += 1

        dates = list(daily_sales.keys())
        sales = [
            round(daily_sales[d]["sales"], 2)
            for d in dates
        ]

        total_sales = round(sum(sales), 2)
        total_bills = len(bills)

        average_bill = (
            round(total_sales / total_bills, 2)
            if total_bills
            else 0
        )

        # -----------------------------
        # CREATE PRESENTATION
        # -----------------------------

        prs = Presentation()

        # Title slide
        slide = prs.slides.add_slide(
            prs.slide_layouts[0]
        )

        slide.shapes.title.text = "KiranaPilot Sales Analysis"

        slide.placeholders[1].text = (
            f"Last {days} days\n"
            f"{start.strftime('%d %b %Y')} - "
            f"{end.strftime('%d %b %Y')}"
        )

        # Summary slide
        slide = prs.slides.add_slide(
            prs.slide_layouts[5]
        )

        title = slide.shapes.title
        title.text = "Sales Summary"

        textbox = slide.shapes.add_textbox(
            Inches(1),
            Inches(1.7),
            Inches(8),
            Inches(3)
        )

        frame = textbox.text_frame

        lines = [
            f"Total Sales: ₹{total_sales:.2f}",
            f"Total Bills: {total_bills}",
            f"Average Bill Value: ₹{average_bill:.2f}",
        ]

        for i, line in enumerate(lines):

            paragraph = (
                frame.paragraphs[0]
                if i == 0
                else frame.add_paragraph()
            )

            paragraph.text = line
            paragraph.font.size = Pt(24)

        # Chart slide
        slide = prs.slides.add_slide(
            prs.slide_layouts[5]
        )

        slide.shapes.title.text = "Daily Sales"

        chart_data = CategoryChartData()
        chart_data.categories = dates
        chart_data.add_series(
            "Sales",
            sales
        )

        chart = slide.shapes.add_chart(
            XL_CHART_TYPE.COLUMN_CLUSTERED,
            Inches(1),
            Inches(1.5),
            Inches(8),
            Inches(4.5),
            chart_data
        ).chart

        chart.has_legend = False
        chart.has_title = True
        chart.chart_title.text = "Sales by Day"

        # Save
        filename = (
            f"sales_analysis_"
            f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pptx"
        )

        path = GENERATED_DIR / filename

        prs.save(path)

        return str(path)

    finally:
        db.close()