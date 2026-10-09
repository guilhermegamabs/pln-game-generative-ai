import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react'
import { api, ErroAPI, type RespostaJogo, type Ultimo } from '../api'
import { Medidores } from '../componentes/Medidores'
import { DEMONIOS, INTENCOES, NOMES, RETRATOS, sinal } from '../dados'
import { calar, falar } from '../voz'
import { Espelho } from './Espelho'

interface Props {
  inicial: RespostaJogo
  voz: boolean
  setVoz: (ligada: boolean) => void
  aoTerminar: (partida: RespostaJogo) => void
  aoSair: () => void
}

type Sussurro = NonNullable<Ultimo['manifestacao']>

// Linhas do terminal que viram painel próprio na interface (HUD, fala, manifestação, final) não se repetem na narração.
function narracao(linhas: string[], falaNpc?: string): string[] {
  return linhas
    .map((l) => l.trim())
    .filter(
      (l) =>
        l &&
        !l.startsWith('[') &&
        !/[░█]/.test(l) &&
        !l.startsWith('***') &&
        !l.startsWith('===') &&
        !(falaNpc && l.endsWith(falaNpc)),
    )
}

function relatoCombate(c: NonNullable<Ultimo['combate']>, nome: string, brecha: boolean): string {
  const partes: string[] = []
  if (c.acao === 'defender') partes.push(`Você se defende.${brecha ? ' Brecha aberta: o próximo golpe sai em dobro.' : ''}`)
  if (c.acao === 'item') partes.push('Você usa um item.')
  if (c.acao === 'fugir') return `Você fugiu. ${nome} não vai esquecer.`
  if (c.dano_causado) partes.push(`${c.poder ? 'Com o poder demoníaco, você' : 'Você'} causa ${c.dano_causado} de dano.`)
  if (c.resultado === 'venceu') partes.push(`${nome} cai.`)
  else if (c.dano_recebido) partes.push(`${nome} revida: ${c.dano_recebido} de dano.`)
  else if (c.resultado === 'continua') partes.push(`${nome} não revida.`)
  return partes.join(' ')
}

