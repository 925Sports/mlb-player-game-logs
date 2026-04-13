import csv
import glob
from datetime import date

def merge_all_logs():
    # Find all daily CSV files
    csv_files = sorted(glob.glob("mlb_player_game_logs_*.csv"))
    
    if not csv_files:
        print("No daily CSV files found!")
        return

    print(f"Found {len(csv_files)} daily files. Merging into one seasonal file...")

    all_rows = []
    headers = None

    for file in csv_files:
        with open(file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if headers is None:
                headers = reader.fieldnames
            all_rows.extend(reader)

    # Write the big seasonal file
    output_file = "mlb_2026_season_game_logs.csv"
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"✅ Successfully merged {len(all_rows)} player game logs into {output_file}")
    print(f"Total rows: {len(all_rows)}")

if __name__ == "__main__":
    merge_all_logs()
