import csv
from pathlib import Path
from huggingface_hub import HfApi

BACKEND = Path(__file__).resolve().parents[2]
OUTPUT = BACKEND / "data" / "raw" / "sector_map.csv"

DATASET_ID = "kawsersikder/bangladesh-stock-market-dataset"


def collect_sector_map():
    print("Collecting DSE sector mappings...")

    api = HfApi()
    records = []

    files = api.list_repo_tree(
        repo_id=DATASET_ID,
        repo_type="dataset",
        path_in_repo="Unprocessed Data",
        recursive=True
    )

    for item in files:
        parts = item.path.split("/")

        if len(parts) != 3:
            continue

        if not item.path.lower().endswith(".csv"):
            continue

        sector = parts[1]
        symbol = Path(parts[2]).stem.upper()

        records.append({
            "Symbol": symbol,
            "Sector": sector
        })

    if not records:
        raise RuntimeError("No sector mappings found")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["Symbol", "Sector"]
        )
        writer.writeheader()
        writer.writerows(
            sorted(records, key=lambda x: x["Symbol"])
        )

    print("Sector mapping collection completed!")
    print(f"Symbols: {len(records)}")
    print(f"Sectors: {len(set(r['Sector'] for r in records))}")
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    collect_sector_map()
