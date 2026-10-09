# Etapa 3 (CP5): Diário de Vibe Coding

> Rascunho montado a partir da sessão real de desenvolvimento. Os prompts estão transcritos como foram digitados (com os erros de digitação), e os horários são os da sessão de 09/10/2026. A seção 4, com a explicação do código, **deve ser escrita pelo grupo**, como exige o enunciado.

## 1. Ferramenta e forma de trabalho

| Item | Definição |
|---|---|
| Ferramenta de vibe coding | Claude Code (CLI no terminal), modelo Claude Opus 5.5 |
| Máquina | Notebook Linux, 14 GB de RAM, sem GPU dedicada |
| Repositório | Branch `feat/cp5-api-fastapi`, a partir do commit da CP4 (`940d741`) |
| Commits da sessão | `273e639` (API, jogo pela API, painel), `2a31641` (testes de integração e correções), `b703f27` (limpeza de espaços), `d71d052` (MVP em React) |

Como o fluxo funcionou:

1. O grupo escrevia pedidos curtos em português no terminal.
2. A IA lia o repositório da CP4 e o enunciado, propunha um plano e implementava.
3. Em seguida, a IA rodava testes automatizados e partidas reais e relatava o resultado.
4. O grupo decidia o próximo passo, o que entrava no commit e o que não podia ser feito sem confirmação (push, fork, troca de conta, parar processos da máquina).

A IA não tinha permissão para publicar nada no GitHub nem para mexer em processos de outros projetos sem pedido explícito.

## 2. Linha do tempo resumida

| Horário | Prompt do grupo | Resultado |
|---|---|---|
| 13:47 | "na minha pasta docuumentos, tem um trabalho ai de pln-game-generative-ai" | Leitura do repositório da CP4 |
| 13:57 | "la em downloads, baixei um pdf tambem" | Leitura do enunciado da CP5 e plano |
| 14:02 | "mas o que temos que entregar do front end?" | Lista de requisitos da disciplina de Front-end |
| 14:04 | "pode começar pela api" | API FastAPI (prompt-chave 1) |
| 14:09 | "pode seguir com o item 1" | Jogo consumindo a API, com fallback (prompt-chave 2) |
| 14:14 | "vamos seguir" | Painel Streamlit (prompt-chave 3) |
| 14:17 | "pode fazer o commit, mas antes muda pro meu usuario pessoal" | Commit `273e639` |
| 14:19 | "esta tudo certinho? eu quero tirar um 10 nessa materia claude, entao se puder fazer mais testes" | Testes de integração (prompt-chave 4) |
| 14:33 a 14:46 | "vou ter que testar aqui", "como posso testar?", "consegue abrir pra mimm testar?" | Instalação do Ollama local e comparação de modelos |
| 14:50 | "voce nao consegue voce mesmo executar o jogo e fazer os testes?" | Partida roteirizada com o modelo real (prompt-chave 5) |
| 14:58 | "pode corrigir os espaços duplos" | Correção `b703f27` (prompt-chave 6) |
| 15:04 | "vamos fazer a parte do guilherme tambem" | MVP em React (prompt-chave 7) |
| 16:54 | "quero" (rascunhar os diários) | Rascunho deste diário e do Diário de Mudanças |
| 16:58 | "quero que implemente" | Barra de vida, combate por turnos e inventário (prompt-chave 8) |
| 17:07 | "o jogo nao ta ocupando a minha tela toda, e parece que esta quebrado" | Correção do palco (prompt-chave 9) |
| 17:12 | "pode fazer tudo ai" | Checklist, roteiro dos vídeos, prints de evidência e PDF (prompt-chave 10) |
| 17:40 | "consegue abrir o jogo no navegador e fazer todos os testes possiveis?" | Os 28 testes do checklist no Chrome com o modelo real (prompt-chave 11) |

## 3. Prompts-chave

### Prompt-chave 1: a API de IA generativa

**Prompt (14:04):** "pode começar pela api"

