from app.infrastructure.database.database import Base, engine, SessionLocal
from app.infrastructure.database.models import Product

Base.metadata.create_all(bind=engine)

db = SessionLocal()

products = [
    Product(
        sku="MAGGI70",
        name="Maggi 70g",
        category="FMCG",
        unit="packet",
        is_loose=False,
        cost_price=12,
        sell_price=14,
        mrp=14,
        quantity=50,
        reorder_level=10,
        gst_rate=12,
        hsn_code="190230"
    ),
    Product(
        sku="SUGAR1KG",
        name="Sugar 1kg",
        category="Staples",
        unit="kg",
        is_loose=True,
        cost_price=40,
        sell_price=45,
        mrp=45,
        quantity=30,
        reorder_level=5,
        gst_rate=0,
        hsn_code=None
    ),
    Product(
        sku="ATTA5KG",
        name="Aashirvaad Atta 5kg",
        category="Staples",
        unit="packet",
        is_loose=False,
        cost_price=230,
        sell_price=260,
        mrp=270,
        quantity=15,
        reorder_level=5,
        gst_rate=5,
        hsn_code="110100"
    ),
    Product(
        sku="BUTTER100",
        name="Amul Butter 100g",
        category="Dairy",
        unit="packet",
        is_loose=False,
        cost_price=55,
        sell_price=60,
        mrp=62,
        quantity=8,
        reorder_level=3,
        gst_rate=12,
        hsn_code="040510"
    )
]

for product in products:
    existing = db.query(Product).filter(
        Product.sku == product.sku
    ).first()

    if not existing:
        db.add(product)

db.commit()
db.close()

print("Seed data inserted.")