import { type RespostaJogo } from '../api'
import { Medidores } from '../componentes/Medidores'

export function Final({ partida, aoMenu }: { partida: RespostaJogo; aoMenu: () => void }) {
  const { jogador, limiares } = partida.estado
  const titulo = partida.ultimo.final?.titulo ?? jogador.final ?? 'Fim'
  const texto = partida.ultimo.final?.texto
  const redencao = titulo === 'Redenção'
  return (
    <section className={`tela-final${redencao ? ' redencao' : ''}`}>
      <div className="fundo" style={{ backgroundImage: 'url(/imagens/menu_fundo.png)' }} />
      <div className="vinheta" />
      <div className="final-conteudo">
        <div className="rotulo">Final</div>
        <h2>{titulo}</h2>
        {texto && <p className="final-texto">{texto}</p>}
        <div className="final-colunas">
          <div className="painel">
            <div className="rotulo">Sua alma no fim</div>
            <Medidores pecados={jogador.pecados} limiar={limiares.manifestacao} />
          </div>
          <div className="painel">
            <div className="rotulo">O que você fez</div>
            {jogador.eventos.length ? jogador.eventos.map((e, i) => <p key={i}>{e}</p>) : <p className="discreto">Nada além de palavras.</p>}
          </div>
        </div>
        <button className="botao grande" onClick={aoMenu}>
          Voltar ao menu
        </button>
      </div>
    </section>
  )
}
