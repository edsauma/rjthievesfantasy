# Fantasy Football Dashboard

Substitui a planilha com Power Query por um dashboard HTML que se atualiza
sozinho todo dia via GitHub Actions e fica publicado no GitHub Pages.

## Como funciona

- **Sleeper**: usa a API pública oficial (`api.sleeper.app`) — estável, sem chave.
- **Fleaflicker**: usa a API pública oficial (`fleaflicker.com/api`) — estável, sem chave.
- **FantasyPros**: não tem API gratuita, então lemos o JSON (`ecrData`) embutido
  na própria página de rankings — mais robusto que os seletores CSS da planilha
  original, mas ainda depende da estrutura do site. Se um dia parar de funcionar,
  o arquivo `clients/fantasypros.py` é o único lugar que precisa de ajuste.
- Todo dia a Action roda `main.py`, gera `docs/index.html` e publica.

## Configuração (única vez)

1. **Crie um repositório novo no GitHub** (pode ser privado) e suba esta pasta
   inteira para ele.

2. **Confira o `config.py`** — já preenchi com os IDs de liga/time que
   identifiquei na sua planilha original (ErreJota, Quevedo, Super Bowlo,
   Camisa). Se algum estiver errado, é só corrigir ali.

3. **Ative o GitHub Pages**:
   - Vá em `Settings` → `Pages`
   - Em "Build and deployment", escolha `Deploy from a branch`
   - Branch: `main`, pasta: `/docs`
   - Salve. Em alguns minutos seu dashboard estará em
     `https://SEU-USUARIO.github.io/SEU-REPOSITORIO/`

4. **Rode a Action pela primeira vez manualmente**:
   - Vá na aba `Actions` do repositório
   - Clique no workflow "Atualizar dashboard de fantasy football"
   - Clique em `Run workflow`

Pronto — a partir daí ela roda sozinha todo dia às 09:00 UTC (~06:00 em
Brasília) e o site se atualiza automaticamente.

## Rodando localmente (para testar antes de subir)

```bash
pip install -r requirements.txt
python main.py
# abre docs/index.html no navegador
```

## Ajustando a sensibilidade das sugestões

Em `config.py`, o valor `RANK_GAP_THRESHOLD` controla quantas posições de
diferença no ranking do FantasyPros são necessárias para um agente livre virar
sugestão de troca. Comece com 8 e ajuste conforme achar as sugestões
conservadoras/agressivas demais.

## Limitações conhecidas

- Não testei os clientes contra o Fleaflicker/FantasyPros/Sleeper ao vivo
  nesta sessão (meu ambiente de execução aqui não tem acesso a esses domínios
  específicos) — a lógica segue a documentação oficial das APIs e a estrutura
  conhecida das páginas, mas vale rodar localmente primeiro e conferir a saída
  antes de confiar 100% nas sugestões.
- A correspondência de nomes entre plataformas (`matcher.py`) cobre os casos
  comuns (acentos, Jr./Sr./II/III), mas nomes muito divergentes entre
  Sleeper/Fleaflicker/FantasyPros podem não casar — se notar um jogador
  "sumindo" das sugestões, provavelmente é isso.
- IDP (LB/DL/DB) tem convenções de nomenclatura de posição que variam bastante
  entre plataformas; pode precisar de ajuste fino em `config.py`.
