# Roteiro do vídeo da CP5

**Um vídeo único, de 5 minutos, para as duas disciplinas.** O PLN pede de 2 a 5 minutos com o MVP em execução; o Front-end pede "um vídeo simples para explicar um pouco do jogo e da arquitetura". A parte de arquitetura (bloco 7) é anunciada em voz alta, para o professor de Front-end achar o trecho dele.

As falas abaixo são **sugestões**: fale com as suas palavras.

## Antes de gravar

- [ ] Gravar na máquina com GPU (cada fala leva uns 5 s; no notebook sem GPU leva de 1 a 2 minutos).
- [ ] Ollama, API e jogo no ar; três terminais, como no `README.md`.
- [ ] Navegador em tela cheia (F11), 1920x1080, **voz ligada**.
- [ ] Começar do zero: **Novo Jogo**.
- [ ] Terminal da API visível ao lado do navegador nos blocos 6 e 7.
- [ ] **Não deixar a chave de API aparecer na tela** (nem o `.env`, nem o `.env.local`).
- [ ] VS Code já aberto nos arquivos `api/routers/ia_generativa.py`, `api/providers/ia_provider.py` e `api/main.py`.

---

## Bloco 1 — Abertura (0:00 a 0:30)

**Mostrar:** tela de menu, com a arte de fundo e o status "qwen2.5:7b via API do grupo · pronto".

**Falar:**
- Nome do jogo, integrantes e RMs.
- "RPG narrativo de fantasia sombria; é a implementação do jogo que a gente desenhou na CP4."
- "A arte do menu foi gerada com Stable Diffusion XL, ainda na CP4."
- "Stack: React com TypeScript no front, FastAPI no back, Ollama para texto e Piper para voz. É a mesma stack que a CP4 previu."

## Bloco 2 — Diálogo livre, a mecânica central (0:30 a 1:15)

**Mostrar:** clicar em **Novo Jogo**; a narração de abertura tocando; digitar para o Tomás: *"Calma, Tomás. Ninguém vai te machucar enquanto eu estiver aqui."*; o indicador "pensando"; a resposta com voz; os painéis **Intenção lida** e **Memória**.

**Falar:**
- "Essa narração é voz gerada pelo Piper, rodando local."
- "Mecânica 1, diálogo livre: eu escrevo o que quiser, não escolho de uma lista."
- "O turno faz duas chamadas à LLM: primeiro ela só classifica a intenção, aqui compaixão, depois o Tomás responde em personagem."
- "Separamos as duas porque, quando pedíamos tudo junto, a classificação errava mais."
- "Mecânica 4: o NPC guarda uma memória do que aconteceu, e ela entra nos próximos turnos."

## Bloco 3 — Corrupção (1:15 a 1:45)

**Mostrar:** clicar no **Odran**; digitar *"Te pago 20 moedas para você retirar a acusação."*; o medidor de **Avareza** subindo no painel da direita.

**Falar:**
- "Mecânica 2: cada escolha alimenta um dos sete pecados."
- "A IA só lê a intenção. **Quanto** o pecado sobe é regra fixa no código, então o modelo não inventa progressão e o balanceamento é testável."

## Bloco 4 — Combate (1:45 a 2:40)

**Mostrar:** ir até a **Brenna**, ameaçar, clicar em **Atacar** e confirmar; usar **Defender**, depois **Golpear**, depois **Poção**; o golpe final; as linhas "Tomás viu tudo" e "Odran viu tudo".

**Falar:**
- "Mecânica 5, combate por turnos, com as quatro ações da CP4: golpear, defender, item e poder."
- "Defender reduz o dano e abre uma brecha para o próximo golpe sair em dobro."
- "Quando a Brenna cai, as testemunhas registram. A relação delas despenca, e isso muda como elas falam comigo depois."

## Bloco 5 — Demônio Interior e Espelho da Alma (2:40 a 3:20)

**Mostrar:** atacar o Odran até a **Ira passar de 40**; o alerta **"A Fera sussurra"**, com retrato e voz; as marcas de corrupção aparecendo no HUD; apertar **Tab** para abrir o Espelho da Alma; mostrar o botão **Poder demoníaco** agora habilitado.