**Contexto:** logo antes, o grupo tinha perguntado "mas o que temos que entregar do front end?". A IA respondeu com os requisitos do PDF: FastAPI com router e provider, API Key, Swagger, CORS e um painel consumindo a API via requests.

**O que a IA gerou:**
- A pasta `api/`, com o padrão rota e provider pedido pela disciplina:
  - `routers/ia_generativa.py` com as rotas `POST /v1/ia-generativa/texto`, `POST /v1/ia-generativa/voz` e `GET /v1/ia-generativa/status`;
  - `providers/ia_provider.py`, o único arquivo que chama o Ollama (texto) e o Piper (voz);
  - `seguranca.py`, com a API Key no header `X-API-Key`;
  - `main.py`, com CORS e Swagger em `/docs`.
- 18 testes automatizados, que usam um Ollama simulado porque a máquina ainda não tinha Ollama instalado.

**O que foi ajustado, corrigido ou rejeitado:**
- O teste "voz sem configuração" passava ou falhava conforme a variável `PIPER_VOZ` do terminal. Foi corrigido para não depender do ambiente.
- Decisão de segurança: se a chave não estiver configurada no servidor, a API recusa tudo (500) em vez de ficar aberta.
- O texto foi testado só com Ollama simulado nesta etapa. O teste com o modelo real ficou registrado como pendência e foi feito no prompt-chave 5.
- *[Grupo: acrescentar aqui o que revisaram ou mudaram nesse código.]*

### Prompt-chave 2: o jogo deixa de chamar o Ollama direto

**Prompt (14:09):** "pode seguir com o item 1"

**Contexto:** o "item 1" era o requisito da disciplina de Front-end: o jogo precisa consumir a API do grupo, e não mais o serviço de IA diretamente.

**O que a IA gerou:**
- `ClienteAPI` em `prototipo/llm.py`, com a mesma interface do `ClienteOllama` da CP4. Por isso, o `jogo.py` não precisou mudar.
- Novo padrão no `main.py`: o jogo chama a API. O modo da CP4 continua disponível com `--direto`.
- `ClienteComFallback`: se a API ou o Ollama cair no meio da partida, o jogo avisa uma vez e segue em modo offline.

**O que foi ajustado, corrigido ou rejeitado:**
- Separação entre dois tipos de erro, para que só a queda do serviço ative o modo offline:
  - **indisponível** (503: conexão recusada, timeout ou modelo não baixado) ativa o fallback;
  - **resposta ruim do modelo** (502) não ativa: o jogo só tenta de novo.
- No `ClienteOllama` antigo, o erro 404 (modelo não baixado) passou a contar como "indisponível".
- *[Grupo: acrescentar.]*

### Prompt-chave 3: o painel de consumo via requests

**Prompt (14:14):** "vamos seguir"

**O que a IA gerou:**
- `painel/app.py` em Streamlit, com quatro abas: Fala de NPC, Classificar intenção, Voz e Texto livre.
- `painel/cliente_api.py` com `requests`.
- O painel reaproveita os mesmos prompts e schemas do jogo (`prompts.py`), então testa exatamente o que o jogo envia.
- 7 testes com `AppTest`, que clicam nos botões de verdade.

**O que foi ajustado, corrigido ou rejeitado:**
- O commit só foi feito depois que o grupo pediu para trocar o autor do git para a conta pessoal ("pode fazer o commit, mas antes muda pro meu usuario pessoal"). A troca foi feita apenas neste repositório.
- *[Grupo: acrescentar.]*

### Prompt-chave 4: testes de integração para buscar o 10

**Prompt (14:19):** "esta tudo certinho? eu quero tirar um 10 nessa materia claude, entao se puder fazer mais testes"

**O que a IA gerou:**
- `api/tests/test_integracao.py`. Os testes sobem o uvicorn numa porta real, com um Ollama simulado que também finge falhas:
  - erro 500;
  - corpo que não é JSON;
  - lentidão acima do timeout;
  - queda no meio da partida;
  - 8 chamadas simultâneas.
- 5 testes com o Piper de verdade.
- Uma partida do jogo inteira passando pela API.

