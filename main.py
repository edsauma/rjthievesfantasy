import os
import config
import positions
import lineup_slots
import sleeper, fleaflicker, fantasypros, keeptradecut
from analyzer import compute_flags, attach_ranks, attach_extra_rank, _flag_key
import report


def get_rankings_cache_all() -> dict:
    """Busca os rankings do FantasyPros uma única vez pra cada posição.
    Posições como QB/K/DL/LB/DB/IDP não têm variação por tipo de pontuação
    (PPR vs padrão) — buscar duas vezes a mesma página (uma pro cache
    'standard' e outra pro 'ppr') só aumenta o risco de uma das duas falhar
    por alguma instabilidade momentânea da FantasyPros, deixando aquele
    cache com o ranking vazio sem necessidade."""
    scoring_independent = ["qb", "k"] + config.POSITIONS_IDP + ["idp"]
    scoring_dependent = ["rb", "wr", "te", "flex"]

    shared = {}
    for pos in scoring_independent:
        try:
            shared[pos] = fantasypros.get_rankings(pos, "standard")
        except Exception as e:
            print(f"[aviso] falha ao buscar ranking de {pos}: {e}")
            shared[pos] = []
    print(f"[debug] rankings compartilhados carregados: {', '.join(f'{p}={len(v)}' for p, v in shared.items())}")

    by_scoring = {}
    for scoring in ("standard", "ppr"):
        cache = dict(shared)
        for pos in scoring_dependent:
            try:
                cache[pos] = fantasypros.get_rankings(pos, scoring)
            except Exception as e:
                print(f"[aviso] falha ao buscar ranking de {pos} ({scoring}): {e}")
                cache[pos] = []
        by_scoring[scoring] = cache
    return by_scoring


def build_team_result(team_cfg: dict, platform: str, platform_key: str,
                       my_team_raw: list, free_agents_raw: list, rankings: dict) -> dict:
    _DEBUG_NAMES = {"myles garrett", "greg rousseau"}
    for p in my_team_raw:
        if p["name"].lower() in _DEBUG_NAMES:
            print(f"[debug-dl] BRUTO (meu time) | {p['name']} | position={p['position']} | "
                  f"ranking_position={p.get('ranking_position')}")
    for p in free_agents_raw:
        if p["name"].lower() in _DEBUG_NAMES:
            print(f"[debug-dl] BRUTO (agente livre) | {p['name']} | position={p['position']} | "
                  f"ranking_position={p.get('ranking_position')}")

    drop_keys, add_info = compute_flags(my_team_raw, free_agents_raw, rankings)

    my_team = attach_ranks(my_team_raw, rankings)
    my_team = attach_extra_rank(my_team, rankings.get("flex", []), "flex_rank")
    my_team = attach_extra_rank(my_team, rankings.get("idp", []), "idp_rank")
    for p in my_team:
        p["flag"] = "drop" if _flag_key(p) in drop_keys else None

    # Debug temporário: rastreando dois jogadores específicos que estavam
    # sumindo em meio a centenas de outros jogadores DL nos logs do Sleeper
    for p in my_team:
        if p["name"].lower() in _DEBUG_NAMES:
            print(f"[debug-dl] MEU TIME | {p['name']} | position={p['position']} | "
                  f"ranking_position={p.get('ranking_position')} | rank={p.get('rank')}")

    slot_list = team_cfg.get("lineup_slots")  # None = usa o padrão da plataforma
    lineup_sections, bench = lineup_slots.assign_lineup(my_team, platform_key, slot_list)
    # assign_lineup marca 'is_starter' em cada jogador de my_team (mutação in-place)

    free_agents = attach_ranks(free_agents_raw, rankings)
    for p in free_agents:
        if p["name"].lower() in _DEBUG_NAMES:
            print(f"[debug-dl] AGENTE LIVRE | {p['name']} | position={p['position']} | "
                  f"ranking_position={p.get('ranking_position')} | rank={p.get('rank')}")
    for p in free_agents:
        key = _flag_key(p)
        p["flag"] = "add" if key in add_info else None
        p["flag_gap"] = add_info.get(key)
    for p in free_agents:
        if len(p.get("position_options") or []) > 1:
            print(f"[debug-dual] {p['name']} | position={p['position']} | "
                  f"position_options={p.get('position_options')} | flag={p.get('flag')}")
    free_agents.sort(key=lambda p: (positions.sort_key(platform_key, positions.display_group(p["position"])),
                                     p["rank"] if p["rank"] is not None else 9999))

    # Lista completa (top N por GRUPO de exibição — DE/DT contam junto com
    # DL, não separado), com os que valem a pena sinalizados, excluindo
    # posições escondidas por configuração (específico por plataforma)
    hidden = config.FREE_AGENTS_HIDDEN_POSITIONS.get(platform_key, set())
    free_agents_visible = [p for p in free_agents if p["position"] not in hidden]
    fa_limited = []
    seen_per_pos = {}
    for p in free_agents_visible:
        group = positions.display_group(p["position"])
        count = seen_per_pos.get(group, 0)
        if count < config.FREE_AGENTS_DISPLAY_LIMIT or p["flag"] == "add":
            fa_limited.append(p)
            seen_per_pos[group] = count + 1

    for p in fa_limited:
        if len(p.get("position_options") or []) > 1:
            print(f"[debug-dual] SOBREVIVEU AO LIMITE | {p['name']} | position_options={p.get('position_options')}")

    return {
        "label": team_cfg["label"],
        "platform": platform,
        "platform_key": platform_key,
        "my_team": my_team,
        "free_agents": fa_limited,
    }


