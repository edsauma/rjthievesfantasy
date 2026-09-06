"""
Cliente para a API pública do Fleaflicker (https://www.fleaflicker.com/api-docs/index.html).
Não exige chave para ligas públicas.

O roster vem dividido em vários "groups" (titulares, banco, taxi squad) —
é preciso percorrer todos, não só o primeiro.

A posição exibida ('position') fica no código granular que o Fleaflicker
usa (CB, S, EDR, IL, LB...). Para cruzar com o FantasyPros (que usa
categorias mais amplas: DB, DL), guardamos também 'ranking_position'.
"""
import requests
import positions

BASE = "https://www.fleaflicker.com/api"


def _get(endpoint: str, params: dict):
    r = requests.get(f"{BASE}/{endpoint}", params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def get_my_team(league_id: str, team_id: str) -> list[dict]:
    data = _get("FetchRoster", {"leagueId": league_id, "teamId": team_id})
    team = []
    for group in data.get("groups", []):
        for slot in group.get("slots", []):
            player = slot.get("leaguePlayer") or {}
            pro = player.get("proPlayer", {})
            if not pro:
                continue
            raw_position = (pro.get("position") or "").lower()
            if not raw_position:
                continue
            team.append({
                "id": pro.get("id"),
                "name": pro.get("nameFull", ""),
                "position": raw_position,
                "ranking_position": positions.ranking_position(raw_position),
                "team": pro.get("proTeamAbbreviation"),
            })
    return team


def get_free_agents(league_id: str, raw_positions_list: list[str], results_per_position: int = 50) -> list[dict]:
    """raw_positions_list deve conter os códigos ORIGINAIS do Fleaflicker
    (ex: 'cb', 's', 'edr'), pois é isso que a API espera no filtro."""
    free_agents = []
    for pos in raw_positions_list:
        try:
            data = _get("FetchPlayerListing", {
                "leagueId": league_id,
                "filter.position": pos.upper(),
                "filter.status": "FREE_AGENT",
            })
        except requests.HTTPError:
            continue
        for entry in data.get("players", []):
            pro = entry.get("proPlayer", {})
            if not pro:
                continue
            raw_position = (pro.get("position") or pos).lower()
            free_agents.append({
                "id": pro.get("id"),
                "name": pro.get("nameFull", ""),
                "position": raw_position,
                "ranking_position": positions.ranking_position(raw_position),
                "team": pro.get("proTeamAbbreviation"),
            })
    return free_agents
