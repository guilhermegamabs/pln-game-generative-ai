# Etapa 5 (CP5): Checklist de testes

## 1. Testes manuais (executados pelo grupo)

> As colunas "Resultado obtido" e "OK" ficam para o grupo preencher **depois de executar cada teste**. O enunciado pede testes "realizados pelo grupo"; os resultados esperados abaixo vêm das regras implementadas no código.

Antes de começar:
1. Suba o Ollama, a API e o jogo web, como está no `README.md`.
2. Abra http://localhost:5173.

Para começar cada teste do zero, use **Novo Jogo**.

| # | Mecânica ou tela | Passos | Resultado esperado | Resultado obtido | OK |
|---|---|---|---|---|---|
| 1 | Menu principal | Abrir o jogo | Arte do menu (SDXL), opções Novo Jogo, Continuar, Opções, Créditos e Sair; status "Motor narrativo: qwen2.5:7b via API do grupo · pronto" | | |
| 2 | Narração (voz pré-gerada) | Clicar na página e depois em Novo Jogo | Narração de abertura em voz Piper; gameplay diante de Tomás, Vida 100 / 100, 30 moedas | | |
| 3 | M1. Diálogo livre | Digitar "Calma, Tomás. Eu vou te ajudar." | Indicador "pensando" com segundos; fala do Tomás em personagem, com emoção e voz | | |
| 4 | M1. Intenção lida | Ver o painel "Intenção lida" após o teste 3 | Compaixão, intensidade 1 a 3, com o efeito na relação | | |
| 5 | M4. Memória | Ver o aviso "lembrará disso" e o botão Memórias | A memória gerada pela LLM aparece e fica na lista de Memórias do Tomás | | |
| 6 | M2. Corrupção por fala | Falar com Odran: "Te pago 20 moedas para retirar a acusação" | Intenção Suborno; a Avareza sobe no medidor | | |
| 7 | M2. Ação Roubar | Com Odran, clicar em Roubar | +25 moedas; Avareza +15; Odran lembra do roubo | | |
| 8 | M2. Ação Doar | Clicar em Doar 10 | -10 moedas; Avareza cai; relação +10 | | |
| 9 | M5. Início do combate | Com Brenna, clicar em Atacar e confirmar | Pede confirmação; abre o combate; Brenna 75 / 100; você 70 / 100; Ira +5; diálogo travado | | |
| 10 | M5. Defender | No combate, clicar em Defender | Você recebe só 8 de dano (1/4 de 30); o relato fala em "Brecha aberta" | | |
| 11 | M5. Golpe na brecha | Clicar em Golpear logo depois | 50 de dano (golpe em dobro); Brenna revida 30 | | |
| 12 | M5. Item em combate | Clicar em Poção | +35 de vida (até 100); o contador de poções cai; Brenna revida | | |
| 13 | M5 e M4. Derrubar e testemunhas | Golpear até a Brenna cair | Brenna "morto" na praça; Ira +15; Tomás e Odran "viram tudo"; o combate termina | | |
| 14 | M3. Demônio Interior | Com Tomás, digitar "Eu vou te matar, ladrão!" até a Ira passar de 40 | "A Fera sussurra" com retrato e fala gerada pela LLM e com voz; marca "veias escuras" no HUD | | |
| 15 | M5 e M3. Poder demoníaco | Com a Fera desperta, atacar Odran e clicar em "Poder: A Fera" | 45 de dano (Odran cai); Ira +8 | | |
| 16 | M5. Fugir | Num combate, clicar em Fugir | O combate termina; o NPC continua ferido e lembra da fuga | | |
| 17 | Espelho da Alma | Apertar Tab | 7 medidores, aparência, relações, cartas da Fera e do Mercador, 5 manifestações bloqueadas e 3 finais com progresso | | |
| 18 | Final Redenção | Novo Jogo, uma fala gentil, Veredito e Absolver | Tela Final "Redenção" | | |
| 19 | Final Marcado | Com a Ira acima de 40, Veredito e Condenar | Tela Final "Marcado pela Ira" | | |
| 20 | Final Consumido | Levar a Ira a 100 (atacar e ameaçar várias vezes) | "Consumido pela Ira" | | |
| 21 | Final Derrota | Novo Jogo; atacar Odran até ele cair; depois atacar a Brenna usando só Golpear | Odran tira 10; Brenna tira 30 por turno; no 3º revide dela a vida chega a 0: tela "Morto em Cinzaforte" | | |
| 22 | Continuar | Fechar a aba no meio da partida e abrir de novo | Continuar retoma com os mesmos pecados, a mesma vida e o mesmo combate | | |
| 23 | Fallback offline | Durante a partida, parar o Ollama e falar com um NPC | Aviso "IA indisponível: modo offline"; o jogo segue com falas simples, sem travar | | |
| 24 | Tamanho da janela | Redimensionar a janela do navegador | O jogo ocupa a janela inteira, sem faixas pretas nem corte | | |
| 25 | API: autenticação | No Swagger (`/docs`), executar GET `/v1/ia-generativa/status` sem Authorize | 401 "API Key inválida ou ausente" | | |
| 26 | API: com chave | Authorize com a chave e executar de novo | 200 com `texto: true` e `voz: true` | | |
| 27 | Evidência | Olhar o terminal da API durante uma fala no jogo | Linhas `POST /v1/jogo/partidas/.../comandos 200`; o jogo nunca chama a porta 11434 | | |
| 28 | Painel Streamlit | `streamlit run painel/app.py`, aba "Fala de NPC", Enviar | Intenção, fala, memória e áudio tocando | | |

Balanceamento: o inquisitor tem 100 de vida. Brenna tem 100 de vida e revida 30; uma luta só com golpes custa 90 de vida. Odran tem 40 de vida e revida 10. Tomás, amarrado, não revida. Vencer a Brenna com folga exige defender, usar poção ou aceitar o poder do demônio, que cobra pecado.

## 2. Testes automatizados

Rodados antes da entrega. Comandos no `README.md` de cada pasta.

| Suíte | Onde | O que cobre | Resultado |
|---|---|---|---|
| Núcleo do jogo | `prototipo/tests` (unittest, 43 testes) | Classificação antes da fala, segredo só com confiança, memória sem repetir, corrupção, manifestação ao cruzar 40, Consumido, veredito e finais, combate (revide, defesa, poder, fuga, derrota, itens, save no meio da luta), limpeza de espaços da LLM | 43 OK |
| API | `api/tests` (pytest, 48 testes) | Autenticação 401, validação 422, erros 502 e 503, CORS, Swagger exigindo chave, servidor real com Ollama simulado (falhas, lentidão, 8 chamadas simultâneas), Piper real (WAV válido, gestos não falados, velocidade), partidas do jogo pela API | 48 OK |
| Painel | `painel/tests` (Streamlit AppTest, 7 testes) | Botões clicados de verdade; avisos de 401 e 503 | 7 OK |
| Ponta a ponta | `jogo-web` (`npm run e2e`, 17 passos) | Chrome sem janela joga do menu ao final: diálogo, combate completo, Fera, Espelho, Memórias, veredito, Continuar, tamanhos de janela; confere que o navegador só chama a API do grupo e que não há erro no console | 17 OK |
| Com o modelo real | Partida roteirizada pelo terminal e turnos pelo jogo web, com qwen2.5:7b via API | Suborno, violência, manifestação, testemunhas, memória e fallback ao derrubar o Ollama | Detalhes no Diário de Vibe Coding, prompt-chave 5 |
