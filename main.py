import os
import config
from clients import sleeper, fleaflicker, fantasypros
from analyzer import analyze_team
import report


def get_rankings_cache(scoring: str) -> dict:
    """Baixa os rankings do FantasyPros uma vez por posição/escopo e reutiliza
    entre times que usam o mesmo tipo de pontuação (standard/ppr)."""
    cache = {}
    for pos in config.POSITIONS_OFFENSE + config.POSITIONS_IDP:
        try:
            cache[pos] = fantasypros.get_rankings(pos, scoring)
        except Exception as e:
            print(f"[aviso] falha ao buscar ranking de {pos} ({scoring}): {e}")
            cache[pos] = []
    return cache


def process_fleaflicker(team_cfg: dict, rankings: dict) -> dict:
    my_team = fleaflicker.get_my_team(team_cfg["league_id"], team_cfg["team_id"])
    positions = sorted({p["position"] for p in my_team})
    free_agents = fleaflicker.get_free_agents(team_cfg["league_id"], positions)
    suggestions = analyze_team(my_team, free_agents, rankings)
    return {"label": team_cfg["label"], "platform": "Fleaflicker", "suggestions": suggestions}


def process_sleeper(team_cfg: dict, all_players: dict, rankings: dict) -> dict:
    my_team = sleeper.get_my_team(team_cfg["league_id"], team_cfg["roster_id"], all_players)
    positions = sorted({p["position"] for p in my_team})
    free_agents = sleeper.get_free_agents(team_cfg["league_id"], all_players, positions)
    suggestions = analyze_team(my_team, free_agents, rankings)
    return {"label": team_cfg["label"], "platform": "Sleeper", "suggestions": suggestions}


def main():
    rankings_by_scoring = {
        "standard": get_rankings_cache("standard"),
        "ppr": get_rankings_cache("ppr"),
    }

    sleeper_players_cache = None
    results = []

    for team_cfg in config.TEAMS:
        rankings = rankings_by_scoring[team_cfg["scoring"]]
        try:
            if team_cfg["platform"] == "fleaflicker":
                results.append(process_fleaflicker(team_cfg, rankings))
            elif team_cfg["platform"] == "sleeper":
                if sleeper_players_cache is None:
                    sleeper_players_cache = sleeper.get_all_players()
                results.append(process_sleeper(team_cfg, sleeper_players_cache, rankings))
        except Exception as e:
            print(f"[erro] time {team_cfg['label']}: {e}")
            results.append({"label": team_cfg["label"], "platform": team_cfg["platform"], "suggestions": []})

    html = report.render(results)
    os.makedirs(os.path.dirname(config.OUTPUT_HTML), exist_ok=True)
    with open(config.OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Relatório gerado em {config.OUTPUT_HTML}")


if __name__ == "__main__":
    main()
