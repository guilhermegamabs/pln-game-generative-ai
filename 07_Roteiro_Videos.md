# Roteiro dos vídeos da CP5

Dois vídeos, um por disciplina. As falas são sugestões; falem com as próprias palavras.

**Antes de gravar:**
- Gravar na máquina com GPU, onde cada fala leva poucos segundos. Em CPU, cada fala leva de 1 a 2 minutos; se gravar assim, corte as esperas na edição e diga isso na narração.
- Começar com **Novo Jogo** (sem save) e com a voz ligada nas Opções.
- Deixar o terminal da API visível ao lado do navegador nos trechos de arquitetura.
- Gravar em 1920x1080, com o navegador em tela cheia (F11).

## Vídeo 1: PLN, MVP jogável (alvo de 4 minutos, máximo 5)

O PDF pede: menu, jogabilidade das mecânicas e o momento em que o conteúdo de IA aparece ou soa. Para o ponto extra, os itens precisam ficar "evidenciados no vídeo".

| Tempo | O que mostrar | O que falar |
|---|---|---|
| 0:00 a 0:20 | Menu com a arte, o status "qwen2.5:7b via API do grupo · pronto" e o aviso de IA | OS 7 PECADOS, RPG narrativo da CP4. O MVP foi feito em React e TypeScript com back-end FastAPI, como a CP4 previu. A arte do menu foi gerada com Stable Diffusion XL na CP4. |
| 0:20 a 0:35 | Clicar em Novo Jogo; a narração de abertura toca | A narração é voz gerada pelo Piper TTS. Estamos na Praça do Pelourinho: Tomás é acusado de roubo e a Capitã Brenna quer enforcá-lo. |
| 0:35 a 1:10 | Digitar "Calma, Tomás. Eu vou te ajudar."; "pensando"; resposta com voz; painéis Intenção lida e Memória | **M1, diálogo livre.** O que eu digito vai para a LLM duas vezes: primeiro ela classifica a intenção (compaixão), depois o Tomás responde em personagem. A voz é sintetizada na hora pelo Piper. O Tomás grava uma memória, que é a M4. |
| 1:10 a 1:40 | Ir até o Odran; "Te pago 20 moedas para você retirar a acusação"; medidor de Avareza subindo; depois Roubar | **M2, corrupção.** A LLM só lê a intenção (suborno); quanto o pecado sobe é regra fixa no código, então o modelo não inventa progressão. |
| 1:40 a 2:30 | Ir até a Brenna, Atacar e confirmar; barra de vida caindo; Defender, Golpear em dobro, Poção, golpe final; "Tomás viu tudo" | **M5, combate por turnos**, com as quatro ações da CP4. Defender abre uma brecha; a poção vem do inventário. Quando a Brenna cai, as testemunhas registram, e isso muda como elas me tratam. |
| 2:30 a 3:05 | Com o Tomás, "Eu vou te matar, ladrão!"; a Ira passa de 40; "A Fera sussurra" com retrato e voz; marcas no HUD | **M3, Demônio Interior.** A Ira passou de 40 e a manifestação despertou. A fala dela é gerada pela LLM e a voz pelo Piper. O retrato é do SDXL. A aparência mudou: os NPCs passam a ver as veias escuras. |
| 3:05 a 3:25 | Tab: Espelho da Alma | A terceira tela do mockup: os sete pecados, as manifestações e o progresso para cada final. |
| 3:25 a 3:50 | Parar o Ollama (Ctrl+C) e falar com o Odran; aviso de modo offline; o jogo segue | Tratamento de erro da IA em tempo real: se o modelo cair, o jogo avisa e continua com falas simples, sem travar. |
| 3:50 a 4:20 | Veredito, Condenar; tela "Marcado pela Ira" | O fim da sessão: o veredito sobre o Tomás. O final depende dos pecados: Redenção, Marcado, Consumido ou derrota em combate. |
| 4:20 a 4:45 | Terminal: `npm run e2e` passando (pode acelerar) e os resultados do pytest | Os testes automatizados cobrem as mecânicas: 43 do núcleo, 48 da API, 7 do painel e um teste ponta a ponta que joga a partida inteira no navegador. |

Checklist do que **precisa** aparecer:
- [ ] Menu principal
- [ ] Gameplay com HUD
- [ ] M1 a M5 em uso
- [ ] Texto gerado ao vivo
- [ ] Voz tocando
- [ ] Imagens do SDXL
- [ ] Um final
- [ ] Fallback
- [ ] Testes

## Vídeo 2: Front-end, arquitetura da API (alvo de 2 minutos)

O PDF pede um vídeo simples sobre o jogo e a arquitetura. O que é avaliado: rotas, provider, autenticação, CORS e o consumo via requests.

| Tempo | O que mostrar | O que falar |
|---|---|---|
| 0:00 a 0:20 | Diagrama do README (jogo → API → Ollama e Piper) | Na CP4 o jogo chamava o Ollama direto. Agora o jogo e o painel chamam a API do grupo, e só a API fala com o Ollama (texto) e com o Piper (voz). |
| 0:20 a 0:50 | VS Code: `api/routers/ia_generativa.py` e `api/providers/ia_provider.py` lado a lado; `main.py` com CORS | Padrão rota e provider: o router só recebe e valida; o provider é o único arquivo que conhece o Ollama e o Piper. O CORS libera o jogo web em localhost:5173. |
| 0:50 a 1:15 | Swagger em /docs; executar GET /status sem chave (401); Authorize com a chave; executar de novo (200) | A autenticação é por API Key no header X-API-Key. Sem a chave, 401. Swagger automático em /docs. |
| 1:15 a 1:40 | Jogo web ao lado do terminal da API; falar com um NPC; destacar as linhas POST no log | A evidência: cada fala do jogo vira uma chamada à nossa API. O navegador nunca chama a porta do Ollama. |
| 1:40 a 2:00 | Painel Streamlit, aba Fala de NPC, Enviar; o áudio toca | O painel consome a mesma API via requests: classifica, gera a fala e a voz. |
| 2:00 a 2:10 | Link do repositório no GitHub | Código do back-end, do jogo e do painel no repositório. |
