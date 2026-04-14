from datetime import date, timedelta
import per_inning_main  # This calls the main function we already have

def backfill_per_inning():
    start_date = date(2026, 3, 25)          # First day of 2026 MLB season
    end_date = date.today() - timedelta(days=1)  # Yesterday (safe for today’s daily run)
    
    current = start_date
    while current <= end_date:
        date_str = current.strftime("%Y-%m-%d")
        print(f"\n{'='*60}")
        print(f"BACKFILLING: {date_str}")
        print(f"{'='*60}")
        
        per_inning_main.main(date_str)   # Runs the exact same logic as daily
        current += timedelta(days=1)
    
    print("\n🎉 Backfill completed! All per-inning data has been pulled.")

if __name__ == "__main__":
    backfill_per_inning()