export function Gameplay({ inicial, voz, setVoz, aoTerminar, aoSair }: Props) {
  const [partida, setPartida] = useState(inicial)
  const [fala, setFala] = useState<Ultimo['fala'] | null>(null)
  const [leitura, setLeitura] = useState<Ultimo['leitura'] | null>(null)
  const [memoria, setMemoria] = useState<Ultimo['memoria'] | null>(null)
  const [sussurro, setSussurro] = useState<Sussurro | null>(null)
  const [deltas, setDeltas] = useState<Ultimo['pecados']>({})
  const [texto, setTexto] = useState('')
  const [pensando, setPensando] = useState<string | null>(null)
  const [segundos, setSegundos] = useState(0)
  const [erro, setErro] = useState<string | null>(null)
  const [avisoOffline, setAvisoOffline] = useState<string | null>(null)
  const [golpe, setGolpe] = useState<Ultimo['combate'] | null>(null)
  const [painel, setPainel] = useState<'memorias' | 'veredito' | 'itens' | null>(null)
  const [espelho, setEspelho] = useState(false)
  const [confirmarAtaque, setConfirmarAtaque] = useState(false)
  const [tocando, setTocando] = useState(false)
  const [linhas, setLinhas] = useState(() => narracao(inicial.linhas))
  const campo = useRef<HTMLInputElement>(null)

  const estado = partida.estado
  const npc = estado.npcs.find((n) => n.id === estado.atual)!
  const falaDoAtual = fala && fala.npc === npc.id ? fala : null
  const combate = estado.jogador.combate
  const golpeDoAtual = golpe && golpe.npc === npc.id ? golpe : null
  const item = (id: string) => estado.jogador.inventario.find((i) => i.id === id)
  const poder = estado.jogador.manifestacoes.length
    ? estado.jogador.manifestacoes.reduce((a, b) => (estado.jogador.pecados[b] > estado.jogador.pecados[a] ? b : a))
    : null

  useEffect(() => {
    if (!pensando) return
    setSegundos(0)
    const relogio = setInterval(() => setSegundos((s) => s + 1), 1000)
    return () => clearInterval(relogio)
  }, [pensando])

  useEffect(() => {
    if (!confirmarAtaque) return
    const t = setTimeout(() => setConfirmarAtaque(false), 3000)
    return () => clearTimeout(t)
  }, [confirmarAtaque])

  useEffect(() => {
    const tecla = (e: KeyboardEvent) => {
      if (e.key === 'Tab') {
        e.preventDefault()
        setEspelho((v) => !v)
      } else if (e.key === 'Escape') {
        setEspelho(false)
        setPainel(null)
      }
    }
    window.addEventListener('keydown', tecla)
    return () => window.removeEventListener('keydown', tecla)
  }, [])

  useEffect(() => () => calar(), [])

  const enviar = useCallback(
    async (entrada: string, rotulo: string) => {
      if (pensando || !entrada.trim()) return
      setPensando(rotulo)
      setErro(null)
      setPainel(null)
      try {
        const r = await api.comando(partida.id, entrada)
        const u = r.ultimo
        setPartida(r)
        setDeltas(u.pecados ?? {})
        if (u.fala) setFala(u.fala)
        setGolpe(u.combate ?? null)
        if (u.leitura) setLeitura(u.leitura)
        if (u.memoria) setMemoria(u.memoria)
        if (u.manifestacao) setSussurro(u.manifestacao)
        setLinhas(narracao(r.linhas, u.fala?.texto))
        const aviso = r.linhas.find((l) => l.startsWith('[IA indisponível'))
        if (aviso) setAvisoOffline(aviso.replace(/^\[|\]$/g, ''))
        if (voz && u.fala) falar(u.fala.texto, setTocando)
        if (voz && u.manifestacao) falar(u.manifestacao.fala, setTocando)
        if (u.final) aoTerminar(r)
      } catch (e) {
        if (e instanceof ErroAPI && e.codigo === 409) {
          aoTerminar(await api.partida(partida.id))
          return
        }
        setErro((e as Error).message)
      } finally {
        setPensando(null)
        campo.current?.focus()
      }
    },
    [pensando, partida.id, voz, aoTerminar],
  )

  const enviarFala = (e: FormEvent) => {
    e.preventDefault()
    const t = texto.trim()
    if (!t) return
    setTexto('')
    enviar(t, `${npc.nome} está pensando`)
  }

  const atacar = () => {
    if (!confirmarAtaque) return setConfirmarAtaque(true)
    setConfirmarAtaque(false)
    enviar('/atacar', 'O combate acontece')
  }

  const [pecadoSussurro, nomeLocal] = [sussurro?.pecado, estado.cena.local.split(', em ')[0]]
  const usarItem = (id: string) => enviar(`/item ${id}`, id === 'pocao' ? 'Você bebe a poção' : 'Você derrama a água benta')

  const relacaoClasse = npc.relacao < -10 ? 'ruim' : npc.relacao > 10 ? 'boa' : ''

  return (
    <section className="tela-jogo">
      <div className="fundo" style={{ backgroundImage: 'url(/imagens/cena_praca.png)' }} />
      <div className="vinheta" />

      <div className="painel hud-jogador">
        <div className="nome">{estado.jogador.nome}</div>
        <div className={`barra hud-vida${golpe?.dano_recebido ? ' ferido' : ''}`} key={estado.jogador.vida}>
          <i style={{ width: `${(estado.jogador.vida / estado.jogador.vida_max) * 100}%` }} />
        </div>
        <div className="linha">
          <span>
            Vida {estado.jogador.vida} / {estado.jogador.vida_max}
          </span>
          <span className="hud-ouro">{estado.jogador.ouro} moedas</span>
        </div>
        <div className="hud-marcas">
          {estado.jogador.aparencia.length ? `Marcas: ${estado.jogador.aparencia.join(', ')}` : 'Sem marcas de corrupção'}
        </div>
      </div>

      <div className="painel presentes">
        <div className="rotulo">Na praça</div>
        {estado.npcs.map((n) => (
          <button
            key={n.id}
            className={`presente${n.id === estado.atual ? ' atual' : ''}`}
            disabled={!n.vivo || !!pensando || n.id === estado.atual || !!combate}
            onClick={() => enviar(`/falar ${n.id}`, `Você se aproxima de ${n.nome.split(',')[0]}`)}
          >
            <img src={RETRATOS[n.id]} alt="" />
            <span>
              {n.nome.split(',')[0]}
              <small>{n.vivo ? `${n.rotulo_relacao} · ${sinal(n.relacao)}` : 'morto'}</small>
            </span>
          </button>
        ))}
      </div>

      <div className="painel local">
        <div className="nome">{nomeLocal}</div>
        <div className="sub">CINZAFORTE · TERRITÓRIO DA IRA</div>
      </div>
      {partida.offline && (
        <div className="painel offline" title={avisoOffline ?? ''}>
          IA indisponível: modo offline (falas simples)
        </div>
      )}

      <div className="painel corrupcao">
        <div className="rotulo">Corrupção</div>
        <Medidores pecados={estado.jogador.pecados} limiar={estado.limiares.manifestacao} destaque={deltas} />
      </div>

      {sussurro && (
        <div className="painel sussurro">
          {pecadoSussurro && DEMONIOS[pecadoSussurro] ? (
            <img src={DEMONIOS[pecadoSussurro]} alt={sussurro.nome} />
          ) : (
            <div className="sem-retrato">{sussurro.nome.split(' ').pop()?.[0]}</div>
          )}
          <div>
            <div className="quem">{sussurro.nome} sussurra…</div>
            <p>“{sussurro.fala}”</p>
          </div>
        </div>
      )}

      {leitura && (
        <div className="painel leitura">
          <div className="rotulo">Intenção lida</div>
          <span className="chip">
            {INTENCOES[leitura.intencao] ?? leitura.intencao} · intensidade {leitura.intensidade}
          </span>
          <div className="efeitos">
            {Object.entries(deltas ?? {}).map(([p, v]) => (
              <span key={p}>
                {NOMES[p as keyof typeof NOMES]} <b className={v! > 0 ? 'sobe' : 'desce'}>{sinal(v!)}</b> ·{' '}
              </span>
            ))}
            Relação com {estado.npcs.find((n) => n.id === leitura.npc)?.nome.split(',')[0]}{' '}
            <b className={leitura.delta_relacao >= 0 ? 'bom' : 'ruim'}>{sinal(leitura.delta_relacao)}</b>
          </div>
        </div>
      )}

      {memoria && (
        <div className="painel memoria-toast">
          <b>{estado.npcs.find((n) => n.id === memoria.npc)?.nome.split(',')[0]} lembrará disso:</b> “{memoria.texto}”
        </div>
      )}

      {(linhas.length > 0 || erro) && (
        <div className={`painel narracao${erro ? ' aviso-erro' : ''}`}>
          {erro ?? linhas.map((l, i) => <p key={i}>{l}</p>)}
        </div>
      )}

      {painel === 'memorias' && (
        <div className="painel lista-memorias">
          <div className="rotulo">O que {npc.nome.split(',')[0]} lembra de você</div>
          {npc.memorias.length ? npc.memorias.map((m, i) => <p key={i}>“{m}”</p>) : <p className="discreto">Nenhuma lembrança ainda.</p>}
        </div>
      )}

      {painel === 'itens' && (
        <div className="painel lista-memorias inventario">
          <div className="rotulo">Inventário</div>
          {estado.jogador.inventario.map((i) => (
            <div key={i.id} className="item">
              <span>
                <b>{i.nome}</b> x{i.quantidade}
                <small>{i.efeito}</small>
              </span>
              <button className="botao" disabled={!!pensando || !i.quantidade} onClick={() => usarItem(i.id)}>
                Usar
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="painel dialogo">
        <img className="retrato" src={RETRATOS[npc.id]} alt={npc.nome} />
        <div className="npc-cabecalho">
          <span className="npc-nome">{npc.nome}</span>
          <span className={`npc-relacao ${relacaoClasse}`}>
            {npc.rotulo_relacao} · {sinal(npc.relacao)}
          </span>
          {combate ? (
            <span className="npc-vida">
              <span className="barra">
                <i style={{ width: `${(npc.vida / npc.vida_max) * 100}%` }} />
              </span>
              {npc.vida} / {npc.vida_max}
            </span>
          ) : (
            falaDoAtual?.emocao && <span className="npc-emocao">{falaDoAtual.emocao}</span>
          )}
          <button className={`voz${voz ? '' : ' mudo'}`} onClick={() => (voz ? (calar(), setVoz(false)) : setVoz(true))} title="Liga ou desliga as vozes">
            <span className={`onda${tocando ? ' tocando' : ''}`}>
              <i /><i /><i /><i /><i /><i />
            </span>
            {voz ? 'voz' : 'sem voz'}
          </button>
        </div>
        <p className="fala">
          {pensando ? (
            <span className="pensando">
              {pensando}… <small>{segundos} s</small>
            </span>
          ) : golpeDoAtual ? (
            <span className="relato-combate">{relatoCombate(golpeDoAtual, npc.nome.split(',')[0], combate?.brecha ?? false)}</span>
          ) : falaDoAtual ? (
            `“${falaDoAtual.texto}”`
          ) : (
            <span className="descricao">{npc.descricao}</span>
          )}
        </p>
        <form className="entrada" onSubmit={enviarFala}>
          <input
            ref={campo}
            className="campo"
            value={texto}
            maxLength={500}
            autoFocus
            disabled={!!pensando || !!combate}
            placeholder={combate ? 'Em combate: escolha uma ação abaixo' : `Diga algo a ${npc.nome.split(',')[0]}…`}
            onChange={(e) => setTexto(e.target.value)}
          />
          <button className="botao" type="submit" disabled={!!pensando || !!combate || !texto.trim()}>
            Falar
          </button>
        </form>
        {combate ? (
          <div className="acoes combate">
            <button className="botao perigo" onClick={() => enviar('/atacar', 'Você golpeia')} disabled={!!pensando}>
              Golpear
            </button>
            <button className="botao" onClick={() => enviar('/defender', 'Você ergue a guarda')} disabled={!!pensando}>
              Defender
            </button>
            <button
              className="botao poder"
              onClick={() => enviar('/poder', `${estado.manifestacoes[poder!].nome} empresta a força`)}
              disabled={!!pensando || !poder}
              title={poder ? `${estado.manifestacoes[poder].poder}. Custa ${NOMES[poder]} +8.` : 'Nenhum pecado despertou ainda'}
            >
              {poder ? `Poder: ${estado.manifestacoes[poder].nome}` : 'Poder demoníaco'}
            </button>
            <button className="botao" onClick={() => usarItem('pocao')} disabled={!!pensando || !item('pocao')?.quantidade}>
              Poção ({item('pocao')?.quantidade ?? 0})
            </button>
            <button className="botao" onClick={() => usarItem('agua_benta')} disabled={!!pensando || !item('agua_benta')?.quantidade}>
              Água benta ({item('agua_benta')?.quantidade ?? 0})
            </button>
            <button className="botao" onClick={() => enviar('/fugir', 'Você recua')} disabled={!!pensando}>
              Fugir
            </button>
            <button className="botao" onClick={() => setEspelho(true)}>
              Espelho [Tab]
            </button>
          </div>
        ) : (
          <div className="acoes">
            <button className="botao perigo" onClick={atacar} disabled={!!pensando}>
              {confirmarAtaque ? 'Confirmar ataque?' : 'Atacar'}
            </button>
            <button className="botao" onClick={() => enviar('/roubar', 'Você estende a mão')} disabled={!!pensando}>
              Roubar
            </button>
            <button className="botao" onClick={() => enviar('/doar 10', 'Você conta as moedas')} disabled={!!pensando || estado.jogador.ouro < 10}>
              Doar 10
            </button>
            <button className="botao" onClick={() => setPainel(painel === 'itens' ? null : 'itens')}>
              Itens
            </button>
            <button className="botao" onClick={() => setPainel(painel === 'memorias' ? null : 'memorias')}>
              Memórias
            </button>
            <button className="botao" onClick={() => setEspelho(true)}>
              Espelho [Tab]
            </button>
            <button className="botao veredito" onClick={() => setPainel(painel === 'veredito' ? null : 'veredito')} disabled={!!pensando}>
              Veredito
            </button>
            <button className="botao discreto-botao" onClick={aoSair}>
              Menu
            </button>
          </div>
        )}
        {painel === 'veredito' && (
          <div className="painel escolha-veredito">
            <div className="rotulo">Julgar Tomás e encerrar a partida</div>
            <p className="discreto">O final depende dos seus pecados no momento do veredito.</p>
            <div className="acoes">
              <button className="botao" onClick={() => enviar('/veredito absolver', 'A praça aguarda')}>
                Absolver
              </button>
              <button className="botao perigo" onClick={() => enviar('/veredito condenar', 'A praça aguarda')}>
                Condenar
              </button>
            </div>
          </div>
        )}
      </div>

      {espelho && <Espelho estado={estado} aoFechar={() => setEspelho(false)} />}
    </section>
  )
}
