import config
import positions
from matcher import normalize_name, build_lookup


def _flag_key(player):
    """Chave estável para identificar um jogador numa lista (independente de
    qual posição/grupo ele está sendo exibido em)."""
    return (normalize_name(player.get("name", "")), player.get("position"))


def _build_lookups(rankings_by_position):
    """Monta, uma única vez, um dict categoria -> lookup (nome normalizado ->
    rank) a partir do cache de rankings do FantasyPros, para reaproveitar
    entre todos os jogadores em vez de reconstruir a cada chamada."""
    return {cat: build_lookup(lst) for cat, lst in rankings_by_position.items()}


def _best_rank(player, lookups):
    """Retorna o melhor (menor) rank do FantasyPros para o jogador.

    Jogadores "híbridos" podem aparecer em mais de uma categoria de ranking
    do FantasyPros (ex: um edge rusher listado tanto em LB quanto em DL).
    Quando a posição do jogador mapeia para uma dessas categorias que se
    sobrepõem, consultamos todas elas e usamos o melhor rank encontrado."""
    category = positions.ranking_position(player.get("position"))
    if category is None:
        return None

    name = normalize_name(player.get("name", ""))
    best = None
    for cat in positions.overlap_categories(category):
        lookup = lookups.get(cat)
        if not lookup:
            continue
        rank = lookup.get(name)
        if rank is not None and (best is None or rank < best):
            best = rank
    return best


def attach_ranks(players, rankings_by_position):
    """Anota cada jogador com seu melhor rank do FantasyPros (ver _best_rank)."""
    lookups = _build_lookups(rankings_by_position)
    for p in players:
        p["rank"] = _best_rank(p, lookups)
    return players


def attach_extra_rank(players, ranking_list, field_name):
    """Anota cada jogador com um rank vindo de uma lista específica (usado
    para os rankings combinados de FLEX e IDP do FantasyPros)."""
    lookup = build_lookup(ranking_list)
    for p in players:
        name = normalize_name(p.get("name", ""))
        p[field_name] = lookup.get(name)
    return players


def compute_flags(team_players, free_agents, rankings_by_position):
    """Agrupa o time e os agentes livres por posição BRUTA/granular (CB com
    CB, S com S, LB com LB, etc. — nunca misturando posições diferentes) e,
    dentro de cada grupo, sinaliza o pior jogador do time para troca e o(s)
    melhor(es) agente(s) livre(s) disponíveis, quando a diferença de rank for
    grande o suficiente. Os ranks usados já são os melhores entre categorias
    sobrepostas (attach_ranks), então um jogador híbrido é comparado de forma
    justa sem precisar de lógica extra aqui.

    Retorna (drop_keys, add_info): um set de chaves a sinalizar como "sair" e
    um dict chave -> maior gap encontrado, para sinalizar como "entrar"."""
    drop_keys = set()
    add_info = {}

    groups = {}
    for p in team_players:
        groups.setdefault(p["position"], {"team": [], "fa": []})["team"].append(p)
    for p in free_agents:
        groups.setdefault(p["position"], {"team": [], "fa": []})["fa"].append(p)

    for raw_pos, bucket in groups.items():
        team_list = [p for p in bucket["team"] if p.get("rank") is not None]
        fa_list = [p for p in bucket["fa"] if p.get("rank") is not None]
        if not team_list or not fa_list:
            continue

        category = positions.ranking_position(raw_pos)
        threshold = config.RANK_GAP_THRESHOLD_OVERRIDES.get(
            category, config.RANK_GAP_THRESHOLD
        )

        worst_team = max(team_list, key=lambda p: p["rank"])
        best_fa = min(fa_list, key=lambda p: p["rank"])

        gap = worst_team["rank"] - best_fa["rank"]
        if gap >= threshold:
            drop_keys.add(_flag_key(worst_team))
            for fa in fa_list:
                this_gap = worst_team["rank"] - fa["rank"]
                if this_gap >= threshold:
                    key = _flag_key(fa)
                    prev_gap = add_info.get(key)
                    if prev_gap is None or this_gap > prev_gap:
                        add_info[key] = this_gap

    return drop_keys, add_info
