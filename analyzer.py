import config
import positions
from matcher import normalize_name, build_lookup

# Quantidade máxima de agentes livres sinalizados como "ENTRAR" por grupo de
# posição numa mesma rodada de sugestões.
MAX_ADD_SUGGESTIONS = 5


def _flag_key(player):
    """Chave estável para identificar um jogador numa lista (independente de
    qual posição/grupo ele está sendo exibido em)."""
    return (normalize_name(player.get("name", "")), player.get("position"))


def _build_lookups(rankings_by_position):
    """Monta, uma única vez, um dict categoria -> lookup (nome normalizado ->
    rank) a partir do cache de rankings do FantasyPros, para reaproveitar
    entre todos os jogadores em vez de reconstruir a cada chamada."""
    return {cat: build_lookup(lst) for cat, lst in rankings_by_position.items()}


def _resolve_rank(player, lookups):
    """Retorna (melhor_rank, categoria_vencedora) para o jogador.

    Jogadores "híbridos" podem aparecer em mais de uma categoria de ranking
    do FantasyPros (ex: um edge rusher listado tanto em LB quanto em DL).
    Quando a posição do jogador mapeia para uma dessas categorias que se
    sobrepõem (lb/dl/db), consultamos todas elas e usamos o melhor rank
    encontrado, junto com a categoria de onde ele veio."""
    native_category = positions.ranking_position(player.get("position"))
    if native_category is None:
        return None, None

    name = normalize_name(player.get("name", ""))
    best = None
    best_cat = native_category
    for cat in positions.overlap_categories(native_category):
        lookup = lookups.get(cat)
        if not lookup:
            continue
        rank = lookup.get(name)
        if rank is not None and (best is None or rank < best):
            best = rank
            best_cat = cat
    return best, best_cat


def attach_ranks(players, rankings_by_position):
    """Anota cada jogador com seu melhor rank do FantasyPros (ver
    _resolve_rank). Quando o melhor rank vem de uma categoria diferente da
    posição "nativa" do jogador na plataforma (caso de jogadores híbridos
    nas categorias defensivas lb/dl/db), a posição do jogador é atualizada
    para essa categoria vencedora — assim ele passa a ser agrupado/exibido
    corretamente (ex: um LB que rankeia melhor como DL some de "LB" e passa
    a aparecer em "DL"). Isso não afeta `position_options`, usado para
    decidir em quais slots da escalação o jogador pode ser posicionado."""
    lookups = _build_lookups(rankings_by_position)
    for p in players:
        native_category = positions.ranking_position(p.get("position"))
        rank, best_cat = _resolve_rank(p, lookups)
        p["rank"] = rank
        p["rank_category"] = best_cat
        if (
            best_cat is not None
            and native_category in positions.IDP_OVERLAP_CATEGORIES
            and best_cat != native_category
        ):
            p["position"] = best_cat
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
    """Agrupa o time e os agentes livres por posição BRUTA/granular, como
    reportada pela plataforma (CB com CB, S com S, LB com LB — nunca
    misturando, mesmo que compartilhem a mesma categoria de ranking do
    FantasyPros) e, dentro de cada grupo, sinaliza o pior jogador do time
    para troca e o(s) melhor(es) agente(s) livre(s) disponíveis, quando a
    diferença de rank for grande o suficiente.

    Importante: esta função faz sua PRÓPRIA consulta aos rankings (a partir
    de `rankings_by_position`) em vez de depender de um `rank` já anotado no
    jogador, porque no pipeline (main.py) ela é chamada antes de
    `attach_ranks` rodar nas mesmas listas. O rank usado em cada comparação
    já considera o melhor valor entre categorias sobrepostas (lb/dl/db),
    igual a `attach_ranks`, então um jogador híbrido é comparado de forma
    justa.

    Retorna (drop_keys, add_info): um set de chaves a sinalizar como "sair" e
    um dict chave -> maior gap encontrado, para sinalizar como "entrar". No
    máximo MAX_ADD_SUGGESTIONS agentes livres são sinalizados por grupo —
    sem esse limite, uma posição com muitos jogadores qualificados (ex: WR)
    podia sinalizar dezenas de nomes de uma vez."""
    lookups = _build_lookups(rankings_by_position)

    groups = {}
    for p in team_players:
        groups.setdefault(p["position"], {"team": [], "fa": []})["team"].append(p)
    for p in free_agents:
        groups.setdefault(p["position"], {"team": [], "fa": []})["fa"].append(p)

    drop_keys = set()
    add_info = {}

    for raw_pos, bucket in groups.items():
        team_ranked = [
            (p, r) for p in bucket["team"] for r in [_resolve_rank(p, lookups)[0]] if r is not None
        ]
        fa_ranked = [
            (p, r) for p in bucket["fa"] for r in [_resolve_rank(p, lookups)[0]] if r is not None
        ]
        if not team_ranked or not fa_ranked:
            continue

        category = positions.ranking_position(raw_pos)
        threshold = config.RANK_GAP_THRESHOLD_OVERRIDES.get(category, config.RANK_GAP_THRESHOLD)

        worst_player, worst_rank = max(team_ranked, key=lambda pr: pr[1])

        qualifying = [
            (fa_player, fa_rank, worst_rank - fa_rank)
            for fa_player, fa_rank in fa_ranked
            if worst_rank - fa_rank >= threshold
        ]
        if not qualifying:
            continue

        # Mantém só os MAX_ADD_SUGGESTIONS de melhor rank (maior gap) por grupo.
        qualifying.sort(key=lambda item: item[1])
        qualifying = qualifying[:MAX_ADD_SUGGESTIONS]

        drop_keys.add(_flag_key(worst_player))
        for fa_player, fa_rank, gap in qualifying:
            key = _flag_key(fa_player)
            prev = add_info.get(key)
            if prev is None or gap > prev:
                add_info[key] = gap

    return drop_keys, add_info
