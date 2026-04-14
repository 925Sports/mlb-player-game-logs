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
    # Game-level info
    home_team = box_data.get("teams", {}).get("home", {})
    away_team = box_data.get("teams", {}).get("away", {})
    game_info = {
        "gameDate": game_date,
        "gamePk": game_pk,
        "venue_name": box_data.get("venue", {}).get("name", ""),
        "home_team_name": home_team.get("team", {}).get("name", ""),
        "home_team_abbreviation": home_team.get("team", {}).get("abbreviation", ""),
        "home_score": home_team.get("score"),
        "away_team_name": away_team.get("team", {}).get("name", ""),
        "away_team_abbreviation": away_team.get("team", {}).get("abbreviation", ""),
        "away_score": away_team.get("score"),
    }

    for team_side in ["home", "away"]:
        team = box_data.get("teams", {}).get(team_side, {})
        team_abbr = team.get("team", {}).get("abbreviation", "")
        players = team.get("players", {})

        for player_key, player_data in players.items():
            person = player_data.get("person", {})
            stats = player_data.get("stats", {})
            batting = stats.get("batting", [{}])[0] if isinstance(stats.get("batting"), list) else stats.get("batting", {})
            pitching = stats.get("pitching", [{}])[0] if isinstance(stats.get("pitching"), list) else stats.get("pitching", {})

            row = {
                **game_info,
                "playerId": person.get("id"),
                "fullName": person.get("fullName"),
                "primaryPosition": person.get("primaryPosition", {}).get("abbreviation"),
                "batSide": person.get("batSide", {}).get("code"),
                "pitchHand": person.get("pitchHand", {}).get("code"),
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
                "note": player_data.get("note"),   # Decision (W, L, SV, etc.)
            }
            rows.append(row)
    return rows

def main():
    today = date.today()
    dates_to_pull = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(5)]  # Last 5 days

    all_new_rows = []
    print(f"Pulling rich stats for dates: {dates_to_pull}")

    for d in dates_to_pull:
        print(f"\nProcessing {d}...")
        schedule = get_schedule(d)
        games = schedule.get("dates", [{}])[0].get("games", [])

        for game in games:
            game_pk = game["gamePk"]
            status = game.get("status", {}).get("detailedState", "")
            if status not in ["Final", "Completed Early", "Live"]:
                continue

            try:
                box = get_boxscore(game_pk)
                new_rows = extract_player_rows(game_pk, box, d)
                all_new_rows.extend(new_rows)
                print(f"  ✓ Added {len(new_rows)} detailed player rows from game {game_pk}")
                time.sleep(1.8)
            except Exception as e:
                print(f"  ✗ Error on game {game_pk}: {e}")

    # Append to seasonal file
    filename = "mlb_2026_season_game_logs.csv"
    file_exists = os.path.exists(filename)

    fieldnames = all_new_rows[0].keys() if all_new_rows else []

    mode = "a" if file_exists else "w"
    with open(filename, mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(all_new_rows)

    print(f"\n✅ Appended {len(all_new_rows)} rich rows to {filename}")

if __name__ == "__main__":
    main()