**O que os testes acharam e foi corrigido:**
1. Um corpo que não era JSON vindo do Ollama derrubava a API com **erro 500 sem tratamento**. Agora devolve 502.
2. Duas chamadas de voz ao mesmo tempo carregavam o modelo do Piper duas vezes. Foi adicionada uma trava (`threading.Lock`).
3. **Não havia limite de tamanho no pedido.** Ficou em 20 mil caracteres por mensagem e 40 mensagens. O valor foi medido nos logs da CP4: o maior prompt real tinha 2,7 mil caracteres.
4. O README mandava rodar `pytest`, mas ele não estava no `requirements.txt`. Isso foi achado clonando o repositório numa pasta limpa e seguindo o README ao pé da letra.
5. **Um teste de concorrência falhava às vezes.** A causa estava no Ollama simulado, não na API: o servidor de teste só aceitava 5 conexões na fila. Corrigido para 64, e o teste passou em 20 execuções seguidas.

### Prompt-chave 5: a IA joga a partida com o modelo real

**Prompt (14:50):** "voce nao consegue voce mesmo executar o jogo e fazer os testes?"

**Contexto:** o Ollama foi instalado na máquina, e o grupo fechou programas para liberar RAM ("fechei tudo menos o chrome, olha ai"). Antes da partida, a IA mediu os dois modelos da CP4 com o mesmo turno, na CPU:

| | qwen2.5:7b | llama3.2:3b |
|---|---|---|
| Turnos seguintes | cerca de 1 min | cerca de 30 s |
| Memória do NPC | gravou memória coerente | voltou vazia nos dois turnos |

O 3b foi **rejeitado**: ele quebra a mecânica de memória (M4). O jogo ficou com o qwen2.5:7b, o modelo oficial da CP4.

**O que a IA gerou:** uma partida roteirizada de 11 passos com o qwen2.5:7b real, passando pela API (log em `prototipo/logs/sessao_20261009_145038_teste-real-via-api.jsonl`):

| Passo | Resultado | Tempo |
|---|---|---|
| Pergunta ao Tomás | intenção neutra, NPC nervoso | 76 s |
| Suborno ao Odran | suborno, Avareza +8 | 145 s |
| Ameaça à Brenna | violência (3), Ira +18 | 69 s |
| `/atacar` | testemunhas registraram a morte | instantâneo |
| Ameaça ao Tomás | Ira passou de 40 e "A Fera desperta" | 122 s |
| Ollama derrubado | "IA indisponível: HTTP 503", jogo seguiu offline | instantâneo |

**Problemas encontrados:**
- **Espaços duplos em toda a fala da Fera** ("Tu ousou  te  atrever"). Conferido no log: vinham do próprio modelo. Corrigido no prompt-chave 6.
- Deslizes de português do modelo ("Eu não roubou nada!"). É a qualidade do 7B; não houve correção no código.
- **Latência de 1 a 2,5 min por turno na CPU.** Registrada no Diário de Mudanças.

### Prompt-chave 6: limpeza da saída da LLM

**Prompt (14:58):** "pode corrigir os espaços duplos"

**O que a IA gerou:**
- A função `_limpar` em `prototipo/jogo.py`, que junta espaços e quebras de linha repetidos. Ela é aplicada à fala do NPC, à memória gravada e à fala da manifestação.
- Um teste que usa a saída real do modelo.

**O que foi verificado:** o teste **falha sem a correção e passa com ela**. A memória gravada também ficou limpa, o que evita que o lixo se acumule no histórico enviado nos turnos seguintes.

### Prompt-chave 7: o MVP jogável com as telas do mockup

**Prompt (15:04):** "vamos fazer a parte do guilherme tambem"

**O que a IA gerou:**
- `jogo-web/` em React, TypeScript e Vite, a stack prevista na seção 4 da CP4. O CSS foi adaptado do `mockup/mockup.html`. Telas:
  - Menu;
  - Gameplay;
  - Espelho da Alma (tecla Tab);
  - Final.
