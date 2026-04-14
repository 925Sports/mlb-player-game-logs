import requests
import csv
import time
from datetime import date, timedelta

def get_schedule(target_date):
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={target_date}&gameType=R&hydrate=team,linescore,decisions,person,stats"
    print(f"Fetching schedule for {target_date}")
    response = requests.get(url)
    if response.status_code != 200:
        print(f"❌ Schedule failed: {response.status_code}")
        return []
    data = response.json()
    return data.get("dates", [])

def get_boxscore(game_pk):
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore?hydrate=person"
    response = requests.get(url)
    time.sleep(1.5)
    return response.json() if response.status_code == 200 else None

def extract_player_rows(game, box_data, game_date):
    rows = []
    if not box_data or not game:
        return rows

    # Full game metadata (exact columns from your original seasonal file)
    game_info = {
        "gameDate": game_date,
        "gamePk": game.get("gamePk"),
        "gameGuid": game.get("guid"),
        "link": game.get("link"),
        "gameType": game.get("gameType"),
        "season": game.get("season"),
        "officialDate": game.get("officialDate"),
        "description": game.get("description"),
        "dayNight": game.get("dayNight"),
        "gamedayType": game.get("gamedayType"),
        "doubleHeader": game.get("doubleHeader"),
        "tiebreaker": game.get("tiebreaker"),
        "seriesDescription": game.get("seriesDescription"),
        "seriesGameNumber": game.get("seriesGameNumber"),
        "gamesInSeries": game.get("gamesInSeries"),
        "gameNumber": game.get("gameNumber"),
        "status_abstractGameState": game.get("status", {}).get("abstractGameState"),
        "status_detailedState": game.get("status", {}).get("detailedState"),
        "venue_id": game.get("venue", {}).get("id"),
        "venue_name": game.get("venue", {}).get("name"),
        "home_team_id": game.get("teams", {}).get("home", {}).get("team", {}).get("id"),
        "home_team_name": game.get("teams", {}).get("home", {}).get("team", {}).get("name"),
        "home_team_abbreviation": game.get("teams", {}).get("home", {}).get("team", {}).get("abbreviation"),
        "home_score": game.get("teams", {}).get("home", {}).get("score"),
        "home_isWinner": game.get("teams", {}).get("home", {}).get("isWinner"),
        "away_team_id": game.get("teams", {}).get("away", {}).get("team", {}).get("id"),
        "away_team_name": game.get("teams", {}).get("away", {}).get("team", {}).get("name"),
        "away_team_abbreviation": game.get("teams", {}).get("away", {}).get("team", {}).get("abbreviation"),
        "away_score": game.get("teams", {}).get("away", {}).get("score"),
        "away_isWinner": game.get("teams", {}).get("away", {}).get("isWinner"),
    }

    # Player rows (add game metadata to every player)
    teams = box_data.get("teams", {})
    for side in ["home", "away"]:
        team_data = teams.get(side, {})
        players = team_data.get("players", {})
        for player_key, player in players.items():
            person = player.get("person", {})
            stats = player.get("stats", {})
            batting = stats.get("batting", {})
            pitching = stats.get("pitching", {})

            row = game_info.copy()  # Start with full game metadata
            row.update({
                "playerId": person.get("id"),
                "fullName": person.get("fullName"),
                "firstName": person.get("firstName"),
                "lastName": person.get("lastName"),
                "primaryNumber": person.get("primaryNumber"),
                "birthDate": person.get("birthDate"),
                "currentAge": person.get("currentAge"),
                "height": person.get("height"),
                "weight": person.get("weight"),
                "primaryPosition_code": person.get("primaryPosition", {}).get("code"),
                "primaryPosition_name": person.get("primaryPosition", {}).get("name"),
                "batSide_code": person.get("batSide", {}).get("code"),
                "batSide_description": person.get("batSide", {}).get("description"),
                "pitchHand_code": person.get("pitchHand", {}).get("code"),
                "pitchHand_description": person.get("pitchHand", {}).get("description"),
                "gameLogSummary": batting.get("summary") or pitching.get("summary") or "",
                "note": player.get("note", ""),
                # Batting
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
                "totalBases": batting.get("totalBases"),
                # Pitching
                "inningsPitched": pitching.get("inningsPitched"),
                "earnedRuns": pitching.get("earnedRuns"),
                "hitsAllowed": pitching.get("hits"),
                "homeRunsAllowed": pitching.get("homeRuns"),
                "strikeOutsPitching": pitching.get("strikeOuts"),
                "baseOnBallsPitching": pitching.get("baseOnBalls"),
                "pitchesThrown": pitching.get("pitchesThrown"),
                "wins": pitching.get("wins"),
                "losses": pitching.get("losses"),
                "saves": pitching.get("saves"),
            })
            rows.append(row)
    return rows

def main():
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"🚀 Starting detailed pull for {yesterday}")

    dates = get_schedule(yesterday)
    all_rows = []

    for d in dates:
        for game in d.get("games", []):
            game_pk = game.get("gamePk")
            status = game.get("status", {}).get("abstractGameState", "")
            if status in ["Final", "Completed Early"]:
                box_data = get_boxscore(game_pk)
                if box_data:
                    rows = extract_player_rows(game, box_data, yesterday)
                    all_rows.extend(rows)
                    print(f"  Game {game_pk}: added {len(rows)} rows")

    if all_rows:
        filename = f"mlb_player_game_logs_{yesterday}.csv"
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_rows[0].keys())
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"✅ Saved {len(all_rows)} rows to {filename}")
    else:
        print("⚠️ No rows collected")

if __name__ == "__main__":
    main()
