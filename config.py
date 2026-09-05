"""
Configuração central do dashboard.

Preencha aqui os dados das suas 4 equipes (extraídos da planilha original).
Se algum ID estiver errado ou uma liga tiver saído do ar, é só ajustar aqui —
o resto do código não precisa mudar.
"""

TEAMS = [
    {
        "label": "ErreJota",
        "platform": "fleaflicker",
        "league_id": "209547",
        # ID do seu time dentro da liga Fleaflicker (visto na URL /teams/<id>)
        "team_id": "1387088",
        "scoring": "standard",  # "standard" ou "ppr" -> define quais rankings do FantasyPros usar
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
        "league_id": "1221938019913695232",
        "roster_id": "9",
        "scoring": "ppr",
    },
    {
        "label": "Camisa",
        "platform": "sleeper",
        "league_id": "1186839568296685568",
        "roster_id": "12",
        "scoring": "ppr",
    },
]

# Posições padrão de ataque + IDP que a planilha original acompanhava
POSITIONS_OFFENSE = ["qb", "rb", "wr", "te", "k"]
POSITIONS_IDP = ["lb", "dl", "db"]  # FantasyPros usa esses códigos para defesa individual

# Quantos "slots piores" um jogador precisa estar atrás de um agente livre
# para virar sugestão de troca/waiver (ajuste conforme sua tolerância)
RANK_GAP_THRESHOLD = 1

OUTPUT_HTML = "docs/index.html"  # pasta "docs" é o padrão pro GitHub Pages
CACHE_DIR = "data"
