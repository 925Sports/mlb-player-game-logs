import requests
import csv
import time
from datetime import date

def get_schedule(date_str):
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}&gameType=R"
    print(f"Fetching schedule for {date_str}...")
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def get_play_by_play(game_pk):
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/feed/live"
    print(f"   Fetching play-by-play for game {game_pk}...")
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def main():
    date_str = "2026-04-12"   # Known date with games
    print(f"\n🚀 STARTING MINIMAL TEST — Pulling ONLY {date_str}")

    schedule = get_schedule(date_str)
    games = schedule.get("dates", [{}])[0].get("games", [])
    print(f"Found {len(games)} games in schedule")

    all_rows = []
    for game in games:
        game_pk = game["gamePk"]
        status = game.get("status", {}).get("detailedState", "")
        print(f"   Game {game_pk} status: {status}")
        if status not in ["Final", "Completed Early"]:
            print(f"   ⏭️  Skipping (not Final)")
            continue

        try:
            feed = get_play_by_play(game_pk)
            plays = feed.get("liveData", {}).get("plays", {}).get("allPlays", [])
            print(f"   ✅ Found {len(plays)} plays in game {game_pk}")

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

            time.sleep(1.5)
        except Exception as e:
            print(f"   ❌ Error on game {game_pk}: {e}")

    print(f"\nTotal plays collected: {len(all_rows)}")

    if all_rows:
        filename = f"mlb_per_inning_logs_{date_str}.csv"
        keys = all_rows[0].keys()
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"✅ SAVED daily file: {filename} ({len(all_rows)} rows)")

        # Force merge right here so big file is created
        print("🔄 Running merge now...")
        try:
            exec(open("merge_per_inning_logs.py").read())
            print("✅ Merge completed — big seasonal file should now exist")
        except Exception as e:
            print(f"⚠️ Merge failed: {e}")
    else:
        print("⚠️ No plays collected — nothing to save")

    print("\n🎉 Minimal test finished!")

if __name__ == "__main__":
    main()
