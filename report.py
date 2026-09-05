from datetime import datetime, timezone

STYLE = """
<style>
  :root { color-scheme: light dark; }
  body { font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 16px; line-height: 1.5; }
  h1 { font-size: 1.6rem; margin-bottom: 0; }
  .updated { color: #888; font-size: 0.85rem; margin-bottom: 32px; }
  .team { border: 1px solid #ddd; border-radius: 10px; padding: 20px 24px; margin-bottom: 24px; }
  .team h2 { margin-top: 0; font-size: 1.2rem; }
  .platform { color: #888; font-weight: normal; font-size: 0.85rem; }
  table { width: 100%; border-collapse: collapse; margin-top: 8px; }
  th, td { text-align: left; padding: 8px 6px; border-bottom: 1px solid #eee; font-size: 0.92rem; }
  th { color: #888; font-weight: 600; font-size: 0.8rem; text-transform: uppercase; }
  .gap { font-weight: 600; color: #1a7f37; }
  .empty { color: #888; font-style: italic; }
  .pos-badge { display:inline-block; background:#eef; border-radius: 6px; padding: 1px 8px; font-size: 0.78rem; font-weight:600; }
</style>
"""


def render(results: list[dict]) -> str:
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    sections = []
    for team in results:
        rows = ""
        if team["suggestions"]:
            for s in team["suggestions"]:
                rows += f"""
                <tr>
                  <td><span class="pos-badge">{s['position']}</span></td>
                  <td>{s['drop']} <small>(#{s['drop_rank']})</small></td>
                  <td>→ {s['add']} <small>(#{s['add_rank']})</small></td>
                  <td class="gap">+{s['gap']} posições</td>
                </tr>"""
            table = f"""
            <table>
              <tr><th>Posição</th><th>Trocar</th><th>Por</th><th>Ganho</th></tr>
              {rows}
            </table>"""
        else:
            table = '<p class="empty">Nenhuma sugestão hoje — seu elenco está bem posicionado nessa liga.</p>'

        sections.append(f"""
        <div class="team">
          <h2>{team['label']} <span class="platform">({team['platform']})</span></h2>
          {table}
        </div>""")

    return f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Fantasy Football — Sugestões de Troca</title>
{STYLE}
</head>
<body>
  <h1>🏈 Fantasy Football — Sugestões de Troca</h1>
  <div class="updated">Atualizado automaticamente em {now}</div>
  {''.join(sections)}
</body>
</html>"""
