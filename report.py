from datetime import datetime, timezone
import config

STYLE = """
<style>
  :root { color-scheme: light dark; }
  body { font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; max-width: 1000px; margin: 40px auto; padding: 0 16px; line-height: 1.5; }
  h1 { font-size: 1.6rem; margin-bottom: 0; }
  .updated { color: #888; font-size: 0.85rem; margin-bottom: 32px; }
  .team { border: 1px solid #ddd; border-radius: 10px; padding: 20px 24px; margin-bottom: 32px; }
  .team h2 { margin-top: 0; font-size: 1.3rem; }
  .platform { color: #888; font-weight: normal; font-size: 0.85rem; }
  table { width: 100%; border-collapse: collapse; margin-top: 8px; }
  th, td { text-align: left; padding: 6px 6px; border-bottom: 1px solid #eee; font-size: 0.9rem; }
  th { color: #888; font-weight: 600; font-size: 0.78rem; text-transform: uppercase; }
  .gap { font-weight: 600; color: #1a7f37; }
  .empty { color: #888; font-style: italic; }
  .pos-badge { display:inline-block; background:#eef; border-radius: 6px; padding: 1px 8px; font-size: 0.78rem; font-weight:600; }
  section.block { margin-top: 20px; }
  section.block > h3 { font-size: 1rem; margin-bottom: 4px; border-bottom: 2px solid #eee; padding-bottom: 6px; }
  details { margin: 6px 0; border: 1px solid #eee; border-radius: 8px; padding: 6px 12px; }
  details summary { cursor: pointer; font-weight: 600; padding: 6px 0; }
  .rank-missing { color: #bbb; }
  .highlight-suggestions { background: #fffbe6; border-color: #f0d868; }
</style>
"""


def _rank_cell(rank):
    return f"#{rank}" if rank is not None else '<span class="rank-missing">—</span>'


def _my_team_table(players: list[dict]) -> str:
    if not players:
        return '<p class="empty">Não consegui carregar seu elenco (veja os logs da Action).</p>'
    rows = "".join(
        f"<tr><td><span class='pos-badge'>{p['position'].upper()}</span></td>"
        f"<td>{p['name']} <small>({p.get('team') or '?'})</small></td>"
        f"<td>{_rank_cell(p['rank'])}</td></tr>"
        for p in players
    )
    return f"<table><tr><th>Pos</th><th>Jogador</th><th>Rank FantasyPros</th></tr>{rows}</table>"


def _free_agents_block(free_agents: list[dict]) -> str:
    if not free_agents:
        return '<p class="empty">Nenhum agente livre encontrado (ou API não retornou dados).</p>'
    by_pos = {}
    for p in free_agents:
        by_pos.setdefault(p["position"], []).append(p)
    blocks = []
    for pos, players in sorted(by_pos.items()):
        rows = "".join(
            f"<tr><td>{p['name']} <small>({p.get('team') or '?'})</small></td><td>{_rank_cell(p['rank'])}</td></tr>"
            for p in players
        )
        blocks.append(f"""
        <details>
          <summary>{pos.upper()} — top {len(players)} disponíveis</summary>
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


def _suggestions_block(suggestions: list[dict]) -> str:
    if not suggestions:
        return '<p class="empty">Nenhuma sugestão hoje — seu elenco está bem posicionado nessa liga.</p>'
    rows = "".join(f"""
        <tr>
          <td><span class="pos-badge">{s['position']}</span></td>
          <td>{s['drop']} <small>(#{s['drop_rank']})</small></td>
          <td>→ {s['add']} <small>(#{s['add_rank']})</small></td>
          <td class="gap">+{s['gap']} posições</td>
        </tr>""" for s in suggestions)
    return f"""<table><tr><th>Posição</th><th>Trocar</th><th>Por</th><th>Ganho</th></tr>{rows}</table>"""


def render(results: list[dict]) -> str:
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    sections = []
    for team in results:
        sections.append(f"""
        <div class="team">
          <h2>{team['label']} <span class="platform">({team['platform']})</span></h2>

          <section class="block highlight-suggestions">
            <h3>🔁 Sugestões de troca</h3>
            {_suggestions_block(team.get('suggestions', []))}
          </section>

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
        </div>""")

    return f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Fantasy Football Dashboard</title>
{STYLE}
</head>
<body>
  <h1>🏈 Fantasy Football Dashboard</h1>
  <div class="updated">Atualizado automaticamente em {now}</div>
  {''.join(sections)}
</body>
</html>"""
