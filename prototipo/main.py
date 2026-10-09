"""OS 7 PECADOS — protótipo de diálogo com NPCs via LLM local (Ollama)."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from estado import carregar_mundo
from jogo import Jogo
from llm import (
    MODELO_PADRAO,
    URL_API_PADRAO,
    ClienteAPI,
    ClienteComFallback,
    ClienteFalso,
    ClienteOllama,
    ClienteRegistrado,
    ErroLLM,
)

BASE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description="Protótipo OS 7 PECADOS — diálogo com NPCs via Ollama")
    parser.add_argument("--api", default=URL_API_PADRAO, help=f"URL da API do jogo (padrão: {URL_API_PADRAO})")
    parser.add_argument("--direto", action="store_true", help="modo da CP4: fala direto com o Ollama, sem a API")
    parser.add_argument("--modelo", default=MODELO_PADRAO, help=f"modelo do Ollama no modo --direto (padrão: {MODELO_PADRAO})")
    parser.add_argument("--offline", action="store_true", help="respostas falsas por palavra-chave, sem IA")
    parser.add_argument("--novo", action="store_true", help="ignora o save e começa do zero")
    args = parser.parse_args()

    # Console do Windows não usa UTF-8 por padrão: sem isso os acentos e as barras quebram.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")

    if args.offline:
        cliente = ClienteFalso()
    else:
        cliente = ClienteOllama(args.modelo) if args.direto else ClienteAPI(args.api)
        try:
            cliente.verificar()
            print(f"[carregando {cliente.modelo} na memória...]", flush=True)
            cliente.aquecer()
        except ErroLLM as erro:
            print(f"[erro] {erro}\nPara testar sem IA: python main.py --offline")
            return 1
        # Verificado na abertura; se cair durante a partida, o jogo continua offline em vez de travar.
        cliente = ClienteComFallback(cliente, ClienteFalso())

    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    cliente = ClienteRegistrado(cliente, BASE / "logs" / f"sessao_{carimbo}.jsonl")
    print(f"[modelo: {cliente.modelo}]")

    jogo = Jogo(cliente, carregar_mundo(BASE / "dados" / "mundo.json"), BASE / "saves" / "partida.json", carregar=not args.novo)
    jogo.introducao()
    while not jogo.encerrado:
        try:
            entrada = input("\n> ")
        except (EOFError, KeyboardInterrupt):
            jogo.cmd_sair("")
            break
        jogo.processar(entrada)
    return 0


if __name__ == "__main__":
    sys.exit(main())
