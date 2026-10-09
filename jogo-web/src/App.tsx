import { useState } from 'react'
import type { RespostaJogo } from './api'
import { Palco } from './componentes/Palco'
import { Final } from './telas/Final'
import { Gameplay } from './telas/Gameplay'
import { Menu } from './telas/Menu'

export type Tela = { nome: 'menu' } | { nome: 'jogo'; partida: RespostaJogo } | { nome: 'final'; partida: RespostaJogo }

const CHAVE_VOZ = 'os7.voz'

function lerVoz(): boolean {
  try {
    return localStorage.getItem(CHAVE_VOZ) !== 'nao'
  } catch {
    return true
  }
}

export default function App() {
  const [tela, setTela] = useState<Tela>({ nome: 'menu' })
  const [voz, setVozEstado] = useState(lerVoz)

  const setVoz = (ligada: boolean) => {
    setVozEstado(ligada)
    try {
      localStorage.setItem(CHAVE_VOZ, ligada ? 'sim' : 'nao')
    } catch {
      /* sem localStorage a preferência vale só nesta sessão */
    }
  }

  return (
    <Palco>
      {tela.nome === 'menu' && <Menu voz={voz} setVoz={setVoz} aoJogar={(partida) => setTela({ nome: partida.estado.encerrado ? 'final' : 'jogo', partida })} />}
      {tela.nome === 'jogo' && (
        <Gameplay
          inicial={tela.partida}
          voz={voz}
          setVoz={setVoz}
          aoTerminar={(partida) => setTela({ nome: 'final', partida })}
          aoSair={() => setTela({ nome: 'menu' })}
        />
      )}
      {tela.nome === 'final' && <Final partida={tela.partida} aoMenu={() => setTela({ nome: 'menu' })} />}
    </Palco>
  )
}
