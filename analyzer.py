"""
Para cada categoria de ranking (qb/rb/wr/te/k/lb/dl/db):
1. Pega o rank FantasyPros de cada jogador seu naquela categoria.
2. Pega o rank FantasyPros do melhor agente livre disponível na sua liga
   naquela mesma categoria.
3. Se um agente livre está pelo menos RANK_GAP_THRESHOLD posições melhor
   que o seu pior jogador da categoria, sinalizamos os dois: o seu (pra
   sair, seta vermelha) e o agente livre (pra entrar, seta verde).

Isso é a mesma pergunta que você fazia manualmente olhando as colunas
lado a lado na planilha — automatizado para todas as categorias de uma vez.
"""
from matcher import build_lookup, find_rank, normalize_name
import config


def _flag_key(player: dict) -> tuple:
    """Chave estável pra identificar um jogador dentro da própria lista
    (independe do 'id', que pode faltar ou vir de sistemas diferentes)."""
    return (normalize_name(player.get("name", "")), player.get("position", ""))


def attach_ranks(players: list[dict], rankings_by_position: dict) -> list[dict]:
    """Devolve a mesma lista de jogadores, cada um com o campo 'rank'
    preenchido (ou None se não achou no ranking do FantasyPros)."""
    out = []
    lookups_cache = {}
    for p in players:
        rank_pos = p.get("ranking_position", p.get("position", ""))
        if rank_pos not in lookups_cache:
            lookups_cache[rank_pos] = build_lookup(rankings_by_position.get(rank_pos, []))
        rank = find_rank(p["name"], lookups_cache[rank_pos])
        out.append({**p, "rank": rank})
    return out


def compute_flags(team_players: list[dict], free_agents: list[dict], rankings_by_position: dict):
    """Retorna (drop_keys, add_info):
    - drop_keys: set de chaves de jogadores do time que deveriam sair (seta vermelha)
    - add_info: dict {chave_do_agente_livre: gap} pra saber quem sinalizar
      de verde e mostrar o tamanho do ganho no tooltip
    """
    drop_keys = set()
    add_info = {}

    by_position = {}
    for p in team_players:
        by_position.setdefault(p.get("ranking_position", p["position"]), []).append(p)

    fa_by_position = {}
    for p in free_agents:
        fa_by_position.setdefault(p.get("ranking_position", p["position"]), []).append(p)

    for position, players in by_position.items():
        ranking_lookup = build_lookup(rankings_by_position.get(position, []))
        if not ranking_lookup:
            continue

        ranked_mine = [(p, find_rank(p["name"], ranking_lookup) or 9999) for p in players]
        ranked_mine.sort(key=lambda x: x[1])
        worst_player, worst_rank = ranked_mine[-1]

        fa_lookup = build_lookup(fa_by_position.get(position, []))
        candidates = []
        for name, fa in fa_lookup.items():
            rank = find_rank(fa["name"], ranking_lookup)
            if rank is not None:
                candidates.append((fa, rank))
        candidates.sort(key=lambda x: x[1])

        for fa, fa_rank in candidates[:3]:
            gap = worst_rank - fa_rank
            if gap >= config.RANK_GAP_THRESHOLD:
                drop_keys.add(_flag_key(worst_player))
                key = _flag_key(fa)
                add_info[key] = max(gap, add_info.get(key, 0))

    return drop_keys, add_info
