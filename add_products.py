from app.database import SessionLocal
from app.models import Product

db = SessionLocal()

products = [
    Product(title="iPhone 15", price=999.99, count=10),
    Product(title="Samsung Galaxy S24", price=899.99, count=15),
]

for product in products:
    db.add(product)

db.commit()

print("Добавлено 2 продукта:")
for p in products:
    db.refresh(p)
    print(f"  - {p.title}: ${p.price} ({p.count} шт.)")

db.close()