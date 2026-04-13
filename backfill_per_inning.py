import requests
import csv
from datetime import date, timedelta
import time

def get_schedule(date_str):
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}&gameType=R"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def get_play_by_play(game_pk):
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/feed/live"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def main(start_date="2026-04-12"):   # <-- Changed to test with a known date
    end_date = date.fromisoformat("2026-04-12")   # Only pull one day for testing
    current = date.fromisoformat(start_date)
    print(f"🔄 Testing per-inning pull for {start_date} only (for debugging)")

    while current <= end_date:
        date_str = current.strftime("%Y-%m-%d")
        print(f"\n📅 Processing {date_str}")

        schedule = get_schedule(date_str)
        games = schedule.get("dates", [{}])[0].get("games", [])

        all_rows = []
        for game in games:
            game_pk = game["gamePk"]
            status = game.get("status", {}).get("detailedState", "")
            if status not in ["Final", "Completed Early"]:
                continue
            try:
                feed = get_play_by_play(game_pk)
                plays = feed.get("liveData", {}).get("plays", {}).get("allPlays", [])

                for play in plays:
                    about = play.get("about", {})
                    matchup = play.get("matchup", {})
                    result = play.get("result", {})
                    count = play.get("count", {})

                    row = {
                        "gameDate": date_str,
                        "gamePk": game_pk,
                        "inning": about.get("inning"),
                        "inningOrdinal": about.get("inning"),
                        "isTopInning": about.get("isTopInning"),
                        "batterId": matchup.get("batter", {}).get("id"),
                        "batterName": matchup.get("batter", {}).get("fullName"),
                        "pitcherId": matchup.get("pitcher", {}).get("id"),
                        "pitcherName": matchup.get("pitcher", {}).get("fullName"),
                        "atBatResult": result.get("event"),
                        "rbi": result.get("rbi"),
                        "runs": result.get("runs"),
                        "strikeOuts": 1 if result.get("event") == "Strikeout" else 0,
                        "baseOnBalls": 1 if result.get("event") == "Walk" else 0,
                        "hits": 1 if result.get("event") in ["Single", "Double", "Triple", "Home Run"] else 0,
                        "homeRuns": 1 if result.get("event") == "Home Run" else 0,
                        "description": result.get("description"),
                        "balls": count.get("balls"),
                        "strikes": count.get("strikes"),
                        "pitchesInAB": len(play.get("pitchIndex", [])) if play.get("pitchIndex") else 0,
                        "isInPlay": about.get("isInPlay"),
                        "isStrike": False,
                        "isBall": False
                    }
                    all_rows.append(row)

                print(f"   ✅ {len(plays)} plays from game {game_pk}")
                time.sleep(1.5)
            except Exception as e:
                print(f"   ⚠️ Error on game {game_pk}: {e}")

        if all_rows:
            filename = f"mlb_per_inning_logs_{date_str}.csv"
            keys = all_rows[0].keys()
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(all_rows)
            print(f"   ✅ Saved {len(all_rows)} rows to {filename}")
        else:
            print(f"   ⚠️ No plays found for {date_str}")

        current += timedelta(days=1)

    print("\n🎉 Test per-inning pull completed!")

if __name__ == "__main__":
    main()
