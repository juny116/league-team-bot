# League Team Bot

Discord에서 참가자를 선택해 팀을 구성하고 MongoDB에 경기·Elo를 기록하는 봇입니다. Riot 계정의 최근 경기 조회를 선택 기능으로 제공합니다.

## 코드 구조

| 경로 | 역할 |
|---|---|
| `league_team_bot/bot.py` | 팀 구성·기록 봇 및 !recent 명령 |
| `league_team_bot/player_store.py` | MongoDB 사용자·경기 저장 |
| `league_team_bot/team_selection_views.py` | Discord 참가자 선택 UI |
| `league_team_bot/riot_client.py` | Riot ID·PUUID·경기 조회 |
| `league_team_bot/legacy_selection_bot.py` | DB 없는 초기 참가자 선택 구현 |

## 실행

```bash
pip install -e ".[runtime]"
python -m league_team_bot.bot --config /path/to/bot.yaml
```

봇은 외부 실행 파일의 `discord.token`과 `mongo.host`, `mongo.username`, `mongo.password`를 읽습니다. Riot 기능에는 RIOT_API_KEY가 필요합니다. `!recent 이름#태그`로 최근 경기 승수를 조회합니다. 초기 선택 봇은 `riot.user_list`를 사용하며 현재 DB 기반 봇과 실행 방식이 다릅니다. [Riot API](https://developer.riotgames.com/apis/)의 Account-v1·Match-v5 경로를 사용합니다.

## Source and license

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for project origins and third-party licenses.
