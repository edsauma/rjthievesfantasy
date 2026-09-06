import os
import config
import sleeper, fleaflicker, fantasypros
from analyzer import analyze_team, attach_ranks
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


def build_team_result(label: str, platform: str, my_team_raw: list, free_agents_raw: list, rankings: dict) -> dict:
    suggestions = analyze_team(my_team_raw, free_agents_raw, rankings)
    my_team = attach_ranks(my_team_raw, rankings)
    free_agents = attach_ranks(free_agents_raw, rankings)

    fa_limited = []
    seen_per_pos = {}
    for p in free_agents:
        count = seen_per_pos.get(p["position"], 0)
        if count < config.FREE_AGENTS_DISPLAY_LIMIT:
            fa_limited.append(p)
            seen_per_pos[p["position"]] = count + 1

    return {
        "label": label,
        "platform": platform,
        "my_team": my_team,
        "free_agents": fa_limited,
        "rankings": rankings,
        "suggestions": suggestions,
    }


def process_fleaflicker(team_cfg: dict, rankings: dict) -> dict:
    my_team = fleaflicker.get_my_team(team_cfg["league_id"], team_cfg["team_id"])
    positions = sorted({p["position"] for p in my_team})
    free_agents = fleaflicker.get_free_agents(team_cfg["league_id"], positions)
    print(f"[debug] {team_cfg['label']}: {len(my_team)} jogadores no time, {len(free_agents)} agentes livres encontrados")
    return build_team_result(team_cfg["label"], "Fleaflicker", my_team, free_agents, rankings)


def process_sleeper(team_cfg: dict, all_players: dict, rankings: dict) -> dict:
    my_team = sleeper.get_my_team(team_cfg["league_id"], team_cfg["roster_id"], all_players)
    positions = sorted({p["position"] for p in my_team})
    free_agents = sleeper.get_free_agents(team_cfg["league_id"], all_players, positions)
    print(f"[debug] {team_cfg['label']}: {len(my_team)} jogadores no time, {len(free_agents)} agentes livres encontrados")
    return build_team_result(team_cfg["label"], "Sleeper", my_team, free_agents, rankings)


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
            results.append({
                "label": team_cfg["label"], "platform": team_cfg["platform"],
                "my_team": [], "free_agents": [], "rankings": {}, "suggestions": [],
            })

    html = report.render(results)
    os.makedirs(os.path.dirname(config.OUTPUT_HTML), exist_ok=True)
    with open(config.OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Relatório gerado em {config.OUTPUT_HTML}")


if __name__ == "__main__":
    main()
