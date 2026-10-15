"""Riot account and match lookup, configured by the caller."""
import os
from urllib.parse import quote
import requests

class RiotClient:
    def __init__(self, api_key=None, region="asia", session=None):
        self.api_key = api_key or os.environ.get("RIOT_API_KEY")
        if not self.api_key:
            raise ValueError("Set RIOT_API_KEY or pass api_key")
        if region not in {"americas", "asia", "europe", "sea"}:
            raise ValueError("Unsupported Riot routing region")
        self.base_url = f"https://{region}.api.riotgames.com"
        self.session = session or requests.Session()

    def _get(self, path, params=None):
        response = self.session.get(self.base_url + path, params=params, headers={"X-Riot-Token": self.api_key}, timeout=20)
        response.raise_for_status()
        return response.json()

    def account(self, game_name, tag_line):
        return self._get(f"/riot/account/v1/accounts/by-riot-id/{quote(game_name, safe='')}/{quote(tag_line, safe='')}")

    def recent_matches(self, puuid, count=10):
        if not 1 <= count <= 100:
            raise ValueError("count must be between 1 and 100")
        return self._get(f"/lol/match/v5/matches/by-puuid/{quote(puuid, safe='')}/ids", {"start": 0, "count": count})

    def match(self, match_id):
        return self._get(f"/lol/match/v5/matches/{quote(match_id, safe='')}")

    def recent_win_rate(self, game_name, tag_line, count=10):
        puuid = self.account(game_name, tag_line)["puuid"]
        ids = self.recent_matches(puuid, count)
        wins = played = 0
        for match_id in ids:
            participants = self.match(match_id)["info"]["participants"]
            player = next((p for p in participants if p["puuid"] == puuid), None)
            if player is not None:
                played += 1
                wins += int(player["win"])
        return {"played": played, "wins": wins, "win_rate": wins / played if played else None}
