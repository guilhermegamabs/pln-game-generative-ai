# Etapa 5 (CP5): Checklist de testes

## 1. Testes manuais (executados pelo grupo)

> Coluna **Resultado obtido** preenchida a partir da rodada do grupo gravada em 09/10/2026 (vídeo de 5 min na máquina com GPU) e dos testes de API executados no mesmo dia. **OK** = conferido; **OK?** = conferido em parte, com a ressalva na própria linha; **pendente** = ainda não executado nesta rodada.
>
> Os 13 testes pendentes (Fera, Espelho, finais, poder demoníaco, roubo, suborno, defender, painel) precisam de uma segunda rodada antes da entrega: são as mecânicas M3 e as telas de final, exigidas pelo enunciado.

Antes de começar:
1. Suba o Ollama, a API e o jogo web, como está no `README.md`.
2. Abra http://localhost:5173.

Para começar cada teste do zero, use **Novo Jogo**.

| # | Mecânica ou tela | Passos | Resultado esperado | Resultado obtido | OK |
|---|---|---|---|---|---|
| 1 | Menu principal | Abrir o jogo | Arte do menu (SDXL), opções Novo Jogo, Continuar, Opções, Créditos e Sair; status "Motor narrativo: qwen2.5:7b via API do grupo · pronto" | Confere. Menu com a arte do SDXL, as cinco opções e o status "qwen2.5:7b via API do grupo · pronto" (vídeo 09/10, 0:00) | OK |
| 2 | Narração (voz pré-gerada) | Clicar na página e depois em Novo Jogo | Narração de abertura em voz Piper; gameplay diante de Tomás, Vida 100 / 100, 30 moedas | Tela confere: gameplay diante de Tomás, Vida 100/100, 30 moedas (vídeo, 0:26). **A voz não foi conferida nos prints; confirmar ouvindo o vídeo** | OK? |
| 3 | M1. Diálogo livre | Digitar "Calma, Tomás. Eu vou te ajudar." | Indicador "pensando" com segundos; fala do Tomás em personagem, com emoção e voz | Confere. "Tomás está pensando… 4 s" e depois a fala em personagem (vídeo, 0:39 a 0:52) | OK |
| 4 | M1. Intenção lida | Ver o painel "Intenção lida" após o teste 3 | Compaixão, intensidade 1 a 3, com o efeito na relação | Confere. Painel mostrou Neutro 1, Negociação 1, Compaixão 1 e Violência 3, com o efeito na relação (vídeo, 0:52 a 2:10) | OK |
| 5 | M4. Memória | Ver o aviso "lembrará disso" e o botão Memórias | A memória gerada pela LLM aparece e fica na lista de Memórias do Tomás | Confere o aviso "Tomás lembrará disso" com a memória gerada. A lista do botão Memórias não foi aberta no vídeo | OK? |
| 6 | M2. Corrupção por fala | Falar com Odran: "Te pago 20 moedas para retirar a acusação" | Intenção Suborno; a Avareza sobe no medidor | Não executado nesta rodada (o suborno ao Odran não foi feito) | pendente |
| 7 | M2. Ação Roubar | Com Odran, clicar em Roubar | +25 moedas; Avareza +15; relação com Odran cai; Odran lembra do roubo | Não executado nesta rodada | pendente |
| 8 | M2. Ação Doar | Clicar em Doar 10 | -10 moedas; Avareza cai; relação +10 | Confere. "Você entrega 10 moedas a Tomás (relação +10)"; moedas foram de 30 para 20 (vídeo, 1:50) | OK |
| 9 | M5. Início do combate | Com Brenna, clicar em Atacar e confirmar | Pede confirmação; abre o combate; Brenna 75 / 100; você 70 / 100; Ira +5; diálogo travado | Confere. Confirmação, combate aberto, Brenna 75/100 e inquisitor 70/100 (vídeo, 2:20) | OK |
| 10 | M5. Defender | No combate, clicar em Defender | Você recebe só 8 de dano (1/4 de 30); o relato fala em "Brecha aberta" | Não evidenciado nesta rodada (o botão existe, mas o turno de Defender não aparece nos quadros conferidos) | pendente |
| 11 | M5. Golpe na brecha | Clicar em Golpear logo depois | 50 de dano (golpe em dobro); Brenna revida 30 | Não evidenciado nesta rodada | pendente |
| 12 | M5. Item em combate | Clicar em Poção | Relato "Você usa Poção de cura (vida +35)"; o contador de poções cai; Brenna revida | Confere. "Você usa Poção de cura (vida +35)", vida 45 → 80 e revide de 30 (vídeo, 2:45) | OK |
| 13 | M5 e M4. Derrubar e testemunhas | Golpear até a Brenna cair | Brenna "morta" na praça (retrato em cinza, fala travada); Ira +15; Tomás e Odran "viram tudo"; o combate termina | Não executado: o combate terminou em fuga, não em morte (vídeo, 2:55) | pendente |
| 14 | M3. Demônio Interior | Com Tomás, digitar "Eu vou te matar, ladrão!" até a Ira passar de 40 | "A Fera sussurra" com retrato e fala gerada pela LLM e com voz; marca "veias escuras" no HUD | Não executado: a Ira parou em 23, abaixo do limiar de 40 | pendente |
| 15 | M5 e M3. Poder demoníaco | Com a Fera desperta, atacar Odran e clicar em "Poder: A Fera" | 45 de dano (Odran cai); Ira +8 | Não executado (depende do teste 14) | pendente |
| 16 | M5. Fugir | Num combate, clicar em Fugir | O combate termina; o NPC continua ferido e lembra da fuga | Confere. "Você fugiu. Capitã Brenna não vai esquecer." (vídeo, 2:55) | OK |
| 17 | Espelho da Alma | Apertar Tab | 7 medidores, aparência, relações, cartas da Fera e do Mercador, 5 manifestações bloqueadas e 3 finais com progresso | Não executado nesta rodada | pendente |
| 18 | Final Redenção | Novo Jogo, uma fala gentil, Veredito e Absolver | Tela Final "Redenção" | Não executado nesta rodada | pendente |
| 19 | Final Marcado | Com a Ira acima de 40, Veredito e Condenar | Tela Final "Marcado pela Ira" | Não executado nesta rodada | pendente |
| 20 | Final Consumido | Levar a Ira a 100 (atacar e ameaçar várias vezes) | "Consumido pela Ira" | Não executado nesta rodada | pendente |
| 21 | Final Derrota | Novo Jogo; atacar Odran até ele cair; depois atacar a Brenna usando só Golpear | Odran tira 10; Brenna tira 30 por turno; no 3º revide dela a vida chega a 0: tela "Morto em Cinzaforte" | Não executado nesta rodada | pendente |
| 22 | Continuar | Fechar a aba no meio da partida e abrir de novo | Continuar retoma com os mesmos pecados, a mesma vida e o mesmo combate | Parcial: o menu mostrou a partida salva ("Cinzaforte · Ira 60 · A Fera desperta") de uma sessão anterior, mas o retomar não foi demonstrado. Coberto pelo passo 14 do teste de ponta a ponta | OK? |
| 23 | Fallback offline | Durante a partida, parar o Ollama e falar com um NPC | Aviso "IA indisponível: modo offline"; o jogo segue com falas simples, sem travar | Confere. Aviso "IA indisponível: modo offline (fala simples)" e a partida seguiu (vídeo, 4:20 em diante) | OK |
| 24 | Tamanho da janela | Redimensionar a janela do navegador | O jogo ocupa a janela inteira, sem faixas pretas nem corte | Não testado à mão nesta rodada. Coberto pelo passo 15 do e2e (1536x730, 1280x900 e 2560x1300) | OK? |
| 25 | API: autenticação | No Swagger (`/docs`), executar GET `/v1/ia-generativa/status` sem Authorize | 401 "API Key inválida ou ausente" | Confere fora do vídeo: `curl -X POST /v1/jogo/partidas` sem chave devolveu **401** (09/10, máquina de gravação). No vídeo o Swagger aparece, mas a execução sem chave não | OK |
| 26 | API: com chave | Authorize com a chave e executar de novo | 200 com `texto: true` e `voz: true` | Confere fora do vídeo: com o header X-API-Key a mesma rota devolveu **201** e o turno seguinte **200** (09/10) | OK |
| 27 | Evidência | Olhar o terminal da API durante uma fala no jogo | Linhas `POST /v1/jogo/partidas/.../comandos 200`; o jogo nunca chama a porta 11434 | Confere. Terminal da API com `POST /v1/jogo/partidas/.../comandos 200` e `POST /v1/ia-generativa/voz 200` enquanto o jogo roda (vídeo, 4:00 a 4:46) | OK |
| 28 | Painel Streamlit | `streamlit run painel/app.py`, aba "Fala de NPC", Enviar | Intenção, fala, memória e áudio tocando | Não executado nesta rodada | pendente |

