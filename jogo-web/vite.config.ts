import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// As imagens (SDXL) e vozes (Piper) geradas na CP4 ficam em ../assets: o Vite serve essa pasta direto,
// sem duplicar arquivo. Ex.: ../assets/imagens/menu_fundo.png vira /imagens/menu_fundo.png.
export default defineConfig({
  plugins: [react()],
  publicDir: '../assets',
  server: { port: 5173 },
})
