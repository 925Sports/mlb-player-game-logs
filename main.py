import requests
import csv
from datetime import date, timedelta
import time
import os

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
                "note": player.get("note"),   # Decision (W, L, SV, etc.)
            }
            rows.append(row)
    return rows

def main():
    # Pull YESTERDAY's games so they are guaranteed "Final"
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"🚀 Pulling detailed boxscore data for YESTERDAY: {yesterday}")

    schedule = get_schedule(yesterday)
    games = schedule.get("dates", [{}])[0].get("games", [])

    all_rows = []
    for game in games:
        game_pk = game["gamePk"]
        status = game.get("status", {}).get("detailedState", "")
        if status not in ["Final", "Completed Early", "Live"]:
            continue

        try:
            box = get_boxscore(game_pk)
            new_rows = extract_player_rows(game_pk, box, yesterday)
            all_rows.extend(new_rows)
            print(f"✅ Added {len(new_rows)} players from game {game_pk}")
            time.sleep(1.5)
        except Exception as e:
            print(f"⚠️ Error on game {game_pk}: {e}")

    if not all_rows:
        print("No completed games found for yesterday.")
        return

    filename = "mlb_2026_season_game_logs.csv"
    file_exists = os.path.exists(filename)

    mode = "a" if file_exists else "w"
    with open(filename, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
        if not file_exists:
            writer.writeheader()
        writer.writerows(all_rows)

    print(f"✅ Appended {len(all_rows)} new rows to {filename}")

if __name__ == "__main__":
    main()
