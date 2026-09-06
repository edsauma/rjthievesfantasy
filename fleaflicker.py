"""
Cliente para a API pública do Fleaflicker (https://www.fleaflicker.com/api-docs/index.html).
Não exige chave para ligas públicas.

Duas particularidades importantes descobertas ao inspecionar a resposta real:

1. O roster vem dividido em vários "groups" (titulares, banco, taxi squad).
   Cada um tem sua própria lista de "slots" — é preciso percorrer todos.

2. O Fleaflicker usa códigos de posição de defesa mais granulares (CB, S,
   EDR, IL) do que o FantasyPros (DB, DL). Mapeamos para as categorias do
   FantasyPros para poder cruzar os rankings — mas guardamos a posição
   original também, já que é ela que a API do Fleaflicker espera ao buscar
   agentes livres.
"""
import requests

BASE = "https://www.fleaflicker.com/api"

# Fleaflicker -> categoria equivalente usada pelo FantasyPros
POSITION_TO_RANKING = {
    "cb": "db", "s": "db",
    "edr": "dl", "il": "dl", "de": "dl", "dt": "dl",
}


def _ranking_position(raw_position: str) -> str:
    raw = raw_position.lower()
    return POSITION_TO_RANKING.get(raw, raw)


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
                "position": _ranking_position(raw_position),  # usado para cruzar com FantasyPros
                "raw_position": raw_position,                  # usado para buscar agentes livres na Fleaflicker
                "team": pro.get("proTeamAbbreviation"),
            })
    return team


def get_free_agents(league_id: str, raw_positions: list[str], results_per_position: int = 50) -> list[dict]:
    """raw_positions deve conter os códigos ORIGINAIS do Fleaflicker
    (ex: 'cb', 's', 'edr', não 'db'/'dl'), pois é isso que a API espera."""
    free_agents = []
    for pos in raw_positions:
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
                "position": _ranking_position(raw_position),
                "raw_position": raw_position,
                "team": pro.get("proTeamAbbreviation"),
            })
    return free_agents
