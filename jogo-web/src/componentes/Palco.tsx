import { useEffect, useState, type ReactNode } from 'react'

// O layout do mockup é fixo em 1920x1080; o palco escala para caber em qualquer janela sem deformar.
export function Palco({ children }: { children: ReactNode }) {
  const [escala, setEscala] = useState(1)
  useEffect(() => {
    const medir = () => setEscala(Math.min(window.innerWidth / 1920, window.innerHeight / 1080))
    medir()
    window.addEventListener('resize', medir)
    return () => window.removeEventListener('resize', medir)
  }, [])
  return (
    <div className="moldura">
      <div className="tela" style={{ transform: `scale(${escala})` }}>
        {children}
      </div>
    </div>
  )
}
