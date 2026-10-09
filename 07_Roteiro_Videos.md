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

---

# Falas completas, bloco a bloco

Texto corrido para ler em voz alta (ou adaptar). O tempo entre parênteses é o de fala; o resto do bloco é o jogo respondendo. Fale devagar: cada bloco abaixo leva de 20 a 40 segundos.

## Bloco 1 — Abertura (~25 s de fala)

> "Oi, somos o Guilherme e o Igor, RM565293 e RM563632. Este é o **OS 7 PECADOS**, o MVP da CP5, que implementa o jogo que a gente desenhou na CP4: um RPG narrativo de fantasia sombria em que o jogador é um inquisitor que investiga pecados e acaba corrompido por eles.
>
> Essa arte de fundo foi gerada na CP4 com Stable Diffusion XL, rodando local.
>
> A stack é a que a CP4 previu: React com TypeScript no front, FastAPI no back, e a IA toda local: o Ollama com o qwen 2.5 de 7 bilhões de parâmetros para texto, e o Piper para voz. Aqui no menu o jogo já mostra que o modelo está carregado e pronto."

## Bloco 2 — Diálogo livre (~35 s de fala)

> "Vou começar uma partida nova. Essa narração que está tocando é voz gerada pelo Piper, não é áudio gravado por ninguém.
>
> A cena é a Praça do Pelourinho: o Tomás foi acusado de roubar um amuleto e a Capitã Brenna quer enforcar ele na hora.
>
> A primeira mecânica é o **diálogo livre**: eu escrevo o que eu quiser, não escolho de uma lista de opções. Vou dizer: 'Calma, Tomás. Ninguém vai te machucar enquanto eu estiver aqui.'
>
> Enquanto ele pensa, explico o que está acontecendo por baixo: cada turno faz duas chamadas à LLM. Na primeira ela só classifica a minha intenção; na segunda o Tomás responde em personagem, já sabendo dessa leitura. A gente separou porque, quando pedia tudo numa chamada só, a classificação errava bem mais.
>
> Olha aqui do lado: ele leu como **compaixão**, intensidade 2, e a relação com o Tomás subiu. E aqui embaixo está a **memória**: o Tomás guardou o que eu fiz, e isso volta nas próximas falas. Essa é a quarta mecânica, memória e reputação."

## Bloco 3 — Corrupção (~25 s de fala)

> "Agora vou falar com o Odran, o mercador. Vou tentar comprar ele: 'Te pago 20 moedas para você retirar a acusação.'
>
> Repara no painel da direita: a **Avareza** subiu. Essa é a segunda mecânica, o sistema de corrupção, que é o coração do jogo.
>
> Um detalhe importante de arquitetura: a IA só lê a intenção. **Quanto** cada pecado sobe é uma tabela fixa no código. Isso foi decisão nossa desde a CP4, porque assim o modelo não inventa progressão, dá para balancear e dá para testar. Tem 45 testes automatizados só nessa parte."

## Bloco 4 — Combate (~30 s de fala)

> "Vou ameaçar a Capitã Brenna e partir para cima. A quinta mecânica é o **combate por turnos**, com as quatro ações que a CP4 descreveu: golpear, defender, usar item e usar o poder demoníaco.
>
> Vou **defender** primeiro: além de reduzir o dano, abre uma brecha e o meu próximo golpe sai em dobro. Agora **golpeio**. Vou usar uma **poção**, que vem do inventário e gasta o turno.
>
> E o golpe final. Olha o que apareceu: 'Tomás viu tudo' e 'Odran viu tudo'. Matar alguém na frente dos outros derruba a relação com quem estava lá, e eles vão me tratar diferente a partir de agora."

## Bloco 5 — Demônio Interior e Espelho (~35 s de fala)

> "A minha Ira passou de 40, e aqui está o momento mais importante do jogo: **A Fera despertou**.
>
> Esse é o Demônio Interior, a terceira mecânica. E repara que tem três IAs acontecendo ao mesmo tempo nesta tela: a fala dela foi gerada agora pela LLM, a voz que você está ouvindo é do Piper, e o retrato foi gerado com Stable Diffusion XL.
>
> Mudou mais coisa: no meu HUD apareceram as marcas de corrupção, que é o que os NPCs passam a enxergar em mim. E o botão **Poder demoníaco**, que estava apagado, agora está disponível: causa mais dano, mas alimenta ainda mais a Ira. É o poder que cobra um preço, como a gente escreveu na CP4.
>
> Aperto Tab e abro o **Espelho da Alma**, a terceira tela do mockup: os sete pecados, as manifestações e para onde a partida está indo."

## Bloco 6 — Tratamento de erro (~20 s de fala)

> "Agora um teste de robustez. Vou **derrubar o Ollama** aqui no terminal, no meio da partida, e tentar falar com um NPC.
>
> O jogo não trava: ele avisa que a IA caiu e continua funcionando com respostas simples. As regras de pecado seguem iguais, porque elas estão no nosso código, não na IA. Isso é o tratamento de erro da IA em tempo real, que o enunciado cita como ponto extra."

## Bloco 7 — Arquitetura, Front-end (~45 s de fala)

> "**Agora começa a parte da disciplina de Front-end: a arquitetura da API.**
>
> Esse é o desenho: o jogo no navegador chama a **nossa API em FastAPI**, e só ela conversa com o Ollama, para texto, e com o Piper, para voz. Na CP4 o jogo chamava o Ollama direto; esse desacoplamento é exatamente o que a CP5 pede.
>
> No código, a gente usou o padrão **rota e provider**: aqui em `routers/ia_generativa.py` ficam as rotas, que só recebem e validam; e aqui em `providers/ia_provider.py` fica a única parte do sistema que conhece o Ollama e o Piper. Se um dia a gente trocar o serviço de IA, muda só esse arquivo.
>
> No `main.py` está o **CORS**, liberando só a origem do jogo, em localhost 5173.
>
> Aqui no **Swagger**, em /docs, vou executar a rota **sem a chave**: dá **401**, não autorizado. Agora clico em Authorize, coloco a chave, e executo de novo: **200**, funcionou. A autenticação é por API Key no header X-API-Key.
>
> E essa é a evidência que o enunciado pede: olha o terminal da API enquanto eu mando uma fala no jogo. Cada fala vira um POST na nossa API, e outra chamada para a rota de voz. O navegador nunca fala com a porta do Ollama."

## Bloco 8 — Painel, final e fechamento (~25 s de fala)

> "Esse é o **painel em Streamlit**, que consome a mesma API via requests. Mando um texto, ele chama a rota e toca o áudio. Serve para testar a API sem abrir o jogo.
>
> Para fechar a partida, uso o **Veredito** sobre o Tomás: é o fim de sessão do MVP. O final depende dos pecados que eu acumulei. Como a minha Ira ficou alta, terminei **Marcado pela Ira**. Tem quatro finais: Redenção, Marcado, Consumido e a derrota em combate.
>
> Todo o código, do jogo, da API e do painel, está no repositório, com README explicando como rodar. Obrigado."

## Dicas de narração

- **Fale enquanto o jogo responde.** Cada fala leva uns 5 segundos; use esse tempo para explicar a mecânica, em vez de ficar em silêncio.
- **Nomeie as mecânicas em voz alta** ("essa é a mecânica 2"): o professor precisa reconhecer 3 ou mais.
- **Diga "gerado agora"** sempre que o texto ou a voz aparecerem, porque o critério é integração real, e não asset pronto.
- Se errar, não recomece do zero: pare, respire e repita a frase. Dá para cortar na edição.
