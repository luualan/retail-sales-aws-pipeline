import random
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
from faker import Faker


fake = Faker()
random.seed(42)
Faker.seed(42)

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)


def random_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


def generate_customers(num_customers: int = 500) -> pd.DataFrame:
    states = ["WA", "CA", "OR", "TX", "NY", "FL", "IL", "AZ", "NV", "CO"]

    rows = []
    for customer_id in range(1, num_customers + 1):
        signup_date = random_date(datetime(2024, 1, 1), datetime(2026, 6, 1))

        rows.append(
            {
                "customer_id": customer_id,
                "customer_name": fake.name(),
                "email": fake.email(),
                "state": random.choice(states),
                "signup_date": signup_date.date().isoformat(),
            }
        )

    return pd.DataFrame(rows)


def generate_products(num_products: int = 100) -> pd.DataFrame:
    categories = {
        "Electronics": ["Wireless Mouse", "Keyboard", "USB-C Hub", "Monitor", "Webcam"],
        "Home": ["Air Purifier", "Desk Lamp", "Coffee Maker", "Vacuum", "Organizer"],
        "Books": ["Python Book", "AWS Guide", "Data Engineering Book", "SQL Handbook"],
        "Beauty": ["Moisturizer", "Cleanser", "Sunscreen", "Serum"],
        "Fitness": ["Dumbbells", "Yoga Mat", "Resistance Bands", "Protein Shaker"],
    }

    rows = []
    for product_id in range(1, num_products + 1):
        category = random.choice(list(categories.keys()))
        base_name = random.choice(categories[category])

        rows.append(
            {
                "product_id": product_id,
                "product_name": f"{base_name} {product_id}",
                "category": category,
                "price": round(random.uniform(8.99, 499.99), 2),
            }
        )

    return pd.DataFrame(rows)


def generate_orders(customers: pd.DataFrame, num_orders: int = 2000) -> pd.DataFrame:
    statuses = ["completed", "completed", "completed", "completed", "cancelled", "pending"]
    regions = ["west", "east", "south", "midwest"]

    rows = []
    for order_id in range(1, num_orders + 1):
        order_date = random_date(datetime(2026, 1, 1), datetime(2026, 6, 22))

        # Intentionally create rare bad data
        if random.random() < 0.01:
            customer_id = None
        else:
            customer_id = int(customers.sample(1)["customer_id"].iloc[0])

        rows.append(
            {
                "order_id": order_id,
                "customer_id": customer_id,
                "order_date": order_date.date().isoformat(),
                "order_status": random.choice(statuses),
                "region": random.choice(regions),
            }
        )

    return pd.DataFrame(rows)


def generate_order_items(orders: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    rows = []
    order_item_id = 1

    for _, order in orders.iterrows():
        num_items = random.randint(1, 5)

        for _ in range(num_items):
            product = products.sample(1).iloc[0]

            # Intentionally create rare bad data
            quantity = random.randint(1, 4)
            if random.random() < 0.005:
                quantity = -1

            rows.append(
                {
                    "order_item_id": order_item_id,
                    "order_id": int(order["order_id"]),
                    "product_id": int(product["product_id"]),
                    "quantity": quantity,
                    "unit_price": float(product["price"]),
                }
            )
            order_item_id += 1

    return pd.DataFrame(rows)


def generate_payments(orders: pd.DataFrame, order_items: pd.DataFrame) -> pd.DataFrame:
    payment_methods = ["credit_card", "debit_card", "gift_card", "paypal"]
    payment_statuses = ["paid", "paid", "paid", "failed", "refunded"]

    order_totals = (
        order_items.assign(line_total=order_items["quantity"] * order_items["unit_price"])
        .groupby("order_id", as_index=False)["line_total"]
        .sum()
    )

    rows = []
    for payment_id, row in enumerate(order_totals.itertuples(index=False), start=1):
        status = random.choice(payment_statuses)

        # Cancelled orders are more likely to have failed payments
        order_status = orders.loc[orders["order_id"] == row.order_id, "order_status"].iloc[0]
        if order_status == "cancelled":
            status = random.choice(["failed", "refunded"])

        amount = round(max(row.line_total, 0), 2)

        rows.append(
            {
                "payment_id": payment_id,
                "order_id": int(row.order_id),
                "payment_method": random.choice(payment_methods),
                "payment_status": status,
                "amount": amount,
            }
        )

    return pd.DataFrame(rows)


def generate_refunds(orders: pd.DataFrame, payments: pd.DataFrame) -> pd.DataFrame:
    refund_reasons = ["damaged_item", "late_delivery", "wrong_item", "buyer_remorse"]

    refundable_payments = payments[payments["payment_status"].isin(["refunded"])]
    rows = []

    for refund_id, payment in enumerate(refundable_payments.itertuples(index=False), start=1):
        order_date = orders.loc[orders["order_id"] == payment.order_id, "order_date"].iloc[0]
        refund_date = datetime.fromisoformat(order_date) + timedelta(days=random.randint(1, 20))

        rows.append(
            {
                "refund_id": refund_id,
                "order_id": int(payment.order_id),
                "refund_date": refund_date.date().isoformat(),
                "refund_amount": round(float(payment.amount) * random.uniform(0.25, 1.0), 2),
                "refund_reason": random.choice(refund_reasons),
            }
        )

    return pd.DataFrame(rows)


def write_csv(df: pd.DataFrame, filename: str) -> None:
    path = RAW_DIR / filename
    df.to_csv(path, index=False)
    print(f"Wrote {len(df):,} rows to {path}")


def main() -> None:
    customers = generate_customers()
    products = generate_products()
    orders = generate_orders(customers)
    order_items = generate_order_items(orders, products)
    payments = generate_payments(orders, order_items)
    refunds = generate_refunds(orders, payments)

    write_csv(customers, "customers.csv")
    write_csv(products, "products.csv")
    write_csv(orders, "orders.csv")
    write_csv(order_items, "order_items.csv")
    write_csv(payments, "payments.csv")
    write_csv(refunds, "refunds.csv")


if __name__ == "__main__":
    main()