import csv
import argparse


def analyze_experiment(rows):
    results = []

    for row in rows:
        delivered = int(row["delivered"])
        clicks = int(row["clicks"])

        if delivered <= 0:
            raise ValueError("Delivered must be greater than zero")
        if clicks < 0 or clicks > delivered:
            raise ValueError("Clicks must be between 0 and delivered")

        click_rate = clicks / delivered * 100

        results.append({
            "variant": row["variant"],
            "job": row["job"],
            "delivered": delivered,
            "clicks": clicks,
            "click_rate": click_rate,
        })

    return sorted(
        results,
        key=lambda result: result["click_rate"],
        reverse=True,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Analyze JTBD marketing A/B tests"
    )
    parser.add_argument("csv_file")
    args = parser.parse_args()

    with open(args.csv_file, newline="", encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))

    if not rows:
        raise ValueError("CSV contains no experiment data")

    results = analyze_experiment(rows)

    print("\nJTBD Experiment Results\n")

    for result in results:
        print(
            f"{result['variant']} | "
            f"{result['job']} | "
            f"Click rate: {result['click_rate']:.2f}%"
        )

    print(
        f"\nHighest observed click rate: "
        f"{results[0]['variant']}"
    )
    print("Statistical significance has not been evaluated.")


if __name__ == "__main__":
    main()
