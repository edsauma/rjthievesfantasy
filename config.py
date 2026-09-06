"""
Configuração central do dashboard.

Preencha aqui os dados das suas 4 equipes (extraídos da planilha original).
Se algum ID estiver errado ou uma liga tiver saído do ar, é só ajustar aqui —
o resto do código não precisa mudar.
"""

TEAMS = [
    # ⚠️ Ligas Sleeper: o league_id muda a cada temporada (confira em
    # setembro/outubro, início da nova season, na URL da sua liga no app).
    # roster_id costuma se manter, mas vale conferir também se algo parecer errado.
    {
        "label": "ErreJota",
        "platform": "fleaflicker",
        "league_id": "209547",
        # ID do seu time dentro da liga Fleaflicker (visto na URL /teams/<id>)
        "team_id": "1387088",
        "scoring": "standard",  # "standard" ou "ppr" -> define quais rankings do FantasyPros usar
        # Essa liga tem um slot titular de Punter (P) que a Quevedo não tem —
        # por isso a escalação é customizada aqui em vez de usar o padrão do Fleaflicker.
        "lineup_slots": [
            "QB", "RB", "RB", "RB/WR/TE", "WR", "WR", "TE", "K", "P",
            "CB", "S", "CB/S", "EDR", "EDR", "IL", "LB", "LB", "S/CB/EDR/IL/LB",
        ],
    },
    {
        "label": "Quevedo",
        "platform": "fleaflicker",
        "league_id": "311068",
        "team_id": "1567528",
        "scoring": "standard",
    },
    {
        "label": "Super Bowlo",
        "platform": "sleeper",
        "league_id": "1361761930972266496",
        "roster_id": "9",
        "scoring": "ppr",
    },
    {
        "label": "Camisa",
        "platform": "sleeper",
        "league_id": "1360280713642905600",
        "roster_id": "12",
        "scoring": "ppr",
    },
]

# Posições padrão de ataque + IDP que a planilha original acompanhava
POSITIONS_OFFENSE = ["qb", "rb", "wr", "te", "k"]
POSITIONS_IDP = ["lb", "dl", "db"]  # FantasyPros usa esses códigos para defesa individual

# Quantos "slots piores" um jogador precisa estar atrás de um agente livre
# para virar sugestão de troca/waiver (ajuste conforme sua tolerância)
RANK_GAP_THRESHOLD = 8

# Limites de exibição no dashboard (só afeta o que é MOSTRADO, não a lógica
# de sugestão, que sempre olha a lista inteira)
FREE_AGENTS_DISPLAY_LIMIT = 15   # top N agentes livres por posição, por liga

# Posições que nunca aparecem na seção "Disponíveis na liga", mesmo que haja
# alguém valendo a pena (ajuste essa lista conforme sua preferência)
FREE_AGENTS_HIDDEN_POSITIONS = {"db", "edr", "il", "wr", "cb"}

OUTPUT_HTML = "docs/index.html"  # pasta "docs" é o padrão pro GitHub Pages
CACHE_DIR = "data"
