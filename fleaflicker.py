"""
Cliente para a API pública do Fleaflicker (https://www.fleaflicker.com/api-docs/index.html).
Não exige chave para ligas públicas. Isso substitui o Web.BrowserContents +
seletores CSS que a planilha original usava para raspar as páginas HTML —
muito mais estável, pois é a mesma API que o app oficial usa.

Observação: a Fleaflicker pode alterar a estrutura do JSON de tempos em tempos.
Os acessos abaixo usam .get() com fallback para não quebrar o script inteiro
se um campo mudar de lugar — mas vale checar o retorno bruto se algo vier vazio.
"""
import requests

BASE = "https://www.fleaflicker.com/api"


def _get(endpoint: str, params: dict):
    r = requests.get(f"{BASE}/{endpoint}", params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def _player_name(entry: dict) -> str:
    name = entry.get("proPlayer", {}).get("nameFull")
    return name or ""


def get_my_team(league_id: str, team_id: str) -> list[dict]:
    data = _get("FetchRoster", {"leagueId": league_id, "teamId": team_id})
    team = []
    for slot in data.get("groups", [{}])[0].get("slots", []):
        player = slot.get("leaguePlayer") or {}
        pro = player.get("proPlayer", {})
        if not pro:
            continue
        team.append({
            "id": pro.get("id"),
            "name": pro.get("nameFull", ""),
            "position": (pro.get("position") or "").lower(),
            "team": pro.get("proTeamAbbreviation"),
        })
    return team


def get_free_agents(league_id: str, positions: list[str], results_per_position: int = 50) -> list[dict]:
    """A Fleaflicker pagina os resultados; para cada posição buscamos as
    primeiras N entradas ordenadas por rank de titularidade (proxy razoável
    de qualidade quando ainda não cruzamos com o FantasyPros)."""
    free_agents = []
    for pos in positions:
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
            free_agents.append({
                "id": pro.get("id"),
                "name": pro.get("nameFull", ""),
                "position": (pro.get("position") or pos).lower(),
                "team": pro.get("proTeamAbbreviation"),
            })
    return free_agents