**Falar:**
- "Mecânica 3: passando de 40 numa corrupção, a manifestação desperta."
- "A fala dela é gerada pela LLM na hora, a voz é do Piper e o retrato é do SDXL. As três modalidades de IA no mesmo momento."
- "Agora o HUD mostra marcas no personagem, e o poder demoníaco ficou disponível: dá mais dano, mas alimenta a Ira."
- "Terceira tela do mockup: o Espelho da Alma, com os sete pecados e o progresso para cada final."

## Bloco 6 — Tratamento de erro da IA (3:20 a 3:45)

**Mostrar:** no terminal do Ollama, apertar **Ctrl+C**; voltar ao jogo e falar com um NPC; o aviso de modo offline; o jogo continuando.

**Falar:**
- "Se a IA cair no meio da partida, o jogo avisa e continua com respostas simples, em vez de travar."
- "As regras de pecado seguem iguais, porque elas estão no código, não na IA."

> Religue o Ollama depois (`ollama serve`), para o bloco 7 ter o modelo no ar.

## Bloco 7 — Arquitetura, a parte de Front-end (3:45 a 4:40)

**Diga em voz alta:** *"Agora a parte da disciplina de Front-end: a arquitetura da API."*

**Mostrar, nesta ordem:**
1. O diagrama do `README.md` (jogo → API → Ollama e Piper).
2. No VS Code: `api/routers/ia_generativa.py` e `api/providers/ia_provider.py` lado a lado; depois `api/main.py`, na parte do CORS.
3. O Swagger em `http://localhost:8000/docs`: executar uma rota **sem chave** (resposta **401**), clicar em **Authorize**, colar a chave fora da tela e executar de novo (**200**).
4. O jogo ao lado do terminal da API: mandar uma fala e mostrar as linhas `POST /v1/jogo/.../comandos` e `POST /v1/ia-generativa/voz` aparecendo no log.

**Falar:**
- "Na CP4 o jogo chamava o Ollama direto. Agora ele chama só a nossa API, e só ela fala com o Ollama e com o Piper."
- "Padrão rota e provider: o router recebe e valida; o provider é o único arquivo que conhece os serviços de IA."
- "As rotas de IA são protegidas por API Key no header X-API-Key. Sem a chave, 401."
- "O CORS libera só a origem do jogo, em localhost:5173."
- "Essa é a evidência que o enunciado pede: cada fala do jogo vira uma chamada à nossa API, e o navegador nunca fala com a porta do Ollama."

## Bloco 8 — Painel, final e fechamento (4:40 a 5:00)

**Mostrar:** o painel **Streamlit** mandando uma fala e tocando o áudio; voltar ao jogo e usar o **Veredito** para encerrar; a tela de final; por último, o repositório no GitHub.

**Falar:**
- "O painel consome a mesma API via requests, só para testar as rotas fora do jogo."
- "O fim de sessão é o veredito sobre o Tomás; o final depende dos pecados acumulados."
- "Código do jogo, da API e do painel no repositório, com README de como rodar."

---

## Checklist do que **precisa** aparecer

**PLN**
- [ ] Menu principal
- [ ] Gameplay com HUD
- [ ] 3 ou mais mecânicas (temos 5: diálogo, corrupção, demônio, memória, combate)
- [ ] Texto gerado ao vivo
- [ ] Voz tocando
- [ ] Imagens do SDXL
- [ ] Um final (começo, meio e fim)

**Pontos extras**
- [ ] Fallback quando a IA cai
- [ ] Testes automatizados (pode entrar no fim, acelerado)
- [ ] Mais de uma modalidade de IA integrada (texto, voz e imagem)

**Front-end**
- [ ] Router e provider no editor
- [ ] Swagger em /docs
- [ ] 401 sem chave e 200 com chave
- [ ] CORS
- [ ] Log da API enquanto o jogo roda
- [ ] Painel consumindo via requests
- [ ] Link do repositório

## Se faltar tempo

Corte, nesta ordem: o painel Streamlit (bloco 8), o Espelho da Alma (bloco 5) e os testes. **Nunca corte** o fallback nem o bloco 7, porque são o ponto extra e a disciplina inteira de Front-end.
