"""
Define a configuração real de time titular de cada plataforma (incluindo
posições "úteis"/flex, tipo RB/WR/TE) e distribui os jogadores do seu
elenco nesses slots — o resto vira banco.

A distribuição é gulosa (greedy): para cada slot, na ordem definida,
escolhe o melhor jogador ainda disponível (menor rank do FantasyPros)
entre os elegíveis pra aquele slot. Não é uma otimização perfeita de
escalação, mas reflete bem como a maioria monta o time na prática.
"""
from collections import OrderedDict

SLOT_CONFIG = {
    "sleeper": [
        "QB", "RB", "RB", "WR", "WR", "TE", "RB/WR/TE", "RB/WR/TE", "K",
        "DL", "DL", "LB", "LB", "DB", "DB", "IDP", "IDP",
    ],
    "fleaflicker": [
        "QB", "RB", "RB", "RB/WR/TE", "WR", "WR", "TE", "K",
        "CB", "S", "CB/S", "EDR", "EDR", "IL", "LB", "LB", "S/CB/EDR/IL/LB",
    ],
}

# No Sleeper, os códigos de defesa já vêm agrupados (DL/LB/DB), então o
# "IDP" (qualquer defensivo) cobre essas três categorias.
_SLEEPER_IDP = {"dl", "lb", "db"}


def _eligible_positions(slot_label: str) -> set:
    if slot_label == "IDP":
        return set(_SLEEPER_IDP)
    return {p.lower() for p in slot_label.split("/")}


def assign_lineup(players: list[dict], platform_key: str):
    """Retorna (sections, bench):
    - sections: OrderedDict {slot_label: [jogadores]} na ordem da escalação
    - bench: lista de quem sobrou, ordenada por posição e rank
    """
    slots = SLOT_CONFIG.get(platform_key, [])
    pool = list(players)
    assigned = set()
    sections = OrderedDict()

    for slot_label in slots:
        elig = _eligible_positions(slot_label)
        candidates = [p for p in pool if p["position"] in elig and id(p) not in assigned]
        candidates.sort(key=lambda p: p["rank"] if p["rank"] is not None else 9999)
        sections.setdefault(slot_label, [])
        if candidates:
            chosen = candidates[0]
            assigned.add(id(chosen))
            sections[slot_label].append(chosen)

    bench = [p for p in pool if id(p) not in assigned]
    bench.sort(key=lambda p: (p["position"], p["rank"] if p["rank"] is not None else 9999))
    return sections, bench