def process_fleaflicker(team_cfg: dict, rankings: dict) -> dict:
    my_team = fleaflicker.get_my_team(team_cfg["league_id"], team_cfg["team_id"])
    raw_positions_list = sorted({p["position"] for p in my_team})
    free_agents = fleaflicker.get_free_agents(team_cfg["league_id"], raw_positions_list)
    print(f"[debug] {team_cfg['label']}: {len(my_team)} jogadores no time, {len(free_agents)} agentes livres encontrados")
    return build_team_result(team_cfg, "Fleaflicker", "fleaflicker", my_team, free_agents, rankings)


KTC_POSITIONS = {"qb", "rb", "wr", "te"}  # K não tem valor de troca dynasty -> KTC não rastreia


def process_sleeper(team_cfg: dict, all_players: dict, rankings: dict) -> dict:
    my_team = sleeper.get_my_team(team_cfg["league_id"], team_cfg["roster_id"], all_players)
    raw_positions = {p["position"] for p in my_team}
    ktc_raw = sorted(raw_positions & KTC_POSITIONS)
    direct_raw = sorted(raw_positions - KTC_POSITIONS)  # inclui K e todos os defensivos

    free_agents = []
    fontes = []

    # KeepTradeCut só cobre QB/RB/WR/TE (não tem K nem defensivos individuais
    # no banco de dados dele) — usamos ele aqui pela vantagem de refletir
    # posse real mesmo quando o sync de rookies do Sleeper está atrasado.
    try:
        ktc_agents = keeptradecut.get_available_players(team_cfg["league_id"])
        free_agents += [p for p in ktc_agents if p["position"] in KTC_POSITIONS]
        fontes.append("KeepTradeCut (QB/RB/WR/TE)")
    except Exception as e:
        print(f"[aviso] KeepTradeCut falhou para {team_cfg['label']} ({e}); usando fallback da API do Sleeper")
        free_agents += sleeper.get_free_agents(team_cfg["league_id"], all_players, ktc_raw)
        fontes.append("Sleeper fallback (QB/RB/WR/TE)")

    # K e defensivos sempre vêm direto da API do Sleeper
    if direct_raw:
        free_agents += sleeper.get_free_agents(team_cfg["league_id"], all_players, direct_raw)
        fontes.append("Sleeper (K + defesa)")

    print(f"[debug] {team_cfg['label']}: {len(my_team)} jogadores no time, {len(free_agents)} agentes livres encontrados via {' + '.join(fontes)}")
    return build_team_result(team_cfg, "Sleeper", "sleeper", my_team, free_agents, rankings)


def main():
    rankings_by_scoring = get_rankings_cache_all()

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
                "my_team": [], "free_agents": [],
            })

    html = report.render(results)
    os.makedirs(os.path.dirname(config.OUTPUT_HTML), exist_ok=True)
    with open(config.OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Relatório gerado em {config.OUTPUT_HTML}")


if __name__ == "__main__":
    main()
