"""
FantasyPros não tem API pública gratuita de rankings, então continuamos
buscando a própria página — mas de um jeito bem mais robusto que os
seletores CSS da planilha original (que quebravam a cada redesign do site).

As páginas de ranking do FantasyPros embutem os dados da tabela como um
objeto JavaScript (`ecrData`) dentro de um <script> da própria página.
Ler esse JSON é muito mais estável do que seguir `.sticky-cell-one`,
`TD:nth-child(7)` etc., porque sobrevive a mudanças visuais/CSS — só quebra
se a FantasyPros mudar a própria estrutura de dados, o que é raro.

Se por algum motivo o `ecrData` não for encontrado (ex: FantasyPros mudou o
formato), o código cai para um parser de tabela HTML como plano B.
"""
import re
import json
import requests
import pandas as pd
from io import StringIO

BASE = "https://www.fantasypros.com/nfl/rankings"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; fantasy-dashboard/1.0; personal use)"
}

# Mapeia posição -> slug da URL. IDP e K não têm variante PPR.
def _url_for(position: str, scoring: str) -> str:
    position = position.lower()
    if position == "flex":
        # Ranking dedicado pra posição "útil" ofensiva (RB/WR/TE)
        return f"{BASE}/ppr-flex.php" if scoring == "ppr" else f"{BASE}/flex.php"
    if position == "idp":
        # Ranking dedicado pra qualquer jogador defensivo (não varia por PPR)
        return f"{BASE}/idp.php"
    if scoring == "ppr" and position in ("rb", "wr", "te"):
        return f"{BASE}/ppr-{position}.php"
    return f"{BASE}/{position}.php"


def _extract_ecr_json(html: str):
    match = re.search(r"var\s+ecrData\s*=\s*(\{.*?\});", html, re.S)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def _fallback_table_scrape(html: str):
    """Plano B: tenta ler a primeira tabela HTML da página com pandas."""
    try:
        tables = pd.read_html(StringIO(html))
    except ValueError:
        return []
    if not tables:
        return []
    df = tables[0]
    name_col = next((c for c in df.columns if "player" in str(c).lower()), None)
    rank_col = next((c for c in df.columns if str(c).strip().lower() in ("rk", "rank")), None)
    if not name_col or not rank_col:
        return []
    out = []
    for _, row in df.iterrows():
        try:
            out.append({"name": str(row[name_col]), "rank": int(row[rank_col])})
        except (ValueError, TypeError):
            continue
    return out


def get_rankings(position: str, scoring: str = "standard") -> list[dict]:
    """Retorna [{'name': ..., 'rank': int}, ...] ordenado por rank consenso."""
    url = _url_for(position, scoring)
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    html = resp.text

    data = _extract_ecr_json(html)
    if data and "players" in data:
        players = []
        for p in data["players"]:
            name = p.get("player_name")
            rank = p.get("rank_ecr")
            if name and rank is not None:
                players.append({"name": name, "rank": int(rank)})
        if players:
            return sorted(players, key=lambda x: x["rank"])

    # Plano B, se o JSON embutido não for encontrado
    return _fallback_table_scrape(html)
