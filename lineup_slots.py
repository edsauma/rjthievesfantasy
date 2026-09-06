"""
Define a configuração real de time titular de cada plataforma (incluindo
posições "úteis"/flex, tipo RB/WR/TE) e distribui os jogadores do seu
elenco nesses slots — o resto vira banco.

A distribuição é gulosa (greedy): para cada slot, na ordem definida,
escolhe o melhor jogador ainda disponível entre os elegíveis pra aquele
slot. Para slots de posição única, usa o rank individual do FantasyPros
(campo 'rank'). Para slots "úteis" (flex), usa o ranking dedicado do
FantasyPros pra essa função: 'flex_rank' pros slots ofensivos (RB/WR/TE)
e 'idp_rank' pros slots defensivos combinados — que é mais correto do que
comparar ranks individuais de posições diferentes entre si.
"""
from collections import OrderedDict
import positions

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
_OFFENSE_FLEX = {"rb", "wr", "te"}


def _eligible_positions(slot_label: str) -> set:
    if slot_label == "IDP":
        return set(_SLEEPER_IDP)
    return {p.lower() for p in slot_label.split("/")}


def _slot_kind(slot_label: str, elig: set) -> str:
    """'single' = posição única (usa 'rank' individual);
    'flex' = útil ofensivo (usa 'flex_rank');
    'idp' = útil defensivo (usa 'idp_rank')."""
    if slot_label == "IDP":
        return "idp"
    if len(elig) > 1:
        return "flex" if elig <= _OFFENSE_FLEX else "idp"
    return "single"


def _rank_for_sort(p: dict, kind: str):
    if kind == "flex" and p.get("flex_rank") is not None:
        return p["flex_rank"]
    if kind == "idp" and p.get("idp_rank") is not None:
        return p["idp_rank"]
    return p["rank"] if p.get("rank") is not None else 9999


def assign_lineup(players: list[dict], platform_key: str, slot_list: list = None):
    """Retorna (sections, bench):
    - sections: OrderedDict {slot_label: [jogadores]} na ordem da escalação
    - bench: lista de quem sobrou, ordenada pela MESMA ordem de posições
      usada nos titulares (sem considerar flex — é só o rank individual)
    """
    slots = slot_list or SLOT_CONFIG.get(platform_key, [])
    pool = list(players)
    assigned = set()
    sections = OrderedDict()

    for slot_label in slots:
        elig = _eligible_positions(slot_label)
        kind = _slot_kind(slot_label, elig)
        candidates = [p for p in pool if p["position"] in elig and id(p) not in assigned]
        candidates.sort(key=lambda p: _rank_for_sort(p, kind))
        sections.setdefault(slot_label, [])
        if candidates:
            chosen = candidates[0]
            assigned.add(id(chosen))
            sections[slot_label].append(chosen)

    bench = [p for p in pool if id(p) not in assigned]
    bench.sort(key=lambda p: (positions.sort_key(platform_key, p["position"]),
                               p["rank"] if p.get("rank") is not None else 9999))
    return sections, bench
