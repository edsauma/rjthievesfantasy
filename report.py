from datetime import datetime, timezone
import config

STYLE = """
<style>
  :root { color-scheme: light dark; }
  body { font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; max-width: 1000px; margin: 40px auto; padding: 0 16px; line-height: 1.5; }
  h1 { font-size: 1.6rem; margin-bottom: 0; }
  .updated { color: #888; font-size: 0.85rem; margin-bottom: 24px; }
  table { width: 100%; border-collapse: collapse; margin-top: 8px; }
  th, td { text-align: left; padding: 6px 6px; border-bottom: 1px solid #eee; font-size: 0.9rem; }
  th { color: #888; font-weight: 600; font-size: 0.78rem; text-transform: uppercase; }
  .empty { color: #888; font-style: italic; }
  .pos-badge { display:inline-block; background:#eef; border-radius: 6px; padding: 1px 8px; font-size: 0.78rem; font-weight:600; }
  section.block { margin-top: 20px; }
  section.block > h3 { font-size: 1rem; margin-bottom: 4px; border-bottom: 2px solid #eee; padding-bottom: 6px; }
  details { margin: 6px 0; border: 1px solid #eee; border-radius: 8px; padding: 6px 12px; }
  details summary { cursor: pointer; font-weight: 600; padding: 6px 0; }
  .rank-missing { color: #bbb; }
  .arrow-drop { color: #d1242f; font-weight: 700; margin-right: 4px; }
  .arrow-add { color: #1a7f37; font-weight: 700; margin-right: 4px; }

  /* Abas (CSS puro, sem JS) */
  .tabset input[type=radio] { position: absolute; opacity: 0; pointer-events: none; }
  .tab-labels { display: flex; flex-wrap: wrap; gap: 6px; border-bottom: 1px solid #ddd; margin-bottom: 20px; }
  .tab-labels label { cursor: pointer; padding: 8px 16px; border-radius: 8px 8px 0 0; background: #f2f2f2; font-weight: 600; font-size: 0.92rem; }
  .panels > .panel { display: none; }
"""


def _tab_css(n: int) -> str:
    rules = []
    for i in range(n):
        rules.append(f"#tab-{i}:checked ~ .tab-labels label[for='tab-{i}'] {{ background:#1a7f37; color:#fff; }}")
        rules.append(f"#tab-{i}:checked ~ .panels #panel-{i} {{ display:block; }}")
    return "\n".join(rules) + "\n</style>"


def _rank_cell(rank):
    return f"#{rank}" if rank is not None else '<span class="rank-missing">—</span>'


def _my_team_table(players: list[dict]) -> str:
    if not players:
        return '<p class="empty">Não consegui carregar seu elenco (veja os logs da Action).</p>'
    rows = ""
    for p in players:
        arrow = '<span class="arrow-drop" title="Considere trocar: há um agente livre melhor nessa categoria">↓</span>' if p.get("flag") == "drop" else ""
        rows += (f"<tr><td><span class='pos-badge'>{p['position'].upper()}</span></td>"
                 f"<td>{arrow}{p['name']} <small>({p.get('team') or '?'})</small></td>"
                 f"<td>{_rank_cell(p['rank'])}</td></tr>")
    return f"<table><tr><th>Pos</th><th>Jogador</th><th>Rank FantasyPros</th></tr>{rows}</table>"


def _free_agents_block(free_agents: list[dict]) -> str:
    if not free_agents:
        return '<p class="empty">Nenhum agente livre encontrado (ou fonte de dados não retornou nada).</p>'
    by_pos = {}
    order = []
    for p in free_agents:
        if p["position"] not in by_pos:
            order.append(p["position"])
        by_pos.setdefault(p["position"], []).append(p)
    blocks = []
    for pos in order:
        players = by_pos[pos]
        rows = ""
        for p in players:
            gap = p.get("flag_gap")
            title = f' title="Rank {gap} posições melhor que seu pior jogador nessa categoria"' if gap else ""
            arrow = f'<span class="arrow-add"{title}>↑</span>' if p.get("flag") == "add" else ""
            rows += f"<tr><td>{arrow}{p['name']} <small>({p.get('team') or '?'})</small></td><td>{_rank_cell(p['rank'])}</td></tr>"
        blocks.append(f"""
        <details>
          <summary>{pos.upper()} — {len(players)} disponíveis</summary>
          <table><tr><th>Jogador</th><th>Rank FantasyPros</th></tr>{rows}</table>
        </details>""")
    return "".join(blocks)


def _rankings_block(rankings: dict) -> str:
    blocks = []
    for pos, players in sorted(rankings.items()):
        if not players:
            continue
        top = players[: config.RANKINGS_DISPLAY_LIMIT]
        rows = "".join(f"<tr><td>#{p['rank']}</td><td>{p['name']}</td></tr>" for p in top)
        blocks.append(f"""
        <details>
          <summary>{pos.upper()} — top {len(top)} do consenso FantasyPros</summary>
          <table><tr><th>Rank</th><th>Jogador</th></tr>{rows}</table>
        </details>""")
    return "".join(blocks) if blocks else '<p class="empty">Rankings indisponíveis.</p>'


def render(results: list[dict]) -> str:
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

    radios = "".join(
        f'<input type="radio" name="team-tabs" id="tab-{i}"{" checked" if i == 0 else ""}>'
        for i in range(len(results))
    )
    labels = "".join(
        f'<label for="tab-{i}">{team["label"]}</label>' for i, team in enumerate(results)
    )
    panels = ""
    for i, team in enumerate(results):
        panels += f"""
        <div class="panel" id="panel-{i}">
          <h2>{team['label']} <small style="color:#888;font-weight:normal;">({team['platform']})</small></h2>

          <section class="block">
            <h3>👤 Meu time</h3>
            {_my_team_table(team.get('my_team', []))}
          </section>

          <section class="block">
            <h3>🟢 Disponíveis na liga</h3>
            {_free_agents_block(team.get('free_agents', []))}
          </section>

          <section class="block">
            <h3>📊 Rankings FantasyPros (consenso)</h3>
            {_rankings_block(team.get('rankings', {}))}
          </section>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Fantasy Football Dashboard</title>
{STYLE}
{_tab_css(len(results))}
</head>
<body>
  <h1>🏈 Fantasy Football Dashboard</h1>
  <div class="updated">Atualizado automaticamente em {now} · <span class="arrow-drop">↓</span> considere trocar · <span class="arrow-add">↑</span> melhor opção disponível</div>
  <div class="tabset">
    {radios}
    <div class="tab-labels">{labels}</div>
    <div class="panels">{panels}</div>
  </div>
</body>
</html>"""
