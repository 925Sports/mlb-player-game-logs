import csv
import glob
import os

def rebuild_seasonal_from_dailies():
    seasonal_file = "mlb_2026_season_game_logs.csv"
    daily_files = sorted(glob.glob("mlb_player_game_logs_*.csv"))
    
    if not daily_files:
        print("No daily files found.")
        return
    
    print(f"Found {len(daily_files)} daily files. Rebuilding seasonal file...")
    
    all_rows = []
    fieldnames = None
    
    for daily in daily_files:
        with open(daily, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if fieldnames is None:
                fieldnames = reader.fieldnames
            all_rows.extend(list(reader))
    
    with open(seasonal_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    
    print(f"✅ Rebuilt seasonal file with {len(all_rows)} total rows (now includes April 13)")

if __name__ == "__main__":
    rebuild_seasonal_from_dailies()
