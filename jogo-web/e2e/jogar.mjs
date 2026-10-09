// Teste de ponta a ponta: um jogador clica no jogo inteiro (menu -> partida -> Espelho -> final) num Chrome headless.
// Tira um print de cada tela em e2e/prints/. Uso: e2e/rodar.sh (sobe API + Ollama simulado + Vite).
import { mkdirSync } from 'node:fs'
import puppeteer from 'puppeteer-core'

const ENDERECO = process.env.URL_JOGO ?? 'http://localhost:5174'
const PRINTS = new URL('./prints/', import.meta.url).pathname
mkdirSync(PRINTS, { recursive: true })

const navegador = await puppeteer.launch({
  executablePath: process.env.CHROME ?? '/usr/bin/google-chrome',
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

  await clicarTexto('Atacar')
  if (!(await texto('.acoes')).includes('Confirmar ataque?')) falhar('ataque devia pedir confirmação')
  await clicarTexto('Confirmar ataque?')
  await esperarFimDoTurno()
  if (!(await texto('.presentes')).includes('morto')) falhar('Brenna devia aparecer morta')
  if (!(await texto('.narracao')).includes('cai sem vida')) falhar('narração do ataque não apareceu')
  ok('ataque com confirmação: Brenna morta, narração e testemunhas')

  await clicarTexto('Tomás')
  await esperarFimDoTurno()
  // Ira: compaixão -4 (fica em 0) + ataque 20 + violência 18 = 38, ainda abaixo do limiar de 40.
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
  await print('3_gameplay_fera')

  await pagina.keyboard.press('Tab')
  await pagina.waitForSelector('.espelho')
  if (!(await texto('.manifestacoes')).includes('DESPERTA')) falhar('Espelho devia mostrar A Fera desperta')
  ok('Tab abre o Espelho da Alma com A Fera desperta')
  await print('4_espelho_da_alma')
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
  await print('5_final')

  await clicarTexto('Voltar ao menu')
  await pagina.waitForSelector('.tela-menu')
  await pagina.waitForFunction(() => document.querySelector('.opcoes')?.textContent?.includes('Terminada'))
  ok('menu mostra a partida salva como terminada')

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
