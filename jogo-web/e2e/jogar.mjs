// Teste de ponta a ponta: um jogador clica no jogo inteiro (menu -> partida -> Espelho -> final) num Chrome headless.
// Tira um print de cada tela em e2e/prints/. Uso: e2e/rodar.sh (sobe API + Ollama simulado + Vite).
import { existsSync, mkdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import puppeteer from 'puppeteer-core'

const ENDERECO = process.env.URL_JOGO ?? 'http://localhost:5174'
// fileURLToPath: no Windows, .pathname vira "/C:/..." e o mkdir falha.
const PRINTS = fileURLToPath(new URL('./prints/', import.meta.url))
mkdirSync(PRINTS, { recursive: true })

// Caminhos usuais do Chrome/Edge; CHROME=... sobrescreve.
function navegadorDoSistema() {
  const candidatos = [
    '/usr/bin/google-chrome',
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
  ]
  const achado = candidatos.find((c) => existsSync(c))
  if (!achado) throw new Error('Chrome ou Edge não encontrado. Defina CHROME com o caminho do executável.')
  return achado
}

const navegador = await puppeteer.launch({
  executablePath: process.env.CHROME ?? navegadorDoSistema(),
  headless: true,
  args: ['--autoplay-policy=no-user-gesture-required', '--no-first-run'],
})
const pagina = await navegador.newPage()
await pagina.setViewport({ width: 1920, height: 1080 })
const errosConsole = []
pagina.on('console', (m) => m.type() === 'error' && errosConsole.push(m.text()))
pagina.on('pageerror', (e) => errosConsole.push(String(e)))
pagina.on('response', (r) => r.status() >= 400 && errosConsole.push(`HTTP ${r.status()} ${r.request().method()} ${new URL(r.url()).pathname}`))
const chamadas = []
pagina.on('request', (r) => r.url().includes('/v1/') && r.method() !== 'OPTIONS' && chamadas.push(`${r.method()} ${new URL(r.url()).pathname}`))

let passo = 0
const ok = (msg) => console.log(`  ok ${++passo}. ${msg}`)
const falhar = (msg) => {
  throw new Error(msg)
}
const texto = (sel) => pagina.$eval(sel, (e) => e.textContent ?? '')
const clicarTexto = async (rotulo) => {
  const botoes = await pagina.$$('button')
  for (const b of botoes) {
    const t = await b.evaluate((e) => e.textContent ?? '')
    const ativo = await b.evaluate((e) => !e.disabled)
    if (t.includes(rotulo) && ativo) return b.click()
  }
  falhar(`botão "${rotulo}" não encontrado ou desativado`)
}
const esperarFimDoTurno = () => pagina.waitForFunction(() => !document.querySelector('.pensando'), { timeout: 30000 })
// Espera as animações de entrada (até 1 s) terminarem antes do print.
const print = async (nome) => {
  await new Promise((r) => setTimeout(r, 1200))
  await pagina.screenshot({ path: `${PRINTS}${nome}.png` })
}

try {
  await pagina.goto(ENDERECO, { waitUntil: 'networkidle0' })
  await pagina.waitForFunction(() => document.querySelector('.status-ia')?.textContent?.includes('pronto'), { timeout: 10000 })
  ok(`menu abriu, ${(await texto('.status-ia')).trim()}`)
  await print('1_menu')

  await clicarTexto('Novo Jogo')
  await pagina.waitForSelector('.tela-jogo')
  if (!(await texto('.npc-nome')).includes('Tomás')) falhar('a partida devia começar com Tomás')
  ok('Novo Jogo abre o gameplay diante de Tomás')

  await pagina.type('.campo', 'Calma, Tomás. Eu vou te ajudar.')
  await pagina.keyboard.press('Enter')
  await pagina.waitForSelector('.pensando')
  ok('indicador "pensando" aparece durante o turno')
  await esperarFimDoTurno()
  if (!(await texto('.fala')).includes('salvar minha filha')) falhar('fala do NPC não apareceu')
  if (!(await texto('.leitura')).includes('Compaixão')) falhar('intenção lida não apareceu')
  if (!(await texto('.memoria-toast')).includes('lembrará disso')) falhar('memória não apareceu')
  ok('fala livre: fala do NPC, intenção lida (Compaixão) e memória aparecem')
  await print('2_gameplay_dialogo')

  await clicarTexto('Brenna')
  await esperarFimDoTurno()
  if (!(await texto('.npc-nome')).includes('Brenna')) falhar('não trocou para a Brenna')
  ok('troca de NPC pelo painel "Na praça"')

  const vida = () => texto('.hud-jogador .linha')
  const vidaBrenna = () => texto('.npc-vida')
  await clicarTexto('Atacar')
  if (!(await texto('.acoes')).includes('Confirmar ataque?')) falhar('ataque devia pedir confirmação')
  await clicarTexto('Confirmar ataque?')
  await esperarFimDoTurno()
  await pagina.waitForSelector('.acoes.combate')
  if (!(await vida()).includes('Vida 70 / 100')) falhar(`revide da Brenna devia deixar a vida em 70: ${await vida()}`)
  if (!(await vidaBrenna()).includes('75 / 100')) falhar(`Brenna devia ficar com 75: ${await vidaBrenna()}`)
  if (!(await pagina.$eval('.campo', (e) => e.disabled))) falhar('em combate o diálogo devia ficar bloqueado')
  ok('ataque com confirmação abre o combate por turnos: Brenna 75/100, inquisitor 70/100')

  await clicarTexto('Defender')
  await esperarFimDoTurno()
  if (!(await vida()).includes('Vida 62 / 100')) falhar(`defendendo, o dano devia cair para 8: ${await vida()}`)
  if (!(await texto('.fala')).includes('Brecha aberta')) falhar('relato da defesa não apareceu')
  await clicarTexto('Golpear')
  await esperarFimDoTurno()
  if (!(await vidaBrenna()).includes('25 / 100')) falhar(`golpe na brecha devia causar 50: ${await vidaBrenna()}`)
  if (!(await vida()).includes('Vida 32 / 100')) falhar(`Brenna de pé revida 30: ${await vida()}`)
  ok('Defender: dano reduzido e golpe seguinte em dobro (Brenna 25/100, inquisitor 32/100)')
  await print('3_combate')

  await clicarTexto('Poção (2)')
  await esperarFimDoTurno()
  if (!(await vida()).includes('Vida 37 / 100')) falhar(`poção (32 + 35) e revide de 30: ${await vida()}`)
  if (!(await texto('.acoes')).includes('Poção (1)')) falhar('o inventário devia descontar a poção')
  if (!(await texto('.fala')).includes('Poção de cura (vida +35)')) falhar('o relato devia dizer qual item e quanto curou')
  await clicarTexto('Golpear')
  await esperarFimDoTurno()
  if (await pagina.$('.acoes.combate')) falhar('o combate devia terminar com a Brenna caída')
  if (!(await texto('.presentes')).includes('morta')) falhar('Brenna devia aparecer morta')
  if (!(await pagina.$eval('.campo', (e) => e.disabled))) falhar('com a Brenna caída o campo de fala devia travar')
  if (!(await texto('.fala')).includes('Brenna cai')) falhar('relato do golpe final não apareceu')
  if (!(await texto('.narracao')).includes('cai sem vida')) falhar('narração da morte não apareceu')
  ok('Poção gasta o turno; o golpe final derruba a Brenna e as testemunhas veem')

  await clicarTexto('Tomás')
  await esperarFimDoTurno()
  // Ira: compaixão -4 (fica em 0) + atacar 5 + matar 15 + violência 18 = 38, ainda abaixo do limiar de 40.
  await pagina.type('.campo', 'Solta esse amuleto ou eu arranco sua cabeça!')
  await pagina.keyboard.press('Enter')
  await esperarFimDoTurno()
  if (await pagina.$('.sussurro')) falhar('A Fera não podia despertar com Ira 38')
  ok('Ira 38: abaixo do limiar, nenhuma manifestação ainda')
  await pagina.type('.campo', 'Eu vou te matar, ladrão!')
  await pagina.keyboard.press('Enter')
  await esperarFimDoTurno()
  await pagina.waitForSelector('.sussurro', { timeout: 5000 })
  if (!(await texto('.sussurro')).includes('A Fera')) falhar('A Fera devia despertar')
  const ira = await pagina.$eval('[data-pecado="ira"] b', (e) => e.textContent)
  ok(`Ira passa de 40 (${ira}) e A Fera desperta com fala gerada`)
  await print('4_gameplay_fera')

  await pagina.keyboard.press('Tab')
  await pagina.waitForSelector('.espelho')
  if (!(await texto('.manifestacoes')).includes('DESPERTA')) falhar('Espelho devia mostrar A Fera desperta')
  ok('Tab abre o Espelho da Alma com A Fera desperta')
  await print('5_espelho_da_alma')
  await pagina.keyboard.press('Tab')
  await pagina.waitForFunction(() => !document.querySelector('.espelho'))

  await clicarTexto('Memórias')
  if (!(await texto('.lista-memorias')).includes('matar Capitã Brenna')) falhar('Tomás devia lembrar da morte da Brenna')
  ok('Memórias: Tomás lembra que viu a Brenna morrer')

  await clicarTexto('Veredito')
  await clicarTexto('Condenar')
  await pagina.waitForSelector('.tela-final', { timeout: 30000 })
  const final = await texto('.final-conteudo h2')
  if (final !== 'Marcado pela Ira') falhar(`final inesperado: ${final}`)
  ok(`veredito encerra a partida: final "${final}"`)
  await print('6_final')

  await clicarTexto('Voltar ao menu')
  await pagina.waitForSelector('.tela-menu')
  await pagina.waitForFunction(() => document.querySelector('.opcoes')?.textContent?.includes('Terminada'))
  ok('menu mostra a partida salva como terminada')

  // Janelas que não são 16:9 nem 1920 px (barra do navegador, notebook): o palco precisa ocupar tudo, sem faixa preta nem corte.
  for (const [w, h] of [[1536, 730], [1280, 900], [2560, 1300]]) {
    await pagina.setViewport({ width: w, height: h })
    await new Promise((r) => setTimeout(r, 300))
    const r = await pagina.$eval('.tela', (e) => {
      const q = e.getBoundingClientRect()
      return [q.left, q.top, q.width, q.height].map(Math.round)
    })
    if (r.join() !== [0, 0, w, h].join()) falhar(`em ${w}x${h} o palco ficou em ${r.join(', ')}`)
  }
  await pagina.setViewport({ width: 1920, height: 1080 })
  ok('o palco ocupa a janela inteira em 1536x730, 1280x900 e 2560x1300')

  const vozes = chamadas.filter((c) => c.endsWith('/voz')).length
  if (vozes < 2) falhar(`esperava a voz das falas, vieram ${vozes} chamadas /voz`)
  ok(`${vozes} falas narradas pela rota /v1/ia-generativa/voz`)
  if (chamadas.some((c) => c.includes('11434'))) falhar('o navegador nunca deve chamar o Ollama direto')
  const erros = errosConsole.filter((e) => !e.includes('fonts.g') && !e.startsWith('Failed to load resource'))
  if (erros.length) falhar(`erros no console: ${erros.join(' | ')}`)
  ok('nenhum erro no console; o navegador só chamou a API do grupo')
  console.log(`\nChamadas do navegador: ${[...new Set(chamadas)].join(', ')}`)
  console.log(`Prints em ${PRINTS}`)
} catch (e) {
  await print('erro')
  console.error(`\nFALHOU no passo ${passo + 1}: ${e.message}`)
  process.exitCode = 1
} finally {
  await navegador.close()
}
