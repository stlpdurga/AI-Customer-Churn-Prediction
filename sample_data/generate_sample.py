import csv
import random
from pathlib import Path

random.seed(42)
output = Path(__file__).with_name("sample_customers.csv")
contracts = ["Month-to-month", "Quarterly", "Annual"]
payments = ["UPI", "Card", "NetBanking", "Wallet"]
plans = [799, 1299, 2499, 3999]
rows = []
for index in range(1, 1001):
    tenure = random.randint(1, 60)
    monthly = random.choice(plans)
    tickets = random.randint(0, 7)
    usage = random.randint(5, 100)
    satisfaction = random.randint(1, 10)
    churned = tenure < 8 and tickets >= 4 or usage < 25 and satisfaction <= 4
    rows.append({"customer_id": f"SYN-{index:04d}", "age": random.randint(21, 68), "tenure": tenure,
                 "monthly_revenue": monthly, "total_revenue": monthly * tenure, "contract": random.choice(contracts),
                 "payment_method": random.choice(payments), "usage": usage, "support_tickets": tickets,
                 "satisfaction": satisfaction, "churn": "Yes" if churned else "No"})
rows[17]["monthly_revenue"] = ""
rows[203]["satisfaction"] = ""
rows.append(rows[99].copy())
with output.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
