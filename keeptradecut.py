"""
Fonte alternativa de "quem está disponível" para ligas Sleeper.

A API pública do Sleeper às vezes demora a refletir a posse de jogadores
recém-adicionados via draft de rookies (o time "pertence" ao rookie na
prática, mas o roster retornado pela API do Sleeper ainda não foi
atualizado). O KeepTradeCut resolve isso de outro jeito: a própria página
de power rankings já embute no HTML tanto a lista COMPLETA de jogadores da
NFL (`playersArray`) quanto a posse real de cada time da liga
(`leagueTeams`, com a lista de playerIds de cada time). Cruzando os dois,
calculamos quem está de fato disponível, sem depender do sync do Sleeper.
"""
import re
import json
import requests

URL = "https://keeptradecut.com/dynasty/power-rankings/players"
RELEVANT_POSITIONS = {"qb", "rb", "wr", "te", "k"}


def _extract_js_array(html: str, var_name: str):
    match = re.search(rf"var\s+{var_name}\s*=\s*(\[.*?\]);", html, re.S)
    if not match:
        return None
    return json.loads(match.group(1))


def get_available_players(league_id: str) -> list[dict]:
    resp = requests.get(URL, params={"leagueId": league_id, "platform": "Sleeper"}, timeout=20)
    resp.raise_for_status()
    html = resp.text

    players = _extract_js_array(html, "playersArray")
    teams = _extract_js_array(html, "leagueTeams")
    if players is None or teams is None:
        raise ValueError(
            "Não encontrei playersArray/leagueTeams no HTML do KeepTradeCut "
            "— o formato da página pode ter mudado."
        )

    owned_ids = set()
    for team in teams:
        owned_ids.update(team.get("playerIds", []))

    available = []
    for p in players:
        pos = (p.get("position") or "").lower()
        if pos not in RELEVANT_POSITIONS:
            continue
        if p.get("playerID") in owned_ids:
            continue
        available.append({
            "id": p.get("playerID"),
            "name": p.get("playerName", ""),
            "position": pos,
            "team": p.get("team"),
        })
    return available
