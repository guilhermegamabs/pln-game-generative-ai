import { api } from './api'

// Fila de falas: a do NPC toca primeiro e a do demônio em seguida, sem uma cortar a outra.
let fila: Promise<void> = Promise.resolve()
let atual: HTMLAudioElement | null = null

export function tocarArquivo(url: string, aoTocar?: (tocando: boolean) => void): void {
  fila = fila.then(() => reproduzir(new Audio(url), aoTocar))
}

export function falar(texto: string, aoTocar?: (tocando: boolean) => void): void {
  // Gestos entre asteriscos não são falados; a API também remove, mas assim nem gasta a chamada.
  if (!texto.replace(/\*[^*]*\*/g, '').trim()) return
  const audio = api.voz(texto).catch(() => null) // sem voz (Piper fora), o jogo segue só com texto
  fila = fila.then(async () => {
    const blob = await audio
    if (!blob) return
    const url = URL.createObjectURL(blob)
    await reproduzir(new Audio(url), aoTocar)
    URL.revokeObjectURL(url)
  })
}

export function calar(): void {
  atual?.pause()
  atual = null
  fila = Promise.resolve()
}

function reproduzir(audio: HTMLAudioElement, aoTocar?: (tocando: boolean) => void): Promise<void> {
  return new Promise((fim) => {
    atual = audio
    const terminar = () => {
      aoTocar?.(false)
      fim()
    }
    audio.onended = terminar
    audio.onerror = terminar
    audio.onpause = terminar
    aoTocar?.(true)
    audio.play().catch(terminar) // navegador pode bloquear áudio antes do primeiro clique
  })
}
