"""Gera OS_7_PECADOS_CP5.pdf: README, arquitetura e evidências, telas, diários e checklist num documento só.

Os diários e o checklist são lidos dos .md da raiz, então basta editar os .md e rodar de novo:
    .venv/bin/pip install markdown
    .venv/bin/python relatorio/cp5/gerar_pdf.py
Usa o Chrome/Chromium instalado para imprimir o HTML em PDF (variável CHROME para outro caminho).
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

import markdown

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
SAIDA = RAIZ / "OS_7_PECADOS_CP5.pdf"
REPO = "https://github.com/guilhermegamabs/pln-game-generative-ai"
MESES = "janeiro fevereiro março abril maio junho julho agosto setembro outubro novembro dezembro".split()


def css_da_cp4():
    """Mesmo visual do relatório da CP4: reaproveita o <style> de relatorio/relatorio.html."""
    html = (RAIZ / "relatorio" / "relatorio.html").read_text(encoding="utf-8")
    css = re.search(r"<style>(.*?)</style>", html, re.S).group(1)
    css = css.replace("Relatório Técnico · CP4 PLN", "Relatório CP5 · MVP")
    return css.replace('url("img/menu_fundo.jpg")', 'url("img/menu_fundo.jpg")')


EXTRA_CSS = """
  .pendente { background: #fff1b8; outline: 1px solid #e0b400; padding: 0 1mm; font-style: italic; }
  .aviso-rascunho { border: 2px solid #e0b400; background: #fffbe6; padding: 3mm 4mm; margin: 4mm 0; font: 10pt var(--sans); }
  .md h1 { break-before: auto; font-size: 15pt; border: 0; color: var(--tinta); margin-top: 6mm; }
  .md h2 { font-size: 13pt; color: var(--sangue); }
  .md h3 { font-size: 11pt; }
  .md blockquote { margin: 3mm 0; padding: 2mm 4mm; border-left: 4px solid var(--ouro); background: #fbf8f2; font-style: italic; }
  .md blockquote p:last-child { margin: 0; }
  .md table { font-size: 8.4pt; }
  .tela-print { margin: 2mm 0 5mm; }
  .tela-print img { width: 100%; border: 1px solid var(--linha); border-radius: 1mm; }
  .pag-larga { page: paisagem; break-before: page; }
  .pag-larga > h1 { break-before: auto; }
  .pag-larga .md table { font-size: 8.6pt; }
  .evid img { max-height: 120mm; object-fit: contain; object-position: left top; }
"""


def md(texto):
    texto = _ajustar_listas(texto)
    html = markdown.markdown(texto, extensions=["tables", "fenced_code", "sane_lists"])
    # Trechos que o grupo ainda precisa preencher ficam marcados em amarelo no PDF.
    return re.sub(r"\[Grupo:[^\]]*\]", lambda m: f'<span class="pendente">{m.group(0)}</span>', html)


def _ajustar_listas(texto):
    """Os .md usam sub-itens com 2 espaços e listas logo abaixo de um parágrafo, como no GitHub.
    O Python-Markdown exige 4 espaços e uma linha em branco antes; converte sem mudar o conteúdo."""
    saida, anterior = [], ""
    item = re.compile(r"^(\s*)([-*]|\d+\.)\s")
    for linha in texto.splitlines():
        m = item.match(linha)
        if m:
            linha = " " * (len(m.group(1)) * 2) + linha.lstrip()
            # Sem linha em branco antes, o item vira continuação do parágrafo anterior (até de um parágrafo recuado).
            if anterior.strip() and not item.match(anterior):
                saida.append("")
        saida.append(linha)
        anterior = linha
    return "\n".join(saida)


def secao_md(arquivo):
    texto = (RAIZ / arquivo).read_text(encoding="utf-8")
    texto = re.sub(r"\A# .*\n", "", texto)  # o título vira o h1 numerado do relatório
    texto = texto.replace("\n## ", "\n### ").replace("\n### ", "\n### ")
    return f'<div class="md">{md(texto)}</div>'


def bloco_log(arquivo, filtro=None, limite=40):
    linhas = (AQUI / "evidencias" / arquivo).read_text(encoding="utf-8").splitlines()
    if filtro:
        linhas = [l for l in linhas if re.search(filtro, l)]
    texto = "\n".join(linhas[:limite])
    texto = texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    texto = re.sub(r'("(?:POST|GET) /v1/[^"]*")', r'<span class="r">\1</span>', texto)
    return f"<pre>{texto}</pre>"


def figura(nome, legenda, classe="tela-print"):
    return f'<figure class="{classe}"><img src="img/{nome}"><figcaption>{legenda}</figcaption></figure>'


def montar():
    hoje = date.today()
    data = f"{hoje.day} de {MESES[hoje.month - 1]} de {hoje.year}"
    fontes = "".join((RAIZ / f).read_text(encoding="utf-8") for f in ("04_Diario_Vibe_Coding.md", "05_Diario_de_Mudancas.md", "06_Checklist_Testes.md"))
    pendentes = len(re.findall(r"\[Grupo:", fontes))
    aviso = (
        f'<div class="aviso-rascunho"><b>Rascunho:</b> há {pendentes} trecho(s) marcados em amarelo que o grupo ainda precisa '
        "preencher (explicação do código, revisões, resultados dos testes manuais). Edite os .md da raiz e gere o PDF de novo.</div>"
        if pendentes
        else ""
    )
    corpo = f"""
<section class="capa">
  <div class="arte"></div>
  <div class="conteudo">
    <div class="disciplina">Checkpoint 5 · Vibe Coding e MVP · NLP e Front-end</div>
    <h1 class="titulo-jogo">OS 7 PECADOS</h1>
    <div class="sub">MVP jogável do RPG da CP4, API FastAPI de IA generativa e diários de desenvolvimento</div>
    <div class="meta">
      <div><b>Integrantes</b>Guilherme Gama Bitencourt Souza · RM565293<br>Igor Thiago Nakajima Vieira · RM563632</div>
      <div><b>Data</b>{data}</div>
      <div style="grid-column: 1 / -1"><b>Repositório</b><a href="{REPO}" style="color:#f3dfae">{REPO.removeprefix("https://")}</a></div>
      <div style="grid-column: 1 / -1"><b>Vídeos</b>PLN: <span class="pendente">[Grupo: link do vídeo de 2 a 5 min]</span> · Front-end: <span class="pendente">[Grupo: link do vídeo da arquitetura]</span></div>
    </div>
  </div>
</section>

<section class="sumario">
  <h1>Sumário</h1>
  {aviso}
  <ol>
    <li><span class="n">1</span>O MVP em uma página</li>
    <li><span class="n">2</span>Como executar</li>
    <li><span class="n">3</span>Arquitetura e API (disciplina de Front-end)</li>
    <li><span class="n">4</span>Telas do MVP</li>
    <li><span class="n">5</span>Diário de Vibe Coding</li>
    <li><span class="n">6</span>Diário de Mudanças em relação à CP4</li>
    <li><span class="n">7</span>Checklist de testes</li>
  </ol>
  <div class="caixa ia">
    <p><span class="tag-ia">IA</span> <strong>Uso de IA neste trabalho.</strong> O MVP foi desenvolvido com vibe coding (Claude Code), como pede a CP5; o Diário de Vibe Coding (seção 5) registra os prompts reais. A explicação do código na seção 5.4 é texto do grupo. Os resultados de testes e medições apresentados foram executados de fato; os registros brutos estão no repositório.</p>
  </div>
</section>

<h1><span class="num">1</span>O MVP em uma página</h1>
<p>O MVP é a continuação direta da CP4: mesmo título, gênero e premissa. É um RPG narrativo em que o inquisitor chega à Praça do Pelourinho, em Cinzaforte, e decide o destino de Tomás, acusado de roubo, enquanto cada escolha alimenta os sete pecados. A stack é a que a CP4 previu: front-end em React + TypeScript (Vite) e back-end em Python com FastAPI, que expõe o núcleo do jogo já testado na CP4.</p>
<table>
  <thead><tr><th style="width:42mm">Mecânica da CP4</th><th>Como funciona no MVP</th></tr></thead>
  <tbody>
    <tr><td><strong>M1. Diálogo livre</strong></td><td>O jogador digita; a LLM classifica a intenção (JSON Schema, temperatura 0) e, numa segunda chamada, o NPC responde em personagem com emoção e memória.</td></tr>
    <tr><td><strong>M2. Corrupção</strong></td><td>Sete medidores de 0 a 100; a intenção lida e as ações (roubar, doar, atacar, matar) movem os pecados por regras fixas no código.</td></tr>
    <tr><td><strong>M3. Demônio Interior</strong></td><td>Ao cruzar 40, a manifestação (A Fera, O Mercador) desperta e sussurra com fala gerada pela LLM e voz do Piper; o poder dela pode ser usado em combate, ao custo de mais pecado.</td></tr>
    <tr><td><strong>M4. Memória e reputação</strong></td><td>NPCs guardam memórias geradas pela LLM; testemunhas lembram de mortes; o segredo só entra no prompt com confiança; pecados altos marcam a aparência.</td></tr>
    <tr><td><strong>M5. Combate por turnos</strong></td><td>Atacar, defender, usar item (poção, água benta) e poder demoníaco; o NPC revida; vida zerada é derrota.</td></tr>
  </tbody>
</table>
<table>
  <thead><tr><th style="width:42mm">Requisito da CP5</th><th>Onde está</th></tr></thead>
  <tbody>
    <tr><td>Menu e gameplay do mockup</td><td>Menu, Gameplay, Espelho da Alma e Final (seção 4)</td></tr>
    <tr><td>Fim de sessão</td><td>Veredito sobre Tomás: Redenção, Marcado pela Ira/Avareza; também Consumido (pecado em 100) e Morto em Cinzaforte (derrota em combate)</td></tr>
    <tr><td>IA generativa integrada</td><td><strong>Texto</strong> ao vivo (qwen2.5:7b via Ollama), <strong>voz</strong> ao vivo (Piper TTS) e <strong>imagens</strong> do SDXL geradas na CP4, todas pela API do grupo</td></tr>
    <tr><td>Extras para a nota 10</td><td>2 modalidades em tempo real (texto e voz); 5 mecânicas (mínimo 3); 98 testes automatizados (43 do núcleo, 48 da API, 7 do painel) mais um teste ponta a ponta de 17 passos; fallback para modo offline quando a IA cai; feedback visual (indicador "pensando", animações, barras)</td></tr>
  </tbody>
</table>

<h1><span class="num">2</span>Como executar</h1>
<p>Requisitos: Python 3.11+, Node 20+, <a href="https://ollama.com">Ollama</a> com o modelo <code>qwen2.5:7b</code> e, para voz, a voz <code>pt_BR-faber-medium</code> do Piper. Os READMEs de cada pasta têm os comandos para Windows.</p>
<pre>ollama pull qwen2.5:7b
python -m venv .venv && .venv/bin/pip install -r api/requirements.txt
cp api/.env.example api/.env          # defina API_KEY e PIPER_VOZ (nunca commitar o .env)
cd api && ../.venv/bin/uvicorn main:app --env-file .env        # API em http://localhost:8000 (Swagger em /docs)
cd jogo-web && cp .env.example .env.local                      # VITE_API_KEY = mesma chave
npm install && npm run dev                                     # jogo em http://localhost:5173</pre>
<p>Testes: <code>prototipo/</code> (unittest), <code>api/</code> e <code>painel/</code> (pytest) e <code>jogo-web/</code> (<code>npm run e2e</code>). Nenhuma chave real está no código: a API lê <code>API_KEY</code> do <code>.env</code> e recusa tudo se ela não estiver definida.</p>

<h1><span class="num">3</span>Arquitetura e API (disciplina de Front-end)</h1>
<pre>navegador (jogo-web) ──X-API-Key──► API FastAPI ──► providers/ia_provider.py ──► Ollama (qwen2.5:7b, texto)
painel Streamlit ─────X-API-Key──►   routers/              │                  └─► Piper TTS (voz)
jogo de terminal ─────X-API-Key──►                         └─► núcleo do jogo (prototipo/)</pre>
<table>
  <thead><tr><th style="width:62mm">Rota</th><th>O que faz</th></tr></thead>
  <tbody>
    <tr><td><code>POST /v1/ia-generativa/texto</code></td><td>Mensagens + JSON Schema opcional → texto ou JSON gerado pela LLM, modelo e latência</td></tr>
    <tr><td><code>POST /v1/ia-generativa/voz</code></td><td>Texto → áudio WAV do Piper (gestos entre asteriscos não são falados)</td></tr>
    <tr><td><code>GET /v1/ia-generativa/status</code></td><td>Disponibilidade de texto e voz (o jogo decide o modo offline)</td></tr>
    <tr><td><code>POST /v1/jogo/partidas</code>, <code>GET /v1/jogo/partidas/{{id}}</code>, <code>POST …/comandos</code></td><td>Partidas do jogo web: fala livre ou ação; devolve fala, intenção lida, memória, pecados, combate, manifestação, final e estado</td></tr>
  </tbody>
</table>
<p><strong>Router e provider:</strong> os routers só validam (Pydantic) e traduzem erros em códigos HTTP (401, 404, 409, 422, 502, 503); o provider é a única camada que conhece o Ollama e o Piper. <strong>Autenticação:</strong> header <code>X-API-Key</code>, comparado em tempo constante. <strong>CORS:</strong> liberado só para a origem do jogo (Vite, porta 5173). <strong>Swagger:</strong> automático em <code>/docs</code>.</p>
<h2>Evidência: Swagger, 401 e 200</h2>
{figura("f1_swagger.png", "Swagger em /docs: rotas de IA generativa e do jogo, com o botão Authorize.", "tela-print evid")}
{figura("f2_swagger_401.png", "GET /v1/ia-generativa/status sem a chave: 401 “API Key ausente ou inválida”.", "tela-print evid")}
{figura("f4_swagger_200.png", "Com a chave (Authorize, header X-API-Key): 200, texto e voz disponíveis. A chave foi mascarada no print.", "tela-print evid")}
<h2>Evidência: o jogo consome a API, não o Ollama</h2>
<p>Log do uvicorn durante a coleta das evidências: o 401 e o 200 do Swagger, o jogo de terminal (<code>/status</code> e <code>/texto</code>) e o jogo web (<code>/v1/jogo/partidas</code> e a voz), todos com o qwen2.5:7b real.</p>
{bloco_log("api.log", r'"(GET|POST) /v1/')}
<p>Turno real do jogo de terminal, passando pela API:</p>
{bloco_log("jogo_terminal.txt", r"^(\[modelo|Tomás:|  \[intenção)")}
{figura("f5_jogo_turno_real.jpg", "Jogo web com o modelo real: a fala, a intenção lida e a memória vieram da LLM pela API do grupo.")}

<h1><span class="num">4</span>Telas do MVP</h1>
{figura("1_menu.jpg", "Menu principal: arte SDXL, status do motor de IA e aviso de conteúdo gerado por IA.")}
{figura("2_gameplay_dialogo.jpg", "Gameplay: HUD com barra de vida, presentes na praça, medidores, intenção lida, memória e diálogo com retrato e voz.")}
{figura("3_combate.jpg", "Combate por turnos: vida do oponente ao lado do nome, relato do turno e ações de combate.")}
{figura("4_gameplay_fera.jpg", "Demônio Interior: a Ira passou de 40 e A Fera sussurra com fala gerada pela LLM.")}
{figura("5_espelho_da_alma.jpg", "Espelho da Alma (Tab): pecados, aparência, manifestações e progresso para cada final.")}
{figura("6_final.jpg", "Final: o veredito encerra a partida; o desfecho depende dos pecados.")}

<h1><span class="num">5</span>Diário de Vibe Coding</h1>
{secao_md("04_Diario_Vibe_Coding.md")}

<section class="pag-larga">
<h1><span class="num">6</span>Diário de Mudanças em relação à CP4</h1>
{secao_md("05_Diario_de_Mudancas.md")}
</section>

<h1><span class="num">7</span>Checklist de testes</h1>
{secao_md("06_Checklist_Testes.md")}
"""
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><title>OS 7 PECADOS · Relatório CP5</title>
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;800&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&family=Source+Sans+3:wght@400;600;700&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet">
<style>{css_da_cp4()}{EXTRA_CSS}</style></head><body>{corpo}</body></html>"""


def main():
    html = AQUI / "relatorio_cp5.html"
    html.write_text(montar(), encoding="utf-8")
    chrome = os.environ.get("CHROME") or shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("msedge")
    if not chrome:
        print(f"HTML gerado em {html}; Chrome não encontrado para imprimir o PDF (defina CHROME).")
        return 1
    subprocess.run(
        [chrome, "--headless", "--no-pdf-header-footer", "--virtual-time-budget=8000", f"--print-to-pdf={SAIDA}", html.as_uri()],
        check=True,
        capture_output=True,
    )
    print(f"PDF: {SAIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
