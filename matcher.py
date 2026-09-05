"""
O maior desafio de cruzar Sleeper + Fleaflicker + FantasyPros é que cada um
escreve o nome do jogador de um jeito (com/sem sufixo Jr./II, acentos, etc).
Este módulo normaliza os nomes para permitir comparação confiável,
substituindo o que antes era feito manualmente com CONCAT/ReplaceValue na planilha.
"""
import re
import unicodedata

SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}


def normalize_name(name: str) -> str:
    if not name:
        return ""
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = name.lower()
    name = re.sub(r"[^a-z0-9\s]", "", name)
    parts = [p for p in name.split() if p not in SUFFIXES]
    return " ".join(parts).strip()


def build_lookup(players: list[dict]) -> dict:
    """Recebe uma lista de dicts com pelo menos {'name': ..., ...} e devolve
    um dict {nome_normalizado: registro} para lookup O(1)."""
    lookup = {}
    for p in players:
        key = normalize_name(p.get("name", ""))
        if key:
            lookup[key] = p
    return lookup


def find_rank(player_name: str, ranking_lookup: dict):
    """Procura o rank de um jogador dentro de um lookup de rankings do FantasyPros."""
    key = normalize_name(player_name)
    match = ranking_lookup.get(key)
    return match["rank"] if match else None
