"""
Cliente para a API pública do Fleaflicker (https://www.fleaflicker.com/api-docs/index.html).
Não exige chave para ligas públicas.

O roster vem dividido em vários "groups" (titulares, banco, taxi squad) —
é preciso percorrer todos, não só o primeiro.

A posição exibida ('position') fica no código granular que o Fleaflicker
usa (CB, S, EDR, IL, LB...). Para cruzar com o FantasyPros (que usa
categorias mais amplas: DB, DL), guardamos também 'ranking_position'.

Alguns jogadores têm elegibilidade dupla e a própria API devolve isso como
uma posição composta (ex: "EDR/IL"). Guardamos a primeira como posição
"principal" (pra exibição/ranking) e a lista completa em
'position_options', usada só na hora de decidir em quais slots da
escalação o jogador pode entrar.
"""
import requests
import positions

BASE = "https://www.fleaflicker.com/api"


def _get(endpoint: str, params: dict):
    r = requests.get(f"{BASE}/{endpoint}", params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def _parse_position(raw: str):
    raw = (raw or "").lower()
    options = [p for p in raw.split("/") if p]
    primary = options[0] if options else raw
    return primary, (options or [raw])


def get_my_team(league_id: str, team_id: str) -> list[dict]:
    data = _get("FetchRoster", {"leagueId": league_id, "teamId": team_id, "sport": "NFL"})
    team = []
    for group in data.get("groups", []):
        for slot in group.get("slots", []):
            player = slot.get("leaguePlayer") or {}
            pro = player.get("proPlayer", {})
            if not pro:
                continue
            raw_position = pro.get("position") or ""
            if not raw_position:
                continue
            primary, options = _parse_position(raw_position)
            team.append({
                "id": pro.get("id"),
                "name": pro.get("nameFull", ""),
                "position": primary,
                "position_options": options,
                "ranking_position": positions.ranking_position(primary),
                "team": pro.get("proTeamAbbreviation"),
            })
    return team


def get_free_agents(league_id: str, raw_positions_list: list[str], results_per_position: int = 50) -> list[dict]:
    """raw_positions_list deve conter os códigos ORIGINAIS do Fleaflicker
    (ex: 'cb', 's', 'edr'), pois é isso que a API espera no filtro.

    Parâmetros conforme a documentação oficial
    (https://www.fleaflicker.com/api-docs/index.html#operation--FetchPlayerListing-get):
    'filter.position_eligibility' (lista de códigos de posição) e
    'filter.free_agent_only' (booleano) — não 'filter.position'/'filter.status',
    que eu tinha usado antes por engano."""
    free_agents = []
    seen_ids = set()
    for pos in raw_positions_list:
        try:
            data = _get("FetchPlayerListing", {
                "leagueId": league_id,
                "sport": "NFL",
                "filter.positionEligibility": pos.upper(),
                "filter.freeAgentOnly": "true",
            })
        except requests.HTTPError:
            continue
        for entry in data.get("players", []):
            pro = entry.get("proPlayer", {})
            if not pro:
                continue
            player_id = pro.get("id")
            if player_id is not None and player_id in seen_ids:
                # Jogador com elegibilidade dupla (ex: "EDR/IL") aparece em
                # mais de uma busca de posição — já processamos ele antes,
                # não duplica na lista.
                continue
            if player_id is not None:
                seen_ids.add(player_id)
            raw_position = pro.get("position") or pos
            primary, options = _parse_position(raw_position)
            free_agents.append({
                "id": player_id,
                "name": pro.get("nameFull", ""),
                "position": primary,
                "position_options": options,
                "ranking_position": positions.ranking_position(primary),
                "team": pro.get("proTeamAbbreviation"),
            })
    return free_agents
