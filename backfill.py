from main import main
from datetime import date, timedelta

# Backfill from Opening Day 2026 until today
start_date = date(2026, 3, 26)
end_date = date.today()

current = start_date
while current <= end_date:
    print(f"Starting backfill for {current}")
    main(current.strftime("%Y-%m-%d"))
    current += timedelta(days=1)

print("✅ Full backfill completed!")
