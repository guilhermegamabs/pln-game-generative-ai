import { useEffect, useState } from 'react'
import { api, ErroAPI, type RespostaJogo, type StatusIA } from '../api'
import { NOMES, pecadoDominante } from '../dados'
import { tocarArquivo } from '../voz'

export const CHAVE_PARTIDA = 'os7.partida'

interface Props {
  voz: boolean
  setVoz: (ligada: boolean) => void
  aoJogar: (partida: RespostaJogo) => void
}

function lerPartidaSalva(): string | null {
  try {
    return localStorage.getItem(CHAVE_PARTIDA)
  } catch {
    return null
  }
}

export function Menu({ voz, setVoz, aoJogar }: Props) {
  const [status, setStatus] = useState<StatusIA | null>(null)
  const [erroStatus, setErroStatus] = useState<string | null>(null)
  const [salva, setSalva] = useState<RespostaJogo | null>(null)
  const [painel, setPainel] = useState<'opcoes' | 'creditos' | 'sair' | null>(null)
  const [carregando, setCarregando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    api.status().then(setStatus, (e: ErroAPI) => setErroStatus(e.message))
    const id = lerPartidaSalva()
    if (id) api.partida(id).then(setSalva, () => setSalva(null))
  }, [])

  const novoJogo = async () => {
    setCarregando(true)
    setErro(null)
    try {
      const partida = await api.novaPartida()
      try {
        localStorage.setItem(CHAVE_PARTIDA, partida.id)
      } catch {
        /* sem localStorage não há "Continuar", mas o jogo funciona */
      }
      // Narração da abertura: voz gerada com Piper TTS na CP4 (assets/audio/narrador_intro.wav).
      if (voz) tocarArquivo('/audio/narrador_intro.wav')
      aoJogar(partida)
    } catch (e) {
      setErro((e as Error).message)
      setCarregando(false)
    }
  }

  const resumoSalva = salva
    ? (() => {
        const [p, v] = pecadoDominante(salva.estado.jogador.pecados)
        const desperto = salva.estado.jogador.manifestacoes.map((m) => salva.estado.manifestacoes[m].nome)
        if (salva.estado.encerrado) return `Terminada · ${salva.estado.jogador.final}`
        return ['Cinzaforte', v > 0 ? `${NOMES[p]} ${v}` : 'alma limpa', ...desperto.map((d) => `${d} desperta`)].join(' · ')
      })()
    : null

  const motorPronto = status?.texto ?? false

  return (
    <section className="tela-menu">
      <div className="fundo" style={{ backgroundImage: 'url(/imagens/menu_fundo.png)' }} />
      <div className="escurece" />
      <div className="titulo">
        <h1>
          <span>OS</span>7 PECADOS
        </h1>
      </div>
      <div className="tagline">“Você não enfrenta os pecados. Você decide qual deles vai se tornar você.”</div>
      <nav className="opcoes">
        <button className="opcao ativa" onClick={novoJogo} disabled={carregando}>
          {carregando ? 'Preparando a praça…' : 'Novo Jogo'}
        </button>
        <button className="opcao" onClick={() => salva && aoJogar(salva)} disabled={!salva}>
          Continuar <small>{resumoSalva ?? 'nenhuma partida salva'}</small>
        </button>
        <button className="opcao" onClick={() => setPainel(painel === 'opcoes' ? null : 'opcoes')}>
          Opções <small>Modelo de IA, voz</small>
        </button>
        <button className="opcao" onClick={() => setPainel(painel === 'creditos' ? null : 'creditos')}>
          Créditos
        </button>
        <button className="opcao" onClick={() => setPainel('sair')}>
          Sair
        </button>
      </nav>

      {painel === 'opcoes' && (
        <div className="painel painel-menu">
          <div className="rotulo">Opções</div>
          <p>
            Modelo de texto: <b>{status?.modelo_texto ?? '?'}</b> (definido no <code>api/.env</code>)
          </p>
          <label className="alternar">
            <input type="checkbox" checked={voz} onChange={(e) => setVoz(e.target.checked)} /> Vozes dos personagens (Piper TTS)
          </label>
          <p className="discreto">Voz no servidor: {status ? (status.voz ? 'disponível' : status.detalhe.voz) : '?'}</p>
        </div>
      )}
      {painel === 'creditos' && (
        <div className="painel painel-menu">
          <div className="rotulo">Créditos</div>
          <p>Guilherme Gama Bitencourt Souza · Igor Thiago Nakajima Vieira</p>
          <p className="discreto">
            Os personagens respondem com texto gerado por IA em tempo real (Qwen2.5 7B via Ollama, local). Retratos e cenários:
            Stable Diffusion XL 1.0. Vozes: Piper TTS pt_BR. As regras do jogo (pecados, finais) são do código, não da IA.
          </p>
        </div>
      )}
      {painel === 'sair' && (
        <div className="painel painel-menu">
          <div className="rotulo">Sair</div>
          <p>A partida fica salva no servidor. Para sair, feche esta aba.</p>
        </div>
      )}
      {erro && <div className="painel aviso-erro menu-erro">{erro}</div>}

      <div className="painel status-ia">
        <span className={`ponto ${motorPronto ? '' : 'apagado'}`} />
        <span>
          {status
            ? motorPronto
              ? (
                  <>
                    Motor narrativo: <b>{status.modelo_texto}</b> via API do grupo · pronto
                  </>
                )
              : `Motor narrativo indisponível (${status.detalhe.texto}): o jogo roda em modo offline`
            : erroStatus ?? 'Verificando o motor narrativo…'}
        </span>
      </div>
      <div className="aviso-ia">Diálogos gerados por IA · classificação 16 anos</div>
      <div className="versao">MVP v1.0 · Checkpoint 5 · PLN</div>
    </section>
  )
}
