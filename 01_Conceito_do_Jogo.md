# Etapa 1 — Conceito do Jogo (Game Design)

> Status: **proposta v1** — validar com o grupo antes de consolidar no relatório final.
> Base: `Relatorio_OS_7_Pecados.pdf` (pitch original do grupo).
> Itens exigidos pela seção 4 / Etapa 1 do enunciado estão marcados com ✅.

---

## 1. Título e gênero ✅

**Título:** OS 7 PECADOS
**Tagline:** *"Você não enfrenta os pecados. Você decide qual deles vai se tornar você."*
**Gênero:** RPG narrativo de fantasia sombria, com combate por turnos simples e diálogo livre com NPCs movido por LLM.

## 2. Plataforma-alvo ✅

**PC (Windows), single-player, offline-first.**

Justificativa:
- O diálogo livre exige digitação (teclado), o que favorece PC em vez de mobile/console.
- Permite rodar a LLM **localmente** (Ollama + modelo pequeno, ex.: Llama 3.2 3B) em máquinas comuns, sem custo de API por jogador — atende ao alerta do professor sobre limitação de hardware.
- Modo alternativo previsto: LLM via API (maior qualidade, exige internet e tem custo) configurável nas opções.

## 3. Premissa ✅ (1 parágrafo)

Manifestações sobrenaturais dos sete pecados capitais — Ira, Avareza, Inveja, Preguiça, Luxúria, Gula e Orgulho — tomaram as regiões do reino, cada uma deformando sua sociedade à imagem do pecado que a domina. O protagonista, um inquisitor enviado para investigar e purificar esses territórios, descobre que o poder necessário para enfrentar os pecados vem deles próprios: cada violência, cada barganha desonesta, cada gesto de superioridade alimenta um demônio dentro dele. Ao longo da jornada, os habitantes lembram do que ele fez, reagem ao que ele está se tornando, e o jogador precisa decidir se vai salvar o mundo como um homem ou como o próximo pecado.

## 4. Público-alvo e classificação indicativa ✅

| Item | Definição |
|---|---|
| Público principal | Jogadores a partir de 16 anos que gostam de RPGs narrativos e escolhas com consequência (fãs de Disco Elysium, The Witcher, Fable) |
| Público secundário | Interessados em experiências com IA/narrativa emergente |
| Classificação indicativa (ClassInd) | **16 anos** — violência, temas religiosos/sobrenaturais sombrios, manipulação psicológica, linguagem imprópria moderada |
| Moderação de conteúdo | Prompt de sistema da LLM com limites de conteúdo (sem sexo explícito, sem discurso de ódio), coerente com a classificação |

## 5. Mecânicas principais ✅ (mínimo 3)

### M1 — Diálogo livre com NPCs (motor de interação via LLM)
O jogador **digita** o que quer dizer ou fazer. Cada NPC tem uma ficha (personalidade, objetivos, segredos, relação com o jogador) e uma **memória de eventos**. A LLM gera a fala do NPC em personagem e, em paralelo, retorna uma **classificação estruturada (JSON)** da intenção do jogador (ex.: ameaça, suborno, compaixão, mentira). Opções rápidas sugeridas também aparecem para quem não quiser digitar.

### M2 — Sistema de Corrupção (7 medidores de pecado)
O jogador **não escolhe** o pecado. O jogo lê o comportamento: a intenção classificada em M1 e as ações no mundo (roubar, matar, poupar, ceder) somam ou subtraem pontos em 7 medidores (0–100). A regra de pontuação é **determinística no código**; a LLM apenas classifica a intenção — isso evita que a IA "invente" progressão e mantém o balanceamento controlável.

### M3 — Demônio Interior (poderes com preço)
Ao passar de um limiar (ex.: 40 pontos), o pecado se manifesta como entidade (A Fera, O Mercador, O Reflexo...) e oferece um poder. Aceitar o poder facilita combates e diálogos, mas **acelera a corrupção**. A entidade também "fala" com o jogador (voz interior gerada pela LLM + TTS).

### M4 — Memória e Reputação
Eventos importantes ficam registrados (ajudou, traiu, ameaçou, matou). NPCs e facções consultam essa memória: portas se abrem ou se fecham, preços mudam, testemunhas espalham boatos. Pecados altos também alteram a **aparência** do protagonista e o tom de como o mundo o trata.

### M5 — Combate por turnos simples
Confrontos com criaturas e com as manifestações usam combate por turnos (atacar, defender, usar item, usar poder demoníaco). Mantido propositalmente simples: o foco do jogo é narrativo.

## 6. Objetivo do jogador ✅

- **Progresso:** investigar a região, descobrir a origem da manifestação e confrontá-la (por combate, negociação ou sacrifício).
- **Vitória (campanha):** purificar as regiões e chegar ao confronto final. **Qual final** o jogador alcança depende da combinação de medidores de corrupção, relações e decisões-chave:
  - **Redenção** — todos os medidores abaixo do limiar no confronto final.
  - **Consumido** — algum medidor chega a 100: o protagonista vira a nova manifestação (game over narrativo).
  - **Finais de pecado** — pecado dominante no fim define o desfecho (Ira, Avareza, Orgulho, Inveja...).
  - **O Oitavo Pecado** — final secreto ligado a equilíbrio entre vários pecados altos.
- **No MVP (CP5):** 1 região, derrotar/resolver a manifestação local, com pelo menos 2 finais (Redenção vs. Consumido pela Ira/Avareza).

## 7. Jogos de referência ✅ (mínimo 2)

| Jogo | O que inspira | Comparação |
|---|---|---|
| **Disco Elysium** (ZA/UM, 2019) | Vozes internas que falam com o protagonista; diálogo como gameplay principal | Nosso "Demônio Interior" é equivalente às habilidades-personagem de Disco Elysium, mas cada voz é um pecado e as falas são geradas dinamicamente |
| **Fable** (Lionhead, 2004) | Moralidade que altera aparência e reação dos NPCs | Fable usa eixo bem/mal; nós usamos 7 eixos independentes e detectados pelo comportamento, não por escolhas binárias |
| **Darkest Dungeon** (Red Hook, 2016) | Estética de fantasia sombria; aflições que dão bônus e custos | Aflições de estresse ≈ nossas manifestações: poder que cobra preço |
| **AI Dungeon** (Latitude, 2019) | Narrativa gerada por LLM a partir de texto livre | Mostra o potencial e o problema (caos, incoerência). Nós restringimos a LLM com fichas de NPC, memória e regras determinísticas de jogo |

## 8. Loop de gameplay (resumo)

```
Explorar região → Encontrar situação/NPC → Dialogar (texto livre / LLM)
      ↑                                              ↓
Consequências no mundo  ←  Corrupção + Memória ← Classificar intenção/ação
(reputação, poderes,                                 ↓
 aparência, finais)                    Combate/decisão quando necessário
```

## 9. Exemplo de cena (referência para POC e mockup)

**Local:** praça da cidade de Ira. **Situação:** homem acusado de roubo, cercado por uma multidão.

| Jogador digita | Intenção (LLM) | Efeito |
|---|---|---|
| "Solta ele ou quebro seus dentes." | ameaça / violência | Ira +8, multidão hostil |
| "Quanto vale o que ele roubou? Eu pago." | negociação | Avareza +0, reputação +5 com o acusado |
| "Me conta a verdade e eu te ajudo." | compaixão | Redução leve de Ira, NPC revela pista |
| *(ataca o homem)* | ação: matar | Ira +20, testemunhas registram o evento |
