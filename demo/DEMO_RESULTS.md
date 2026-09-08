# 📸 KiranaPilot — Demo Results

All demonstrations below were performed through the **Telegram interface**.

---

## 1. Inventory & Stock

**Stock lookup:** Checked the current quantity of a product through Telegram.

![Stock lookup](1.stock.jpeg)

**Low-stock check:** Identified the product with the lowest available stock.

![Low stock](2.low%20on%20stock.jpeg)

**Receive stock:** Added incoming stock and verified the updated quantity.

![Receive and check stock](3.%20received%20and%20checked%20.jpeg)

**Inventory count:** Returned the number of products currently registered.

![Product count](4.product%20count.jpeg)

**Inventory listing:** Displayed the available product catalog and stock details.

![Inventory list](demo_telegram_inventory.png)

---

## 2. Khata

**Customer balance & transactions:** Checked Ramesh's balance, transaction history, and recorded a payment.

![Khata](5.khata.jpeg)

---

## 3. Billing

**Draft bill:** Created a bill for multiple products with subtotal, GST and total.

**Sale confirmation:** Confirmed the bill through Telegram and finalized the sale with payment recorded.

![Billing and confirmation](demo_telegram_billing.png)

---

## Verified Features

- ✅ Product search
- ✅ Stock lookup
- ✅ Low-stock detection
- ✅ Receive stock
- ✅ Inventory listing
- ✅ Product count
- ✅ Draft billing
- ✅ Sale confirmation & finalization
- ✅ Khata balance
- ✅ Khata transactions
- ✅ Khata payment/settlement
- ✅ Telegram-based interaction
"""

out = os.path.join(demo_dir, "DEMO_RESULTS.md")
pypandoc.convert_text(md, "md", format="md", outputfile=out, extra_args=["--standalone"])

print(f"Created: {out}")
print("Screenshots copied into:", demo_dir)
