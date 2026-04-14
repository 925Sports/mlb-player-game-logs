import requests
import csv
from datetime import date, timedelta
import time

def get_schedule(date_str):
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}&gameType=R&hydrate=team,linescore,decisions,person,stats"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def get_boxscore(game_pk):
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore?hydrate=person"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def extract_player_rows(game_pk, box_data, game_date):
    rows = []
    for side in ["home", "away"]:
        team_data = box_data.get("teams", {}).get(side, {})
        team_abbr = team_data.get("team", {}).get("abbreviation", "")
        
        for player_key, player in team_data.get("players", {}).items():
            person = player.get("person", {})
            batting = player.get("stats", {}).get("batting", [{}])[0] if player.get("stats", {}).get("batting") else {}
            pitching = player.get("stats", {}).get("pitching", [{}])[0] if player.get("stats", {}).get("pitching") else {}

            row = {
                "gameDate": game_date,
                "gamePk": game_pk,
                "playerId": person.get("id"),
                "fullName": person.get("fullName"),
                "primaryPosition": person.get("primaryPosition", {}).get("abbreviation", ""),
                "home_team_abbreviation": team_abbr,
                "atBats": batting.get("atBats"),
                "hits": batting.get("hits"),
                "doubles": batting.get("doubles"),
                "triples": batting.get("triples"),
                "homeRuns": batting.get("homeRuns"),
                "rbi": batting.get("rbi"),
                "runs": batting.get("runs"),
                "strikeOuts": batting.get("strikeOuts"),
                "baseOnBalls": batting.get("baseOnBalls"),
                "stolenBases": batting.get("stolenBases"),
                "caughtStealing": batting.get("caughtStealing"),
                "groundIntoDoublePlay": batting.get("groundIntoDoublePlay"),
                "plateAppearances": batting.get("plateAppearances"),
                "gameLogSummary": batting.get("summary"),
                "inningsPitched": pitching.get("inningsPitched"),
                "earnedRuns": pitching.get("earnedRuns"),
                "hitsAllowed": pitching.get("hits"),
                "homeRunsAllowed": pitching.get("homeRuns"),
                "strikeOutsPitching": pitching.get("strikeOuts"),
                "baseOnBallsPitching": pitching.get("baseOnBalls"),
                "pitchesThrown": pitching.get("pitchesThrown"),
                "note": player.get("note"),
            }
            rows.append(row)
    return rows

def main():
    test_date = "2026-04-13"   # Hard-coded for debugging
    print(f"🚀 DEBUG MODE - Pulling detailed boxscore data for {test_date}")

    schedule = get_schedule(test_date)
    games = schedule.get("dates", [{}])[0].get("games", [])

    print(f"Found {len(games)} games on {test_date}")

    all_rows = []
    for game in games:
        game_pk = game["gamePk"]
        status = game.get("status", {}).get("detailedState", "")
        print(f"  Game {game_pk} status: {status}")
        if status not in ["Final", "Completed Early", "Live"]:
            print(f"    Skipping - not Final")
            continue

        try:
            box = get_boxscore(game_pk)
            new_rows = extract_player_rows(game_pk, box, test_date)
            all_rows.extend(new_rows)
            print(f"✅ Added {len(new_rows)} players from game {game_pk}")
            time.sleep(1.5)
        except Exception as e:
            print(f"⚠️ Error on game {game_pk}: {e}")

    if all_rows:
        filename = f"mlb_player_game_logs_{test_date}.csv"
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"✅ SUCCESS - Saved {len(all_rows)} rows to {filename}")
    else:
        print("❌ No rows found for this date.")

if __name__ == "__main__":
    main()
