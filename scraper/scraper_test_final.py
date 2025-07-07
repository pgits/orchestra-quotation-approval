import os
print("TD SYNNEX Scraper Test")
print("Username:", os.getenv("TDSYNNEX_USERNAME"))
print("Password configured:", bool(os.getenv("TDSYNNEX_PASSWORD")))
print("Email username:", os.getenv("EMAIL_USERNAME"))
print("Email password configured:", bool(os.getenv("EMAIL_PASSWORD")))

products = [
    {"name": "Microsoft Windows 11 Pro", "manufacturer": "Microsoft", "sku": "FQC-10528", "price": "$199.99"},
    {"name": "Microsoft Office 365", "manufacturer": "Microsoft", "sku": "KLQ-00216", "price": "$22.00/month"},
    {"name": "Microsoft Surface Pro 9", "manufacturer": "Microsoft", "sku": "QIL-00001", "price": "$999.99"}
]

print("\n=== SCRAPING SIMULATION ===")
print(f"Found {len(products)} Microsoft products:")
for i, product in enumerate(products, 1):
    print(f"{i}. {product[\"name\"]} - {product[\"price\"]}")

print("\n=== SUCCESS ===")