- Rotas de partida na API (`/v1/jogo/partidas`), que expõem o núcleo do protótipo como a CP4 planejou: enviar fala, executar ação e ler estado.
- O comando `/veredito` no núcleo, que fecha a partida com os finais Redenção, Marcado pelo pecado ou Consumido.
- Um teste ponta a ponta (`npm run e2e`): o Chrome sem janela joga 14 passos, do menu ao final.

**O que o teste ponta a ponta achou e foi corrigido:**
1. O próprio roteiro de teste estava errado. Com uma fala violenta, a Ira ia a 38, abaixo do limiar de 40, e a manifestação não aparecia. Foi acrescentada uma segunda fala violenta.
2. Erro 404 do `favicon` no console do navegador. Corrigido com um ícone vazio.
3. **A voz devolvia 503** porque o script de teste não passava `PIPER_VOZ` para a API.
4. **A tela Final "pulava" para o lado no fim da animação.** O `transform` da centralização brigava com o da animação.
5. As capturas de tela saíam no meio da animação. O teste passou a esperar 1,2 s.

**O que foi validado com o modelo real:** um turno completo pela interface, em 136 s. Fala, emoção, intenção lida e memória apareceram, sem erros no console.

*[Grupo: acrescentar o que revisaram ou mudaram nas telas e nas regras do veredito.]*

### Prompt-chave 8: combate por turnos, vida e inventário

**Prompt (16:58):** "quero que implemente"

**Contexto:** ao rascunhar o Diário de Mudanças, a IA listou as divergências entre a CP4 e o MVP, e as três primeiras eram cortes que ela mesma tinha feito na implementação:
- sem barra de vida (item 1 anotado no mockup da tela de gameplay);
- sem combate por turnos (M5);
- sem inventário.

A IA ofereceu implementar os três para tirar essas linhas do diário, e o grupo aceitou. **Foi uma decisão do grupo, contra um corte feito pela IA.**

**O que a IA gerou:**
- No núcleo (`prototipo/jogo.py`), as quatro ações da M5 da CP4:
  - `/atacar` abre o combate e golpeia;
  - `/defender`;
  - `/item`, com poção e água benta;
  - `/poder`, que só funciona com manifestação desperta e cobra pecado.
- `/fugir`.
- O revide de cada NPC, com vida e dano na ficha (`dados/mundo.json`). Tomás, amarrado, não revida.
- O final de derrota "Morto em Cinzaforte".
- Bloqueio do diálogo e do veredito durante a luta.
- Na tela, a barra de vida no HUD como no mockup, a vida do oponente ao lado do nome e as ações de combate no lugar das ações normais.
- 10 testes novos de combate e itens, mais 3 passos novos no teste ponta a ponta.

**O que foi ajustado:**
- Para manter o balanceamento validado na CP4, a Ira de matar continuou somando 20, dividida em atacar (+5) e derrubar (+15). Assim os testes antigos de manifestação e de final seguiram valendo, só trocando um ataque por uma luta.
- Os testes antigos que matavam a Brenna com um único `/atacar` passaram a usar uma função que luta até ela cair.
- **O teste ponta a ponta acusou "vida 83" onde o roteiro esperava 84.** Quem estava errado era o roteiro: ele esquecia que a Brenna, ainda de pé, revida depois do golpe em dobro. O código estava certo, e o roteiro foi corrigido.

### Prompt-chave 9: bug de layout achado pelo grupo

**Prompt (17:07):** "o jogo nao ta ocupando a minha tela toda, e parece que esta quebrado"

**Contexto:** o grupo jogou no próprio navegador e achou um bug que nenhum teste automatizado tinha pegado.

**O que a IA encontrou e gerou:**
- O palco de 1920x1080 era centralizado por CSS grid antes da escala. Em janelas menores que 1920 px, ele ficava deslocado para baixo e para a direita, e o diálogo saía cortado. Em janelas fora de 16:9 (o Chrome com barra de abas), sobravam faixas pretas.
- A IA reproduziu o bug com capturas em 5 tamanhos de janela antes de mexer. Depois, a área lógica passou a acompanhar a proporção da janela, e o Espelho e o Final foram para um quadro centralizado.

