// Cliente da API do grupo (api/). O jogo nunca fala com o Ollama nem com o Piper diretamente.

export const PECADOS = ['ira', 'avareza', 'inveja', 'preguica', 'luxuria', 'gula', 'orgulho'] as const
export type Pecado = (typeof PECADOS)[number]

export interface NPC {
  id: string
  nome: string
  descricao: string
  relacao: number
  rotulo_relacao: string
  vivo: boolean
  ouro: number
  memorias: string[]
}

export interface Estado {
  cena: { local: string; situacao: string; npc_inicial: string }
  atual: string
  encerrado: boolean
  jogador: {
    nome: string
    ouro: number
    pecados: Record<Pecado, number>
    manifestacoes: Pecado[]
    eventos: string[]
    final: string | null
    aparencia: string[]
  }
  npcs: NPC[]
  manifestacoes: Record<Pecado, { nome: string; poder: string }>
  limiares: { manifestacao: number; consumido: number }
}

export interface Ultimo {
  fala?: { npc: string; texto: string; emocao: string }
  leitura?: { npc: string; intencao: string; intensidade: number; delta_relacao: number }
  memoria?: { npc: string; texto: string }
  pecados?: Partial<Record<Pecado, number>>
  manifestacao?: { pecado: Pecado; nome: string; fala: string }
  final?: { titulo: string; texto: string }
}

export interface RespostaJogo {
  id: string
  linhas: string[]
  ultimo: Ultimo
  estado: Estado
  offline: boolean
}

export interface StatusIA {
  texto: boolean
  voz: boolean
  modelo_texto: string
  detalhe: { texto: string; voz: string }
}

export class ErroAPI extends Error {
  codigo: number | null
  constructor(mensagem: string, codigo: number | null) {
    super(mensagem)
    this.codigo = codigo
  }
}

const URL_API = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(/\/$/, '')
// MVP local: a chave fica no .env.local do front. Num jogo publicado ela não poderia ir para o navegador;
// o caminho seria login do jogador e token de sessão emitido pela API.
const CHAVE = import.meta.env.VITE_API_KEY ?? ''

async function chamar(metodo: 'GET' | 'POST', rota: string, corpo?: unknown): Promise<Response> {
  let resposta: Response
  try {
    resposta = await fetch(`${URL_API}${rota}`, {
      method: metodo,
      headers: { 'Content-Type': 'application/json', 'X-API-Key': CHAVE },
      body: corpo === undefined ? undefined : JSON.stringify(corpo),
    })
  } catch {
    throw new ErroAPI(`A API do jogo não respondeu em ${URL_API}. Ela está rodando?`, null)
  }
  if (!resposta.ok) {
    let detalhe = resposta.statusText
    try {
      detalhe = (await resposta.json()).detail ?? detalhe
    } catch {
      /* corpo sem JSON: fica o statusText */
    }
    if (resposta.status === 401) detalhe = 'A API recusou a chave. Confira VITE_API_KEY no jogo-web/.env.local.'
    throw new ErroAPI(String(detalhe), resposta.status)
  }
  return resposta
}

export const api = {
  status: async (): Promise<StatusIA> => (await chamar('GET', '/v1/ia-generativa/status')).json(),
  novaPartida: async (): Promise<RespostaJogo> => (await chamar('POST', '/v1/jogo/partidas')).json(),
  partida: async (id: string): Promise<RespostaJogo> => (await chamar('GET', `/v1/jogo/partidas/${id}`)).json(),
  comando: async (id: string, entrada: string): Promise<RespostaJogo> =>
    (await chamar('POST', `/v1/jogo/partidas/${id}/comandos`, { entrada })).json(),
  voz: async (texto: string): Promise<Blob> => (await chamar('POST', '/v1/ia-generativa/voz', { texto })).blob(),
}
