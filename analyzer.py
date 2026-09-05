"""
Para cada time, para cada posição:
1. Pega o rank FantasyPros de cada jogador seu.
2. Pega o rank FantasyPros do melhor agente livre disponível na sua liga.
3. Se um agente livre está pelo menos RANK_GAP_THRESHOLD posições melhor
   que o seu pior jogador daquela posição, isso vira uma sugestão.

Isso é a mesma pergunta que você fazia manualmente olhando as colunas
lado a lado na planilha — só que automatizado e para todas as posições de
uma vez.
"""
from matcher import build_lookup, find_rank
import config


def analyze_team(team_players: list[dict], free_agents: list[dict], rankings_by_position: dict) -> list[dict]:
    suggestions = []

    by_position = {}
    for p in team_players:
        by_position.setdefault(p["position"], []).append(p)

    fa_by_position = {}
    for p in free_agents:
        fa_by_position.setdefault(p["position"], []).append(p)

    for position, players in by_position.items():
        ranking_lookup = build_lookup(rankings_by_position.get(position, []))
        if not ranking_lookup:
            continue

        # Rank dos seus jogadores nessa posição (None = fora do ranking = ruim)
        ranked_mine = []
        for p in players:
            rank = find_rank(p["name"], ranking_lookup)
            ranked_mine.append((p, rank if rank is not None else 9999))
        ranked_mine.sort(key=lambda x: x[1])
        worst_player, worst_rank = ranked_mine[-1] if ranked_mine else (None, None)
        if worst_player is None:
            continue

        # Melhores agentes livres disponíveis nessa posição
        fa_lookup = build_lookup(fa_by_position.get(position, []))
        candidates = []
        for name, fa in fa_lookup.items():
            rank = find_rank(fa["name"], ranking_lookup)
            if rank is not None:
                candidates.append((fa, rank))
        candidates.sort(key=lambda x: x[1])

        for fa, fa_rank in candidates[:3]:
            if worst_rank - fa_rank >= config.RANK_GAP_THRESHOLD:
                suggestions.append({
                    "position": position.upper(),
                    "drop": worst_player["name"],
                    "drop_rank": worst_rank,
                    "add": fa["name"],
                    "add_rank": fa_rank,
                    "gap": worst_rank - fa_rank,
                })

    suggestions.sort(key=lambda s: -s["gap"])
    return suggestions
