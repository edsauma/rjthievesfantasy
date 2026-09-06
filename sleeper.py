"""
Cliente para a API pública do Sleeper (https://docs.sleeper.com/).
Não exige autenticação para dados de ligas públicas/privadas que você participa
(desde que tenha o league_id, que você já usava nos links da planilha).
"""
import json
import os
import time
import requests
import positions

BASE = "https://api.sleeper.app/v1"

# Sleeper permite configurar IDP granular (DE/DT/CB/S) em vez das categorias
# largas do FantasyPros (DL/DB). Mapeamos para poder cruzar os rankings.
POSITION_TO_RANKING = {
    "de": "dl", "dt": "dl", "cb": "db", "s": "db",
}


def _ranking_position(raw_position: str) -> str:
    return POSITION_TO_RANKING.get(raw_position, raw_position)

PLAYERS_CACHE = os.path.join(os.path.dirname(__file__), "..", "data", "sleeper_players.json")
PLAYERS_CACHE_TTL_HOURS = 24


def _get(url: str):
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    return r.json()


def get_all_players() -> dict:
    """O endpoint de players é pesado (~5MB) e muda pouco: cacheamos em disco."""
    if os.path.exists(PLAYERS_CACHE):
        age_hours = (time.time() - os.path.getmtime(PLAYERS_CACHE)) / 3600
        if age_hours < PLAYERS_CACHE_TTL_HOURS:
            with open(PLAYERS_CACHE, "r") as f:
                return json.load(f)

    data = _get(f"{BASE}/players/nfl")
    os.makedirs(os.path.dirname(PLAYERS_CACHE), exist_ok=True)
    with open(PLAYERS_CACHE, "w") as f:
        json.dump(data, f)
    return data


def get_rosters(league_id: str) -> list[dict]:
    return _get(f"{BASE}/league/{league_id}/rosters")


def get_users(league_id: str) -> list[dict]:
    return _get(f"{BASE}/league/{league_id}/users")


def get_my_team(league_id: str, roster_id: str, all_players: dict) -> list[dict]:
    """Retorna os jogadores do seu roster, já com nome e posição resolvidos."""
    rosters = get_rosters(league_id)
    mine = next((r for r in rosters if str(r["roster_id"]) == str(roster_id)), None)
    if not mine:
        raise ValueError(f"roster_id {roster_id} não encontrado na liga {league_id}")

    team = []
    for pid in mine.get("players") or []:
        info = all_players.get(str(pid))
        if not info:
            continue
        pos = (info.get("position") or "").lower()
        if not pos:
            continue
        team.append({
            "id": pid,
            "name": info.get("full_name") or f"{info.get('first_name','')} {info.get('last_name','')}".strip(),
            "position": pos,                       # posição "de verdade", pra exibir/ordenar
            "rank_position": _ranking_position(pos),  # categoria usada pelo FantasyPros
            "team": info.get("team"),
        })
    return team


def get_free_agents(league_id: str, all_players: dict, positions: list[str]) -> list[dict]:
    """Agentes livres = todos os jogadores da NFL naquelas posições que não
    estão em NENHUM roster da liga."""
    rosters = get_rosters(league_id)
    owned_ids = set()
    for r in rosters:
        owned_ids.update(str(p) for p in (r.get("players") or []))

    free_agents = []
    positions_upper = {p.upper() for p in positions}
    for pid, info in all_players.items():
        if pid in owned_ids:
            continue
        pos = (info.get("position") or "").upper()
        if pos not in positions_upper:
            continue
        if info.get("status") not in ("Active", None):
            continue
        free_agents.append({
            "id": pid,
            "name": info.get("full_name") or f"{info.get('first_name','')} {info.get('last_name','')}".strip(),
            "position": pos.lower(),
            "rank_position": _ranking_position(pos.lower()),
            "team": info.get("team"),
        })
    return free_agents
