import csv
import glob
import os
from datetime import date

def merge_daily_into_seasonal():
    seasonal_file = "mlb_2026_season_game_logs.csv"
    daily_files = glob.glob("mlb_player_game_logs_*.csv")
    
    if not daily_files:
        print("No daily files found to merge.")
        return
    
    # Get the most recent daily file
    latest_daily = max(daily_files, key=os.path.getctime)
    print(f"Merging latest daily file: {latest_daily}")
    
    # Read all existing rows from seasonal file to avoid duplicates
    existing_game_pks = set()
    if os.path.exists(seasonal_file):
        with open(seasonal_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_game_pks.add(row.get('gamePk'))
    
    # Read the daily file and append only new rows
    new_rows = []
    with open(latest_daily, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        
        for row in reader:
            if row.get('gamePk') not in existing_game_pks:
                new_rows.append(row)
    
    if not new_rows:
        print("No new rows to append.")
        return
    
    # Append to seasonal file
    mode = 'a' if os.path.exists(seasonal_file) else 'w'
    with open(seasonal_file, mode, newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if mode == 'w':
            writer.writeheader()
        writer.writerows(new_rows)
    
    print(f"✅ Successfully appended {len(new_rows)} new rows from {latest_daily} to {seasonal_file}")

if __name__ == "__main__":
    merge_daily_into_seasonal()
