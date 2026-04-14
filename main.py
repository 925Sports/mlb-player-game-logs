import requests
import csv
from datetime import date
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
            batting_stats = player.get("stats", {}).get("batting", [{}])[0] if player.get("stats", {}).get("batting") else {}
            pitching_stats = player.get("stats", {}).get("pitching", [{}])[0] if player.get("stats", {}).get("pitching") else {}

            row = {
                "gameDate": game_date,
                "gamePk": game_pk,
                "playerId": person.get("id"),
                "fullName": person.get("fullName"),
                "primaryPosition": person.get("primaryPosition", {}).get("abbreviation", ""),
                "home_team_abbreviation": team_abbr,
                "atBats": batting_stats.get("atBats"),
                "hits": batting_stats.get("hits"),
                "doubles": batting_stats.get("doubles"),
                "triples": batting_stats.get("triples"),
                "homeRuns": batting_stats.get("homeRuns"),
                "rbi": batting_stats.get("rbi"),
                "runs": batting_stats.get("runs"),
                "strikeOuts": batting_stats.get("strikeOuts"),
                "baseOnBalls": batting_stats.get("baseOnBalls"),
                "stolenBases": batting_stats.get("stolenBases"),
                "caughtStealing": batting_stats.get("caughtStealing"),
                "groundIntoDoublePlay": batting_stats.get("groundIntoDoublePlay"),
                "plateAppearances": batting_stats.get("plateAppearances"),
                "gameLogSummary": batting_stats.get("summary"),
                "inningsPitched": pitching_stats.get("inningsPitched"),
                "earnedRuns": pitching_stats.get("earnedRuns"),
                "hitsAllowed": pitching_stats.get("hits"),
                "homeRunsAllowed": pitching_stats.get("homeRuns"),
                "strikeOutsPitching": pitching_stats.get("strikeOuts"),
                "baseOnBallsPitching": pitching_stats.get("baseOnBalls"),
                "pitchesThrown": pitching_stats.get("pitchesThrown"),
                "note": player.get("note"),   # Decision (W, L, SV, etc.)
            }
            rows.append(row)
    return rows

def main():
    today = date.today().strftime("%Y-%m-%d")
    print(f"🚀 Pulling detailed boxscore data for {today}")

    schedule = get_schedule(today)
    games = schedule.get("dates", [{}])[0].get("games", [])

    all_rows = []
    for game in games:
        game_pk = game["gamePk"]
        status = game.get("status", {}).get("detailedState", "")
        if status not in ["Final", "Completed Early", "Live"]:
            continue

        try:
            box = get_boxscore(game_pk)
            new_rows = extract_player_rows(game_pk, box, today)
            all_rows.extend(new_rows)
            print(f"✅ Added {len(new_rows)} players from game {game_pk}")
            time.sleep(1.5)
        except Exception as e:
            print(f"⚠️ Error on game {game_pk}: {e}")

    if all_rows:
        filename = f"mlb_player_game_logs_{today}.csv"
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"✅ Saved {len(all_rows)} rows to {filename}")
    else:
        print("No games found for today.")

if __name__ == "__main__":
    main()
