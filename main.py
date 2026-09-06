import os
import config
import positions
import lineup_slots
import sleeper, fleaflicker, fantasypros, keeptradecut
from analyzer import compute_flags, attach_ranks, attach_extra_rank, _flag_key
import report


def get_rankings_cache(scoring: str) -> dict:
    """Baixa os rankings do FantasyPros uma vez por posição/escopo e reutiliza
    entre times que usam o mesmo tipo de pontuação (standard/ppr). Inclui
    também os rankings 'coringa' de FLEX (ofensivo) e IDP (defensivo)."""
    cache = {}
    all_positions = config.POSITIONS_OFFENSE + config.POSITIONS_IDP + ["flex", "idp"]
    for pos in all_positions:
        try:
            cache[pos] = fantasypros.get_rankings(pos, scoring)
        except Exception as e:
            print(f"[aviso] falha ao buscar ranking de {pos} ({scoring}): {e}")
            cache[pos] = []
    return cache


def build_team_result(team_cfg: dict, platform: str, platform_key: str,
                       my_team_raw: list, free_agents_raw: list, rankings: dict) -> dict:
    drop_keys, add_info = compute_flags(my_team_raw, free_agents_raw, rankings)

    my_team = attach_ranks(my_team_raw, rankings)
    my_team = attach_extra_rank(my_team, rankings.get("flex", []), "flex_rank")
    my_team = attach_extra_rank(my_team, rankings.get("idp", []), "idp_rank")
    for p in my_team:
        p["flag"] = "drop" if _flag_key(p) in drop_keys else None

    slot_list = team_cfg.get("lineup_slots")  # None = usa o padrão da plataforma
    lineup_sections, bench = lineup_slots.assign_lineup(my_team, platform_key, slot_list)

    free_agents = attach_ranks(free_agents_raw, rankings)
    for p in free_agents:
        key = _flag_key(p)
        p["flag"] = "add" if key in add_info else None
        p["flag_gap"] = add_info.get(key)
    free_agents.sort(key=lambda p: (positions.sort_key(platform_key, p["position"]),
                                     p["rank"] if p["rank"] is not None else 9999))

    # Lista completa (top N por posição), com os que valem a pena sinalizados,
    # excluindo posições escondidas por configuração
    free_agents_visible = [p for p in free_agents if p["position"] not in config.FREE_AGENTS_HIDDEN_POSITIONS]
    fa_limited = []
    seen_per_pos = {}
    for p in free_agents_visible:
        count = seen_per_pos.get(p["position"], 0)
        if count < config.FREE_AGENTS_DISPLAY_LIMIT or p["flag"] == "add":
            fa_limited.append(p)
            seen_per_pos[p["position"]] = count + 1

    return {
        "label": team_cfg["label"],
        "platform": platform,
        "platform_key": platform_key,
        "lineup_sections": lineup_sections,
        "bench": bench,
        "free_agents": fa_limited,
    }


def process_fleaflicker(team_cfg: dict, rankings: dict) -> dict:
    my_team = fleaflicker.get_my_team(team_cfg["league_id"], team_cfg["team_id"])
    raw_positions_list = sorted({p["position"] for p in my_team})
    free_agents = fleaflicker.get_free_agents(team_cfg["league_id"], raw_positions_list)
    print(f"[debug] {team_cfg['label']}: {len(my_team)} jogadores no time, {len(free_agents)} agentes livres encontrados")
    return build_team_result(team_cfg, "Fleaflicker", "fleaflicker", my_team, free_agents, rankings)


def process_sleeper(team_cfg: dict, all_players: dict, rankings: dict) -> dict:
    my_team = sleeper.get_my_team(team_cfg["league_id"], team_cfg["roster_id"], all_players)
    try:
        free_agents = keeptradecut.get_available_players(team_cfg["league_id"])
        fonte = "KeepTradeCut"
    except Exception as e:
        print(f"[aviso] KeepTradeCut falhou para {team_cfg['label']} ({e}); usando fallback da API do Sleeper")
        raw_positions_list = sorted({p["position"] for p in my_team})
        free_agents = sleeper.get_free_agents(team_cfg["league_id"], all_players, raw_positions_list)
        fonte = "Sleeper (fallback)"
    print(f"[debug] {team_cfg['label']}: {len(my_team)} jogadores no time, {len(free_agents)} agentes livres encontrados via {fonte}")
    return build_team_result(team_cfg, "Sleeper", "sleeper", my_team, free_agents, rankings)


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
                "label": team_cfg["label"], "platform": team_cfg["platform"], "platform_key": team_cfg["platform"],
                "lineup_sections": {}, "bench": [], "free_agents": [],
            })

    html = report.render(results)
    os.makedirs(os.path.dirname(config.OUTPUT_HTML), exist_ok=True)
    with open(config.OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Relatório gerado em {config.OUTPUT_HTML}")


if __name__ == "__main__":
    main()