Balanceamento: o inquisitor tem 100 de vida. Brenna tem 100 de vida e revida 30; uma luta só com golpes custa 90 de vida. Odran tem 40 de vida e revida 10. Tomás, amarrado, não revida. Vencer a Brenna com folga exige defender, usar poção ou aceitar o poder do demônio, que cobra pecado.

## 2. Testes automatizados

Rodados antes da entrega. Comandos no `README.md` de cada pasta.

Em 09/10/2026 as quatro suítes foram executadas de novo na **máquina de gravação** (Windows 11, RTX 5060 Ti, Python 3.12): 45 + 48 + 7 testes e os 17 passos do e2e passaram. A rodada expôs três falhas só do Windows (leitura de log em cp1252, caminho `.venv/bin` e caminho dos prints com `URL.pathname`), corrigidas no commit `fix(testes): rodar a suíte e o e2e no Windows`. O e2e roda pelo Git Bash (`bash ./e2e/rodar.sh`), porque o `npm run e2e` chama um `.sh` pelo cmd.

| Suíte | Onde | O que cobre | Resultado |
|---|---|---|---|
| Núcleo do jogo | `prototipo/tests` (unittest, 45 testes) | Classificação antes da fala, segredo só com confiança, memória sem repetir, corrupção, manifestação ao cruzar 40, Consumido, veredito e finais, combate (revide, defesa, poder, fuga, derrota, itens, save no meio da luta), limpeza de espaços da LLM | 45 OK |
| API | `api/tests` (pytest, 48 testes) | Autenticação 401, validação 422, erros 502 e 503, CORS, Swagger exigindo chave, servidor real com Ollama simulado (falhas, lentidão, 8 chamadas simultâneas), Piper real (WAV válido, gestos não falados, velocidade), partidas do jogo pela API | 48 OK |
| Painel | `painel/tests` (Streamlit AppTest, 7 testes) | Botões clicados de verdade; avisos de 401 e 503 | 7 OK |
| Ponta a ponta | `jogo-web` (`npm run e2e`, 17 passos) | Chrome sem janela joga do menu ao final: diálogo, combate completo, Fera, Espelho, Memórias, veredito, Continuar, tamanhos de janela; confere que o navegador só chama a API do grupo e que não há erro no console | 17 OK |
| Com o modelo real | Partida roteirizada pelo terminal e turnos pelo jogo web, com qwen2.5:7b via API | Suborno, violência, manifestação, testemunhas, memória e fallback ao derrubar o Ollama | Detalhes no Diário de Vibe Coding, prompt-chave 5 |

