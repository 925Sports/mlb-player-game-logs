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
    print(f"🚀 Pulling per-inning data for {date_str}")

    schedule = get_schedule(date_str)
    games = schedule.get("dates", [{}])[0].get("games", [])

    all_rows = []
    for game in games:
        game_pk = game["gamePk"]
        status = game["status"]["detailedState"]
        if status not in ["Final", "Completed Early", "Live"]:
            continue

        try:
            pbp = get_play_by_play(game_pk)
            plays = pbp.get("allPlays", [])

            for play in plays:
                inning = play.get("about", {}).get("inning")
                inningOrdinal = play.get("about", {}).get("inning")
                isTopInning = play.get("about", {}).get("isTopInning")
                batterId = play.get("matchup", {}).get("batter", {}).get("id")
                batterName = play.get("matchup", {}).get("batter", {}).get("fullName")
                pitcherId = play.get("matchup", {}).get("pitcher", {}).get("id")
                pitcherName = play.get("matchup", {}).get("pitcher", {}).get("fullName")
                atBatResult = play.get("result", {}).get("event")
                rbi = play.get("result", {}).get("rbi")
                runs = play.get("result", {}).get("runs")
                strikeOuts = 1 if "strikeout" in atBatResult.lower() else 0
                baseOnBalls = 1 if "walk" in atBatResult.lower() else 0
                hits = 1 if atBatResult in ["Single", "Double", "Triple", "Home Run"] else 0
                homeRuns = 1 if atBatResult == "Home Run" else 0
                description = play.get("result", {}).get("description")
                balls = play.get("count", {}).get("balls")
                strikes = play.get("count", {}).get("strikes")
                pitchesInAB = play.get("count", {}).get("pitches")
                isInPlay = play.get("about", {}).get("isInPlay")
                isStrike = play.get("about", {}).get("isStrike")
                isBall = play.get("about", {}).get("isBall")

                row = {
                    "gameDate": date_str,
                    "gamePk": game_pk,
                    "inning": inning,
                    "inningOrdinal": inningOrdinal,
                    "isTopInning": isTopInning,
                    "batterId": batterId,
                    "batterName": batterName,
                    "pitcherId": pitcherId,
                    "pitcherName": pitcherName,
                    "atBatResult": atBatResult,
                    "rbi": rbi,
                    "runs": runs,
                    "strikeOuts": strikeOuts,
                    "baseOnBalls": baseOnBalls,
                    "hits": hits,
                    "homeRuns": homeRuns,
                    "description": description,
                    "balls": balls,
                    "strikes": strikes,
                    "pitchesInAB": pitchesInAB,
                    "isInPlay": isInPlay,
                    "isStrike": isStrike,
                    "isBall": isBall
                }
                all_rows.append(row)

            print(f"✅ Extracted {len(plays)} plays from game {game_pk}")
            time.sleep(1.5)

        except Exception as e:
            print(f"⚠️ Error on game {game_pk}: {e}")

    if all_rows:
        filename = f"mlb_per_inning_logs_{date_str}.csv"
        keys = all_rows[0].keys()
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"✅ Saved {len(all_rows)} per-inning rows to {filename}")
    else:
        print("No plays found for this date.")

if __name__ == "__main__":
    main()
