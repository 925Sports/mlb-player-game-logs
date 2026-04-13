import requests
import csv
from datetime import date
import time

def get_schedule(date_str):
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}&gameType=R&hydrate=team,linescore,decisions,person,stats"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def get_play_by_play(game_pk):
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/playByPlay"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def main(date_str=None):
    if not date_str:
        date_str = date.today().strftime("%Y-%m-%d")
    
    print(f"🚀 Starting per-inning pull for {date_str}")

    schedule = get_schedule(date_str)
    games = schedule.get("dates", [{}])[0].get("games", [])

    all_rows = []
    for game in games:
        game_pk = game["gamePk"]
        status = game.get("status", {}).get("detailedState", "")
        if status not in ["Final", "Completed Early", "Live"]:
            continue

        try:
            pbp = get_play_by_play(game_pk)
            plays = pbp.get("allPlays", [])

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
                    "strikeOuts": 1 if "strikeout" in str(result.get("event", "")).lower() else 0,
                    "baseOnBalls": 1 if any(x in str(result.get("event", "")).lower() for x in ["walk", "base on balls"]) else 0,
                    "hits": 1 if result.get("event") in ["Single", "Double", "Triple", "Home Run"] else 0,
                    "homeRuns": 1 if result.get("event") == "Home Run" else 0,
                    "description": result.get("description"),
                    "balls": count.get("balls"),
                    "strikes": count.get("strikes"),
                    "pitchesInAB": count.get("pitches"),
                    "isInPlay": about.get("isInPlay"),
                    "isStrike": about.get("isStrike"),
                    "isBall": about.get("isBall")
                }
                all_rows.append(row)

            print(f"✅ Processed {len(plays)} plays from game {game_pk}")
            time.sleep(1.8)  # Slightly longer delay for safety

        except Exception as e:
            print(f"⚠️ Error processing game {game_pk}: {e}")

    if all_rows:
        filename = f"mlb_per_inning_logs_{date_str}.csv"
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"✅ Saved {len(all_rows)} rows to {filename}")
    else:
        print("No plays found.")

if __name__ == "__main__":
    main()
