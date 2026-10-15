import pytest
from league_team_bot.riot_client import RiotClient


class FakeSession:
    def __init__(self): self.calls = []
    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if '/accounts/' in url: data = {"puuid": "player"}
        elif url.endswith('/ids'): data = ["MATCH_1", "MATCH_2"]
        else: data = {"info": {"participants": [{"puuid": "player", "win": url.endswith('1')}]}}
        class Response:
            def raise_for_status(self): pass
            def json(self): return data
        return Response()

def test_riot_lookup_encodes_id_and_counts_players():
    session = FakeSession(); client = RiotClient("dummy-test-key", session=session)
    assert client.recent_win_rate("name /", "tag") == {"played": 2, "wins": 1, "win_rate": .5}
    assert 'name%20%2F/tag' in session.calls[0][0]
    assert all(k["timeout"] == 20 for _, k in session.calls)
    assert session.calls[1][1]["params"] == {"start": 0, "count": 10}

def test_riot_rejects_missing_credentials_and_invalid_count(monkeypatch):
    monkeypatch.delenv("RIOT_API_KEY", raising=False)
    with pytest.raises(ValueError): RiotClient()
    with pytest.raises(ValueError): RiotClient('dummy').recent_matches('player', 0)
