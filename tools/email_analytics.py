import argparse
import csv


def analyze(rows):
    results = []

    for row in rows:
        sent = int(row["sent"])
        clicks = int(row["clicks"])
        orders = int(row["orders"])
        revenue = float(row["revenue"])

        if sent <= 0 or not 0 <= clicks <= sent:
            raise ValueError("Invalid sent or clicks value")
        if orders < 0 or revenue < 0:
            raise ValueError("Orders and revenue cannot be negative")

        results.append({
            "campaign": row["campaign"],
            "click_rate": clicks / sent * 100,
            "revenue_per_email": revenue / sent,
            "orders": orders,
        })

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    args = parser.parse_args()

    with open(args.file, newline="", encoding="utf-8-sig") as f:
        results = analyze(csv.DictReader(f))

    for row in results:
        print(
            f"{row['campaign']}: "
            f"Click rate {row['click_rate']:.2f}% | "
            f"Revenue/email ${row['revenue_per_email']:.2f} | "
            f"Orders {row['orders']}"
        )


if __name__ == "__main__":
    main()
