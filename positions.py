"""
Mapeamento entre posições "reais" (como cada plataforma reporta, mais
granular em ligas com defesa individual/IDP) e a categoria que o
FantasyPros usa pra ranking (mais ampla). Também define a ORDEM de
exibição de cada posição, por plataforma — como pedido, granular no
Fleaflicker (CB, S, EDR, IL separados) e agrupado no Sleeper (DE, LB, DB).
"""

# posição real -> categoria de ranking do FantasyPros
RANKING_MAP = {
    "qb": "qb", "rb": "rb", "wr": "wr", "te": "te", "k": "k",
    "dt": "dl", "dl": "dl", "edr": "dl", "il": "dl",
    # "de" fica de fora de propósito: no Sleeper, jogadores marcados DE não
    # correspondem ao ranking de DL do FantasyPros — ficam sem rank.
    "lb": "lb",
    "cb": "db", "s": "db", "db": "db",
    # "p" (punter) não tem ranking no FantasyPros — fica sem rank, mas aparece na lista
}

DISPLAY_ORDER = {
    "sleeper": ["qb", "rb", "wr", "te", "k", "de", "lb", "db"],
    "fleaflicker": ["qb", "rb", "wr", "te", "k", "p", "cb", "s", "edr", "il", "lb"],
}


def ranking_position(raw_position: str) -> str:
    raw = (raw_position or "").lower()
    return RANKING_MAP.get(raw, raw)


# Mapeamento só pra AGRUPAR a exibição de "Disponíveis na liga" — não mexe
# no ranking usado pra decidir troca (isso é RANKING_MAP, acima). No
# Sleeper, DE e DT contam como DL na hora de listar quem está disponível,
# já que também são escaláveis nesse slot (ver lineup_slots.py).
DISPLAY_GROUP_MAP = {
    "de": "dl",
    "dt": "dl",
}


def display_group(raw_position: str) -> str:
    raw = (raw_position or "").lower()
    return DISPLAY_GROUP_MAP.get(raw, raw)


def sort_key(platform: str, position: str):
    order = DISPLAY_ORDER.get(platform, [])
    position = (position or "").lower()
    try:
        return order.index(position)
    except ValueError:
        return len(order)  # posições não previstas vão pro final, sem quebrar nada
