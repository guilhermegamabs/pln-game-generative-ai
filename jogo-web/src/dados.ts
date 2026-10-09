import type { Pecado } from './api'

export const NOMES: Record<Pecado, string> = {
  ira: 'Ira',
  avareza: 'Avareza',
  inveja: 'Inveja',
  preguica: 'Preguiça',
  luxuria: 'Luxúria',
  gula: 'Gula',
  orgulho: 'Orgulho',
}

export const CORES: Record<Pecado, string> = {
  ira: 'linear-gradient(90deg,#6e0f0c,#e0482f)',
  avareza: 'linear-gradient(90deg,#6b5310,#c9a227)',
  inveja: '#4f8a5a',
  preguica: '#6b6b7a',
  luxuria: '#8a4f86',
  gula: '#a0672e',
  orgulho: '#7b7fb8',
}

// Imagens geradas com Stable Diffusion XL na CP4 (assets/imagens, manifesto em assets/manifesto_imagens.json).
export const RETRATOS: Record<string, string> = {
  tomas: '/imagens/retrato_tomas.png',
  brenna: '/imagens/retrato_brenna.png',
  odran: '/imagens/retrato_odran.png',
}
export const DEMONIOS: Partial<Record<Pecado, string>> = {
  ira: '/imagens/demonio_fera.png',
  avareza: '/imagens/demonio_mercador.png',
}

export const INTENCOES: Record<string, string> = {
  violencia: 'Violência',
  ameaca: 'Ameaça',
  arrogancia: 'Arrogância',
  suborno: 'Suborno',
  ganancia: 'Ganância',
  manipulacao: 'Manipulação',
  compaixao: 'Compaixão',
  negociacao: 'Negociação',
  neutro: 'Neutro',
}

export function pecadoDominante(pecados: Record<Pecado, number>): [Pecado, number] {
  return (Object.entries(pecados) as [Pecado, number][]).reduce((a, b) => (b[1] > a[1] ? b : a))
}

export function morto(npc: { genero?: string }): string {
  return npc.genero === 'f' ? 'morta' : 'morto'
}

export function sinal(valor: number): string {
  return valor > 0 ? `+${valor}` : `${valor}`
}
