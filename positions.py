# Mapeamento de posições: cada plataforma reporta posições de um jeito
# (Fleaflicker é granular: CB, S, EDR, IL, LB; Sleeper é mais genérico:
# DE, DT, DL, LB, DB), mas o ranking do FantasyPros usa categorias próprias
# (qb, rb, wr, te, k, lb, dl, db, além de flex e idp combinados).

# Posição "bruta" (como vem da plataforma) -> categoria de ranking do FantasyPros
RANKING_MAP = {
    "qb": "qb",
    "rb": "rb",
    "wr": "wr",
    "te": "te",
    "k": "k",
    # Fleaflicker (granular)
    "cb": "db",
    "s": "db",
    "edr": "dl",
    "il": "lb",
    "lb": "lb",
    # Sleeper (mais genérico) — DE e DT contam como DL tanto para escalação
    # quanto para o ranking do FantasyPros.
    "de": "dl",
    "dt": "dl",
    "dl": "dl",
    "db": "db",
}

# Categorias de ranking do FantasyPros que podem se sobrepor para o mesmo
# jogador. Um defensor "híbrido" (ex: edge rusher que também joga de LB)
# pode aparecer nos rankings de mais de uma dessas categorias ao mesmo tempo
# (ex: Dallas Turner aparece tanto no ranking de LB quanto no de DL). Nesses
# casos, usamos o melhor (menor) rank entre todas as categorias do grupo.
IDP_OVERLAP_CATEGORIES = {"lb", "dl", "db"}


def ranking_position(raw_position):
    """Retorna a categoria de ranking do FantasyPros para uma posição bruta."""
    if raw_position is None:
        return None
    return RANKING_MAP.get(raw_position.lower())


def overlap_categories(category):
    """Dado uma categoria de ranking, retorna o conjunto de categorias que
    devem ser consultadas para achar o melhor rank do jogador. Para as
    categorias defensivas (lb/dl/db) isso inclui as três, já que o mesmo
    jogador pode estar listado em mais de uma. Para as demais, é só ela
    mesma."""
    if category in IDP_OVERLAP_CATEGORIES:
        return IDP_OVERLAP_CATEGORIES
    return {category}


# Fusão apenas para exibição/contagem (não afeta o ranking em si): no
# Sleeper, DE e DT aparecem agrupados junto com DL.
DISPLAY_GROUP_MAP = {"de": "dl", "dt": "dl"}


def display_group(raw_position):
    if raw_position is None:
        return raw_position
    return DISPLAY_GROUP_MAP.get(raw_position.lower(), raw_position.lower())


DISPLAY_ORDER = {
    "sleeper": ["qb", "rb", "wr", "te", "k", "dl", "lb", "db"],
    # "dl" foi incluído aqui também: um jogador do Fleaflicker cadastrado como
    # CB/S/EDR/IL/LB pode, por conta de um rank melhor em outra categoria do
    # FantasyPros (ver IDP_OVERLAP_CATEGORIES em analyzer.py), acabar exibido
    # agrupado como "DL" mesmo nessa plataforma.
    "fleaflicker": ["qb", "rb", "wr", "te", "k", "p", "cb", "s", "dl", "edr", "il", "lb"],
}


def sort_key(platform_key, group):
    order = DISPLAY_ORDER.get(platform_key, [])
    try:
        return order.index(group)
    except ValueError:
        return len(order)