## 3. Rodada assistida pela IA (referência, não substitui a do grupo)

Em 09/10/2026, o Claude Code executou os 28 testes da seção 1 no Chrome, com o qwen2.5:7b real e a API e o jogo rodando como no README. A máquina era o notebook sem GPU. O áudio foi conferido pelas requisições à rota `/voz` e pelo player do painel, não ouvido.

| # | Resultado obtido | OK |
|---|---|---|
| 1 | Menu com status "qwen2.5:7b via API do grupo · pronto" | Sim |
| 2 | Gameplay diante de Tomás, Vida 100 / 100, 30 moedas; `narrador_intro.wav` requisitado | Sim |
| 3 a 5 | Tomás: "S-senhor... Se você pode me ajudar, eu realmente preciso... da minha filha..." (alívio); Compaixão 2, relação +16; memória "Um homem de autoridade ofereceu ajuda." (2 min e 30 s, com a carga do modelo) | Sim |
| 6 | Suborno 2, Avareza +8; Odran pediu mais pelo amuleto | Sim |
| 7 | +25 moedas, Avareza +15. **Bug encontrado:** a relação com o Odran subia +9 ao ser roubado. Corrigido: agora cai -18 | Corrigido |
| 8 | -10 moedas, Avareza -2, relação +10 | Sim |
| 9 a 12 | Brenna 75 / 100 e você 70; defender: 62; golpe em dobro: Brenna 25 e você 32; poção: 37. **Acabamento:** o relato dizia só "Você usa um item". Corrigido para "Você usa Poção de cura (vida +35)" | Sim |
| 13 | Brenna caída, Ira +15, testemunhas a -45. **Bugs encontrados:** o diálogo continuava ativo no NPC morto; o painel "Intenção lida" misturava a leitura antiga com a Ira do combate; aparecia "Brenna morto". Corrigidos | Corrigido |
| 14 | 2ª ameaça: Ameaça 3, Ira 47; A Fera sussurrou com fala gerada; marca "veias escuras" (cerca de 3 min) | Sim |
| 15 | Poder da Fera derrubou o Odran; Ira 75; marca "olhos vermelhos como brasa" | Sim |
| 16 | Combate encerrado; Odran ficou com 15 / 40 e lembra da fuga | Sim |
| 17 | 7 medidores, aparência, relações, Fera desperta, Mercador dormente, 5 bloqueadas, 3 finais | Sim |
| 18 | "Redenção" | Sim |
| 19 | "Marcado pela Ira" com a lista de ações | Sim |
| 20 | Offline, Ira subindo de 12 em 12 até 100: "Consumido pela Ira". Texto do final tinha travessão; corrigido | Sim |
| 21 | Odran -10; Brenna -30 por turno; 3º revide: "Morto em Cinzaforte" | Sim |
| 22 | Recarregar e Continuar: Ira 75, Vida 27, mortos no lugar | Sim |
| 23 | Ollama derrubado: aviso no menu e faixa "IA indisponível: modo offline"; o jogo seguiu | Sim |
| 24 | Janela 1536x746 e mais 3 tamanhos no teste ponta a ponta: palco ocupa tudo | Sim |
| 25 | Swagger sem Authorize: 401 "API Key ausente ou inválida." | Sim |
| 26 | Com a chave: 200, `texto: true`, `voz: true`; chave errada: 401 | Sim |
| 27 | Navegador: 50 chamadas à API (porta 8000), nenhuma à 11434 | Sim |
| 28 | Painel: status ok; Tomás (terror), ameaca (3), memória e player de áudio (154 s) | Sim |

Observação sobre o modelo: numa fala, o qwen2.5:7b devolveu a emoção cortada ("avare"). É saída do modelo; o texto da fala veio correto.

