import { useEffect, useState, type ReactNode } from 'react'

// O layout do mockup foi desenhado em 1920x1080. O palco escala para a janela sem deformar e,
// em vez de deixar faixas pretas, estica a área lógica até a proporção real da janela:
// os painéis presos às bordas acompanham, e o fundo (cover) preenche o resto.
function medir() {
  const escala = Math.min(window.innerWidth / 1920, window.innerHeight / 1080)
  return { escala, largura: window.innerWidth / escala, altura: window.innerHeight / escala }
}

export function Palco({ children }: { children: ReactNode }) {
  const [palco, setPalco] = useState(medir)
  useEffect(() => {
    const atualizar = () => setPalco(medir())
    window.addEventListener('resize', atualizar)
    return () => window.removeEventListener('resize', atualizar)
  }, [])
  return (
    <div className="moldura">
      <div className="tela" style={{ width: palco.largura, height: palco.altura, transform: `scale(${palco.escala})` }}>
        {children}
      </div>
    </div>
  )
}
