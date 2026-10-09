import { PECADOS, type Pecado } from '../api'
import { CORES, NOMES } from '../dados'

interface Props {
  pecados: Record<Pecado, number>
  limiar: number
  destaque?: Partial<Record<Pecado, number>>
}

export function Medidores({ pecados, limiar, destaque = {} }: Props) {
  return (
    <>
      {PECADOS.map((p) => {
        const valor = pecados[p]
        const variacao = destaque[p]
        return (
          <div key={p} className={`pecado${valor >= limiar ? ' forte' : ''}`} data-pecado={p}>
            <span>{NOMES[p]}</span>
            <div className="barra limiar" style={{ ['--limiar' as string]: `${limiar}%` }}>
              <i style={{ width: `${valor}%`, background: CORES[p] }} />
            </div>
            <b>
              {valor}
              {variacao ? <em className={variacao > 0 ? 'sobe' : 'desce'}>{variacao > 0 ? '+' : ''}{variacao}</em> : null}
            </b>
          </div>
        )
      })}
    </>
  )
}
