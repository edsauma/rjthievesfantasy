from datetime import datetime
from zoneinfo import ZoneInfo
import config
import positions

STYLE = """
<style>
  :root { color-scheme: light dark; }
  body { font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; max-width: 1200px; margin: 40px auto; padding: 0 16px; line-height: 1.5; }
  h1 { font-size: 1.6rem; margin-bottom: 0; }
  .updated { color: #888; font-size: 0.85rem; margin-bottom: 24px; }
  table { width: 100%; border-collapse: collapse; margin-top: 4px; }
  th, td { text-align: left; padding: 6px 6px; border-bottom: 1px solid #eee; font-size: 0.9rem; }
  th { color: #888; font-weight: 600; font-size: 0.76rem; text-transform: uppercase; }
  .empty { color: #888; font-style: italic; }
  .pos-badge { display:inline-block; background:#eef; border-radius: 6px; padding: 1px 8px; font-size: 0.76rem; font-weight:600; white-space:nowrap; }
  .pos-badge-drop { display:inline-block; background:#d1242f; color:#fff; border-radius: 6px; padding: 1px 8px; font-size: 0.76rem; font-weight:700; white-space:nowrap; }
  .reserve-marker { color:#bbb; margin-right:4px; }

  /* Reservas como subgrupo expansível (CSS puro) */
  details.reserves-toggle { border: none; padding: 0; margin: 0; }
  details.reserves-toggle summary { list-style: none; cursor: pointer; padding: 4px 0; color: #888; font-size: 0.82rem; }
  details.reserves-toggle summary::-webkit-details-marker { display: none; }
  details.reserves-toggle summary::before { content: "▸ "; }
  details.reserves-toggle[open] summary::before { content: "▾ "; }
  details.reserves-toggle table { margin-top: 0; }
  section.block { margin-top: 20px; }
  section.block > h3 { font-size: 1rem; margin-bottom: 4px; border-bottom: 2px solid #eee; padding-bottom: 6px; }
  details { margin: 6px 0; border: 1px solid #eee; border-radius: 8px; padding: 6px 12px; }
  details summary { cursor: pointer; font-weight: 600; padding: 6px 0; }
  .rank-missing { color: #bbb; }

  /* Sinalização de troca — bem visível: badge sólida + linha destacada */
  .flag-badge { display:inline-flex; align-items:center; justify-content:center; font-weight:900; font-size: 1rem; width: 22px; height: 22px; border-radius: 999px; margin-right: 7px; }
  .flag-drop-badge { background:#d1242f; color:#fff; }
  .flag-add-badge { background:#1a7f37; color:#fff; }
  tr.flag-row-drop { background: #fff0ef; }
  tr.flag-row-add { background: #edfff2; }
  tr.flag-row-drop td, tr.flag-row-add td { font-weight: 600; }

  /* Duas colunas lado a lado (empilha em telas estreitas) */
  .side-by-side { display: grid; grid-template-columns: 1fr 1fr; gap: 28px; align-items: start; }
  @media (max-width: 760px) { .side-by-side { grid-template-columns: 1fr; } }

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


def _player_row(p, extra_pos_cell=None):
    flag = p.get("flag")
    row_class = f' class="flag-row-{flag}"' if flag else ""
    badge = ""
    if flag == "drop":
        badge = '<span class="flag-badge flag-drop-badge" title="Há um agente livre bem melhor nessa categoria">↓</span>'
    elif flag == "add":
        gap = p.get("flag_gap")
        title = f' title="Rank {gap} posições melhor que seu pior jogador nessa categoria"' if gap else ""
        badge = f'<span class="flag-badge flag-add-badge"{title}>↑</span>'
    pos_cell = f"<td>{extra_pos_cell}</td>" if extra_pos_cell is not None else ""
    return (f"<tr{row_class}>{pos_cell}"
            f"<td>{badge}{p['name']} <small>({p.get('team') or '?'})</small></td>"
            f"<td>{_rank_cell(p['rank'])}</td></tr>")


def _my_team_table(my_team: list[dict], platform_key: str) -> str:
    if not my_team:
        return '<p class="empty">Não consegui carregar seu elenco (veja os logs da Action).</p>'

    by_pos = {}
    for p in my_team:
        by_pos.setdefault(p["position"], []).append(p)
    ordered_positions = sorted(by_pos.keys(), key=lambda pos: positions.sort_key(platform_key, pos))

    rows = ""
    for pos in ordered_positions:
        players = by_pos[pos]
        starters = sorted([p for p in players if p.get("is_starter")],
                           key=lambda p: p["rank"] if p.get("rank") is not None else 9999)
        reserves = sorted([p for p in players if not p.get("is_starter")],
                           key=lambda p: p["rank"] if p.get("rank") is not None else 9999)

        has_drop = any(p.get("flag") == "drop" for p in players)
        badge_class = "pos-badge-drop" if has_drop else "pos-badge"
        pos_label = f"<span class='{badge_class}'>{pos.upper()}</span>"

        if starters:
            for i, p in enumerate(starters):
                rows += _player_row(p, extra_pos_cell=pos_label if i == 0 else "")
        else:
            rows += f"<tr><td>{pos_label}</td><td class='empty' colspan='2'>vazio</td></tr>"

        if reserves:
            reserve_rows = "".join(_player_row(p) for p in reserves)
            rows += f"""
            <tr><td colspan="3" style="padding:2px 0;border-bottom:none;">
              <details class="reserves-toggle">
                <summary>{len(reserves)} no banco</summary>
                <table>{reserve_rows}</table>
              </details>
            </td></tr>"""

    return f"<table><tr><th>Pos</th><th>Jogador</th><th>Rank</th></tr>{rows}</table>"


def _free_agents_block(free_agents: list[dict]) -> str:
    if not free_agents:
        return '<p class="empty">Nenhum agente livre encontrado (ou fonte de dados não retornou nada).</p>'
    by_pos = {}
    order = []
    for p in free_agents:
        group = positions.display_group(p["position"])
        if group not in by_pos:
            order.append(group)
        by_pos.setdefault(group, []).append(p)
    blocks = []
    for group in order:
        players = by_pos[group]
        players.sort(key=lambda p: p["rank"] if p["rank"] is not None else 9999)
        rows = "".join(_player_row(p) for p in players)
        blocks.append(f"""
        <details>
          <summary>{group.upper()} — {len(players)} disponíveis</summary>
          <table><tr><th>Jogador</th><th>Rank</th></tr>{rows}</table>
        </details>""")
    return "".join(blocks)



def render(results: list[dict]) -> str:
    now = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M") + " BRT"

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

          <div class="side-by-side">
            <section class="block">
              <h3>👤 Meu time</h3>
              {_my_team_table(team.get('my_team', []), team.get('platform_key', ''))}
            </section>

            <section class="block">
              <h3>🟢 Disponíveis na liga</h3>
              {_free_agents_block(team.get('free_agents', []))}
            </section>
          </div>

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
  <div class="updated">Atualizado automaticamente em {now} · <span class="flag-badge flag-drop-badge">↓</span> considere trocar · <span class="flag-badge flag-add-badge">↑</span> melhor opção disponível</div>
  <div class="tabset">
    {radios}
    <div class="tab-labels">{labels}</div>
    <div class="panels">{panels}</div>
  </div>
</body>
</html>"""
