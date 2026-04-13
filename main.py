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

def extract_player_rows(game, box, date_str):
    rows = []
    game_pk = game["gamePk"]
    home = game["teams"]["home"]
    away = game["teams"]["away"]
    venue = box.get("teams", {}).get("home", {}).get("team", {}).get("venue", {})

    game_info = {
        "gameDate": date_str,
        "gamePk": game_pk,
        "gameGuid": game.get("gameGuid"),
        "link": f"/api/v1.1/game/{game_pk}/feed/live",
        "gameType": "R",
        "season": "2026",
        "officialDate": date_str,
        "description": game.get("description", ""),
        "dayNight": game.get("dayNight", ""),
        "gamedayType": game.get("gamedayType", ""),
        "doubleHeader": game.get("doubleHeader", ""),
        "tiebreaker": game.get("tiebreaker", ""),
        "seriesDescription": game.get("seriesDescription", ""),
        "seriesGameNumber": game.get("seriesGameNumber"),
        "gamesInSeries": game.get("gamesInSeries"),
        "gameNumber": game.get("gameNumber"),
        "status_abstractGameState": game["status"].get("abstractGameState"),
        "status_detailedState": game["status"].get("detailedState"),
        "venue_id": venue.get("id"),
        "venue_name": venue.get("name"),
        "home_team_id": home["team"]["id"],
        "home_team_name": home["team"]["name"],
        "home_team_abbreviation": home["team"]["abbreviation"],
        "home_score": home.get("score"),
        "home_isWinner": home.get("isWinner"),
        "away_team_id": away["team"]["id"],
        "away_team_name": away["team"]["name"],
        "away_team_abbreviation": away["team"]["abbreviation"],
        "away_score": away.get("score"),
        "away_isWinner": away.get("isWinner"),
    }

    for side in ["home", "away"]:
        players_dict = box.get("teams", {}).get(side, {}).get("players", {})
        for pid, player in players_dict.items():
            if "stats" not in player: 
                continue
            person = player.get("person", {})
            stats = player.get("stats", {})
            batting = stats.get("batting", {})
            pitching = stats.get("pitching", {})

            row = {**game_info}
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
                "gameLogSummary": batting.get("summary") or pitching.get("summary"),
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
                "note": pitching.get("note"),
            })
            rows.append(row)
    return rows

def main(date_str=None):
    if not date_str:
        date_str = date.today().strftime("%Y-%m-%d")   # Now uses today's date automatically
    print(f"🚀 Pulling data for {date_str}")

    schedule = get_schedule(date_str)
    games = schedule.get("dates", [{}])[0].get("games", [])

    all_rows = []
    for game in games:
        game_pk = game["gamePk"]
        status = game["status"]["detailedState"]
        if status not in ["Final", "Completed Early", "Live"]:
            continue
        try:
            box = get_boxscore(game_pk)
            rows = extract_player_rows(game, box, date_str)
            all_rows.extend(rows)
            print(f"✅ {len(rows)} players from game {game_pk}")
            time.sleep(1.2)
        except Exception as e:
            print(f"⚠️ Error on {game_pk}: {e}")

    if all_rows:
        filename = f"mlb_player_game_logs_{date_str}.csv"
        keys = all_rows[0].keys()
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"✅ Saved {len(all_rows)} rows to {filename}")
    else:
        print("No completed games found for this date.")

if __name__ == "__main__":
    main()