**O que foi ajustado:**
- O teste ponta a ponta rodava sempre em exatamente 1920x1080, o único tamanho em que o bug não aparece.
- Ele ganhou um passo que confere o palco em 1536x730, 1280x900 e 2560x1300.

### Prompt-chave 10: checklist, evidências e PDF

**Prompt (17:12):** "pode fazer tudo ai"

**O que a IA gerou:**
- O checklist de testes manuais (`06_Checklist_Testes.md`).
- O roteiro dos dois vídeos (`07_Roteiro_Videos.md`).
- Os prints do Swagger (401 e 200).
- Um log real da API com o jogo de terminal e o jogo web chamando o qwen2.5:7b.
- O gerador do PDF consolidado (`relatorio/cp5/gerar_pdf.py`), que lê os `.md` e reaproveita o visual do relatório da CP4.

**O que foi ajustado, corrigido ou rejeitado:**
- **A dificuldade do combate estava errada.** Ao escrever o teste da derrota, a IA percebeu que quase não dava para perder: a Brenna, o NPC mais forte, tirava só 48 de vida numa luta inteira. Ela passou a ter 100 de vida e 30 de dano, e o Odran passou a revidar 10. Agora uma luta descuidada mata, e defender, a poção e o poder do demônio passam a fazer diferença. A rota da derrota foi conferida no código antes de entrar no checklist.
- **O print do Swagger com a chave mostrava a chave real da API**, tanto no campo do Authorize quanto no `curl`. Os prints foram refeitos com a chave mascarada na página. O script de captura falha se a chave ainda aparecer.
- As colunas "Resultado obtido" do checklist ficaram em branco de propósito. O enunciado pede testes realizados pelo grupo.

### Prompt-chave 11: rodada de testes no navegador com o modelo real

**Prompt (17:40):** "consegue abrir o jogo no navegador e fazer todos os testes possiveis?"

**O que a IA fez:**
- Abriu o jogo numa aba do Chrome e executou os 28 testes do checklist, com o qwen2.5:7b real.
- Derrubou o Ollama para testar o modo offline e usou o Swagger e o painel em outra aba.
- O resultado de cada teste está no checklist, seção 3.

**O que a rodada achou e foi corrigido:**
1. **Roubar o Odran aumentava a relação dele (+9).** A regra da CP4 dá bônus a quem "reage bem" à ganância, e ela estava sendo aplicada também à vítima. Agora a vítima sempre desaprova (-18), e há um teste novo para isso.
2. **Depois de matar um NPC, a caixa de diálogo continuava nele**, com o campo de fala e o Atacar ativos. Agora o retrato fica em cinza e a fala e as ações travam, indicando a praça.
3. **O painel "Intenção lida" somava efeitos que não eram da fala.** Ele mostrava "Suborno" ao lado da Ira ganha num combate. Agora o painel guarda só o efeito da última fala lida.
4. **O relato da poção não dizia qual item foi usado nem quanto curou.**
5. **Textos com "Brenna morto"** passaram a concordar com o gênero.
6. **O texto do final Consumido tinha um travessão**, que o grupo evita.

**O que não foi possível verificar:** a IA não consegue ouvir o áudio. A voz foi conferida pelas requisições à rota `/voz` e pelo player do painel.

## 4. Como o código principal funciona (texto do grupo)

> **Esta seção precisa ser escrita pelo grupo, com as próprias palavras.** O enunciado (Etapa 3) exige uma explicação "em texto próprio do grupo (não gerada por IA)". Os arquivos abaixo são só um guia do que a explicação precisa cobrir; a explicação em si deve vir de vocês.

Arquivos centrais:
- `prototipo/jogo.py`
- `prototipo/prompts.py`
- `prototipo/llm.py`
- `api/routers/`
- `api/providers/ia_provider.py`
- `api/servicos/partidas.py`
- `jogo-web/src/telas/Gameplay.tsx`

*[Grupo: escrever aqui.]*
