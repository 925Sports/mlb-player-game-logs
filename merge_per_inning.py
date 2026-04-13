import csv
import glob

def merge_per_inning():
    csv_files = sorted(glob.glob("mlb_per_inning_logs_*.csv"))
    
    if not csv_files:
        print("No per-inning CSV files found!")
        return

    print(f"Found {len(csv_files)} per-inning files. Merging...")

    all_rows = []
    headers = None

    for file in csv_files:
        with open(file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if headers is None:
                headers = reader.fieldnames
            all_rows.extend(reader)

    output_file = "mlb_2026_per_inning_logs.csv"
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"✅ Merged {len(all_rows)} per-inning plays into {output_file}")

if __name__ == "__main__":
    merge_per_inning()
