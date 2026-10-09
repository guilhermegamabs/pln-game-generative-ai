import { PECADOS, type Estado, type Pecado } from '../api'
import { Medidores } from '../componentes/Medidores'
import { DEMONIOS, NOMES, pecadoDominante, sinal, morto } from '../dados'

// Pecados ativos no MVP (escopo da CP4: Ira e Avareza); os outros aparecem bloqueados até despertarem.
const ATIVOS: Pecado[] = ['ira', 'avareza']

export function Espelho({ estado, aoFechar }: { estado: Estado; aoFechar: () => void }) {
  const { jogador, limiares } = estado
  const [dominante, valor] = pecadoDominante(jogador.pecados)
  const cartas = PECADOS.filter((p) => ATIVOS.includes(p) || jogador.manifestacoes.includes(p))
  const bloqueadas = PECADOS.filter((p) => !cartas.includes(p))
  const acima = PECADOS.filter((p) => jogador.pecados[p] >= limiares.manifestacao)

  return (
    <div className="espelho" onClick={aoFechar}>
      <div className="fundo" style={{ backgroundImage: 'url(/imagens/cena_praca.png)' }} />
      <div className="vinheta" />
      <div className="centro">
        <div className="espelho-titulo">
          <h2>Espelho da Alma</h2>
          <p>O que você está se tornando</p>
        </div>

        <div className="painel medidores" onClick={(e) => e.stopPropagation()}>
          <div className="rotulo">Os sete pecados</div>
          <Medidores pecados={jogador.pecados} limiar={limiares.manifestacao} />
          <div className="legenda-limiar">
            │ marca branca = {limiares.manifestacao}, limiar em que o pecado se manifesta · {limiares.consumido} = consumido
          </div>
        </div>

        <div className="painel aparencia" onClick={(e) => e.stopPropagation()}>
          <div className="rotulo">Aparência</div>
          <p>{jogador.aparencia.length ? jogador.aparencia.join('. ') + '.' : 'Nenhuma marca visível. Ainda.'}</p>
          <div className="relacoes">
            {estado.npcs.map((n, i) => (
              <span key={n.id}>
                {i > 0 && ' · '}
                {n.nome.split(',')[0]}{' '}
                {n.vivo ? (
                  <b className={n.relacao < -10 ? 'ruim' : n.relacao > 10 ? 'bom' : ''}>
                    {n.rotulo_relacao} ({sinal(n.relacao)})
                  </b>
                ) : (
                  <i>{morto(n)}</i>
                )}
              </span>
            ))}
          </div>
        </div>

        <div className="manifestacoes">
          {cartas.map((p) => {
            const desperta = jogador.manifestacoes.includes(p)
            const m = estado.manifestacoes[p]
            return (
              <div key={p} className={`painel carta${desperta ? '' : ' dormente'}`}>
                {DEMONIOS[p] ? <img src={DEMONIOS[p]} alt={m.nome} /> : <div className="carta-vazia" />}
                <div className="info">
                  <h3>{m.nome}</h3>
                  <div className="estado">
                    {desperta ? 'DESPERTA' : 'DORMENTE'} · {NOMES[p]} {jogador.pecados[p]}
                    {desperta ? '' : ` / ${limiares.manifestacao}`}
                  </div>
                  <p>
                    <b>Poder:</b> {m.poder}.
                  </p>
                </div>
              </div>
            )
          })}
        </div>

        <div className="bloqueadas">
          {bloqueadas.map((p) => (
            <div key={p} className="bloq">
              <span>?</span>
              {estado.manifestacoes[p].nome}
            </div>
          ))}
        </div>

        <div className="painel finais">
          <div className="final">
            <h4>Redenção</h4>
            <p>{acima.length ? `Em risco: ${acima.map((p) => NOMES[p]).join(' e ')} acima do limiar` : 'Possível: todos os pecados abaixo do limiar'}</p>
            <div className="barra">
              <i style={{ width: `${Math.max(0, 100 - (valor / limiares.manifestacao) * 100)}%`, background: '#6fae6f' }} />
            </div>
          </div>
          <div className="final">
            <h4>Marcado pela {NOMES[dominante]}</h4>
            <p>
              {valor >= limiares.manifestacao ? 'É o que o veredito traria agora' : `${valor} / ${limiares.manifestacao} para o veredito te marcar`}
            </p>
            <div className="barra">
              <i style={{ width: `${Math.min(100, (valor / limiares.manifestacao) * 100)}%`, background: '#c9a227' }} />
            </div>
          </div>
          <div className="final">
            <h4>Consumido pela {NOMES[dominante]}</h4>
            <p>
              {valor} / {limiares.consumido}
            </p>
            <div className="barra">
              <i style={{ width: `${valor}%`, background: '#e0482f' }} />
            </div>
          </div>
        </div>
        <div className="voltar">[Tab] ou clique para voltar ao jogo</div>
      </div>
    </div>
  )
}
