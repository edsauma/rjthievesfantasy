"""
Para cada posição GRANULAR (a que a plataforma realmente usa: CB, S, EDR,
IL, LB no Fleaflicker; QB, RB, WR, TE, K, DL, LB, DB no Sleeper):
1. Pega o rank FantasyPros de cada jogador seu naquela posição (usando a
   categoria de ranking correspondente — CB e S, por exemplo, usam o
   mesmo ranking combinado de DB do FantasyPros, mas só comparamos
   jogadores da MESMA posição entre si: CB com CB, S com S).
2. Pega o rank do melhor agente livre disponível na sua liga, também
   restrito à mesma posição granular.
3. Se o agente livre está pelo menos RANK_GAP_THRESHOLD posições melhor
   que o seu pior jogador ali, sinalizamos os dois.
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


def attach_extra_rank(players: list[dict], ranking_list: list[dict], field_name: str) -> list[dict]:
    """Anexa um rank adicional vindo de um ranking 'coringa' do FantasyPros
    (FLEX ofensivo ou IDP), que cobre várias posições ao mesmo tempo —
    usado pra decidir quem entra nos slots de flex da escalação."""
    lookup = build_lookup(ranking_list)
    out = []
    for p in players:
        rank = find_rank(p["name"], lookup)
        out.append({**p, field_name: rank})
    return out


def compute_flags(team_players: list[dict], free_agents: list[dict], rankings_by_position: dict):
    """Retorna (drop_keys, add_info), comparando sempre dentro da MESMA
    posição granular (ex: CB só compete com CB, nunca com S)."""
    drop_keys = set()
    add_info = {}

    by_position = {}
    for p in team_players:
        by_position.setdefault(p["position"], []).append(p)

    fa_by_position = {}
    for p in free_agents:
        fa_by_position.setdefault(p["position"], []).append(p)

    for position, players in by_position.items():
        ranking_category = players[0].get("ranking_position", position)
        ranking_lookup = build_lookup(rankings_by_position.get(ranking_category, []))
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
