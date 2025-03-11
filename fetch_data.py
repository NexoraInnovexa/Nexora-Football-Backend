import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("FOOTBALL_API_KEY")

# Load API key from environment variable for security
API_KEY = os.getenv("FOOTBALL_API_KEY", "your_api_key")
URL = "https://api.football-data.org/v4/matches"

headers = {"X-Auth-Token": API_KEY}

def fetch_live_matches():
    """Fetch real-time football match data and return as a DataFrame."""
    response = requests.get(URL, headers=headers)
    
    if response.status_code == 200:
        matches = response.json().get("matches", [])
        data = []
        
        for match in matches:
            if "score" in match:
                home = match["homeTeam"]["name"]
                away = match["awayTeam"]["name"]
                home_score = match["score"]["fullTime"].get("home", 0)
                away_score = match["score"]["fullTime"].get("away", 0)
                winner = match["score"].get("winner")

                data.append({
                    "home_team": home,
                    "away_team": away,
                    "home_team_score": home_score,
                    "away_team_score": away_score,
                    "winner": 1 if winner == "HOME_TEAM" else 0 if winner == "AWAY_TEAM" else 2  # 2 = Draw
                })
        
        return pd.DataFrame(data) if data else None
    else:
        print(f"⚠️ Failed to fetch data: {response.status_code} - {response.text}")
        return None
