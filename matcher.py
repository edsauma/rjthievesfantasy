import re
import unicodedata

SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}


def normalize_name(name):
    """Remove acentos, pontuação e sufixos (Jr., Sr., II...) para comparar
    nomes de jogadores vindos de fontes diferentes de forma confiável."""
    if not name:
        return ""
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    name = name.lower()
    name = re.sub(r"[^a-z0-9\s]", " ", name)
    tokens = [t for t in name.split() if t and t not in SUFFIXES]
    return " ".join(tokens)


def build_lookup(ranking_list):
    """Monta um dict nome-normalizado -> rank a partir de uma lista de
    rankings do FantasyPros. Se o mesmo nome aparecer mais de uma vez na
    mesma lista, mantém o melhor (menor) rank."""
    lookup = {}
    for entry in ranking_list or []:
        raw_name = entry.get("player_name") or entry.get("name") or ""
        name = normalize_name(raw_name)
        rank = entry.get("rank_ecr")
        if rank is None:
            rank = entry.get("rank")
        if name and rank is not None:
            if name not in lookup or rank < lookup[name]:
                lookup[name] = rank
    return lookup


def find_rank(name, lookup):
    return lookup.get(normalize_name(name))
