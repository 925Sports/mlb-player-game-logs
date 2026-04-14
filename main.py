import requests
import csv
import time
from datetime import date, timedelta
import os

def get_schedule(target_date):
    url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={target_date}&gameType=R&hydrate=team,linescore,decisions,person,stats"
    print(f"Fetching schedule for {target_date}: {url}")
    response = requests.get(url)
    print(f"Status code: {response.status_code}")
    if response.status_code != 200:
        print("Error fetching schedule")
        return []
    data = response.json()
    print(f"Top-level keys: {list(data.keys())}")
    dates = data.get("dates", [])
    print(f"Number of date entries: {len(dates)}")
    return dates

def get_boxscore(game_pk):
    url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore?hydrate=person"
    print(f"  → Fetching boxscore for game {game_pk}")
    response = requests.get(url)
    time.sleep(1.5)  # Rate limit safety
    if response.status_code != 200:
        print(f"    Boxscore failed for {game_pk}")
        return None
    return response.json()

def extract_player_rows(game_pk, box_data, game_date):
    rows = []
    if not box_data:
        return rows
    
    teams = box_data.get("teams", {})
    for side in ["home", "away"]:
        team_data = teams.get(side, {})
        team = team_data.get("team", {})
        team_abbrev = team.get("abbreviation", "")
        
        players = team_data.get("players", {})
        for player_key, player in players.items():
            person = player.get("person", {})
            stats = player.get("stats", {})
            batting = stats.get("batting", {})
            pitching = stats.get("pitching", {})
            
            row = {
                "gameDate": game_date,
                "gamePk": game_pk,
                "playerId": person.get("id"),
                "fullName": person.get("fullName"),
                "firstName": person.get("firstName"),
                "lastName": person.get("lastName"),
                "primaryNumber": person.get("primaryNumber"),
                "birthDate": person.get("birthDate"),
                "currentAge": person.get("currentAge"),
                "height": person.get("height"),
                "weight": person.get("weight"),
                "primaryPosition": person.get("primaryPosition", {}).get("name"),
                "batSide": person.get("batSide", {}).get("description"),
                "pitchHand": person.get("pitchHand", {}).get("description"),
                "teamAbbrev": team_abbrev,
                "gameLogSummary": batting.get("summary") or pitching.get("summary") or "",
                "note": player.get("note", ""),  # Decision like (W, 1-0)
                # Batting stats
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
                # Pitching stats
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
            }
            rows.append(row)
    return rows

def main():
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"🚀 Starting pull for YESTERDAY: {yesterday}")
    
    dates = get_schedule(yesterday)
    all_rows = []
    
    for d in dates:
        games = d.get("games", [])
        print(f"Found {len(games)} games on {yesterday}")
        
        for game in games:
            game_pk = game.get("gamePk")
            status = game.get("status", {})
            detailed_state = status.get("detailedState", "")
            abstract_state = status.get("abstractGameState", "")
            print(f"  Game {game_pk} - Status: {abstract_state} / {detailed_state}")
            
            if abstract_state in ["Final", "Completed Early"] or "Final" in detailed_state:
                box_data = get_boxscore(game_pk)
                if box_data:
                    rows = extract_player_rows(game_pk, box_data, yesterday)
                    all_rows.extend(rows)
                    print(f"    Added {len(rows)} player rows")
            else:
                print(f"    Skipping game {game_pk} (not final)")
    
    print(f"\nTotal rows collected: {len(all_rows)}")
    
    if all_rows:
        filename = f"mlb_player_game_logs_{yesterday}.csv"
        fieldnames = all_rows[0].keys()
        
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)
        
        print(f"✅ SUCCESS! Saved {len(all_rows)} rows to {filename}")
        
        # Optional: also append to seasonal file
        seasonal_file = "mlb_2026_season_game_logs.csv"
        mode = "a" if os.path.exists(seasonal_file) else "w"
        with open(seasonal_file, mode, newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if mode == "w":
                writer.writeheader()
            writer.writerows(all_rows)
        print(f"✅ Appended to {seasonal_file}")
    else:
        print("⚠️ No rows collected — check the status prints above")

if __name__ == "__main__":
    main()
