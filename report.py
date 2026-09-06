from datetime import datetime
from zoneinfo import ZoneInfo
import config

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
  .slot-label { display:inline-block; background:#e6e6e6; border-radius: 6px; padding: 1px 8px; font-size: 0.76rem; font-weight:700; white-space:nowrap; }
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


def _my_team_tables(lineup_sections: dict, bench: list) -> str:
    if not lineup_sections and not bench:
        return '<p class="empty">Não consegui carregar seu elenco (veja os logs da Action).</p>'

    rows = ""
    for slot_label, players in lineup_sections.items():
        if not players:
            rows += f"<tr><td><span class='slot-label'>{slot_label}</span></td><td colspan='2' class='empty'>vazio</td></tr>"
            continue
        for p in players:
            rows += _player_row(p, extra_pos_cell=f"<span class='slot-label'>{slot_label}</span>")

    bench_rows = ""
    if bench:
        for p in bench:
            bench_rows += _player_row(p, extra_pos_cell=f"<span class='pos-badge'>{p['position'].upper()}</span>")
    else:
        bench_rows = "<tr><td colspan='3' class='empty'>Sem jogadores no banco</td></tr>"

    return f"""
    <p style="font-size:0.82rem;color:#888;margin:4px 0 10px;">Escalação titular</p>
    <table><tr><th>Slot</th><th>Jogador</th><th>Rank</th></tr>{rows}</table>
    <p style="font-size:0.82rem;color:#888;margin:16px 0 10px;">Banco</p>
    <table><tr><th>Pos</th><th>Jogador</th><th>Rank</th></tr>{bench_rows}</table>
    """


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
        rows = "".join(_player_row(p) for p in players)
        has_flag = any(p.get("flag") == "add" for p in players)
        blocks.append(f"""
        <details{' open' if has_flag else ''}>
          <summary>{pos.upper()} — {len(players)} disponíveis</summary>
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
              {_my_team_tables(team.get('lineup_sections', {}), team.get('bench', []))}
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
