"""Gera os assets visuais do jogo com Stable Diffusion XL 1.0 local (geração OFFLINE, em produção).

Roda no ambiente F:\\ia-local\\venv (torch CUDA + diffusers):
    F:\\ia-local\\venv\\Scripts\\python.exe geracao\\gerar_imagens.py [id ...]

Cada imagem registra prompt, negativo, seed, passos e tempo em assets/manifesto_imagens.json:
é a evidência de "prompt real + resultado" exigida pela Etapa 2.
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

os.environ.setdefault("HF_HOME", r"F:\ia-local\hf")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import torch  # noqa: E402
from diffusers import AutoencoderKL, StableDiffusionXLPipeline  # noqa: E402

BASE = Path(__file__).resolve().parent.parent
SAIDA = BASE / "assets" / "imagens"
MANIFESTO = BASE / "assets" / "manifesto_imagens.json"

MODELO = "stabilityai/stable-diffusion-xl-base-1.0"
VAE = "madebyollin/sdxl-vae-fp16-fix"
PASSOS = 30
GUIDANCE = 7.0

# SDXL entende inglês muito melhor que português; o prompt em inglês é o testado de fato.
NEGATIVO = (
    "text, letters, watermark, logo, signature, blurry, lowres, jpeg artifacts, deformed, "
    "bad anatomy, extra fingers, mutated hands, cartoon, anime, 3d render, photo"
)
ESTILO = "dark fantasy, oil painting, dramatic chiaroscuro lighting, highly detailed, muted palette with crimson and gold accents"

# SDXL treinou em ~1 megapixel: 1344x768 é o 16:9 nativo, 1024x1024 para retratos.
IMAGENS = [
    {
        "id": "menu_fundo",
        "uso": "Fundo do menu principal",
        "largura": 1344, "altura": 768, "seed": 7001,
        "prompt": "key art, a lone inquisitor in a tattered black hooded cloak seen from behind, standing before a colossal ruined gothic cathedral at dusk, seven glowing sigils floating in a circle in a blood red sky, ash falling, cinematic wide composition, " + ESTILO,
    },
    {
        "id": "cena_praca",
        "uso": "Cenário da tela de gameplay (Praça do Pelourinho, Cinzaforte)",
        "largura": 1344, "altura": 768, "seed": 7002,
        "prompt": "medieval town square at dusk, wooden gallows and pillory in the center, angry crowd holding torches, burning timber houses, ash in the air, crimson sky, wet cobblestones, wide establishing shot, concept art, " + ESTILO,
    },
    {
        "id": "retrato_tomas",
        "uso": "Retrato do NPC Tomás (caixa de diálogo)",
        "largura": 1024, "altura": 1024, "seed": 7003,
        "prompt": "character portrait, bust shot, gaunt 30 year old male blacksmith, bruised face, hands tied with rope, frightened eyes, ragged soot-stained clothes, torchlight, dark background, " + ESTILO,
    },
    {
        "id": "retrato_brenna",
        "uso": "Retrato da NPC Capitã Brenna (caixa de diálogo)",
        "largura": 1024, "altura": 1024, "seed": 7004,
        "prompt": "character portrait, bust shot, stern female guard captain in dented steel plate armor, scar on her chin, short dark hair, hand on sword hilt, furious expression, red cloak, torchlight, dark background, " + ESTILO,
    },
    {
        "id": "retrato_odran",
        "uso": "Retrato do NPC Odran, o Mercador (caixa de diálogo)",
        "largura": 1024, "altura": 1024, "seed": 7005,
        "prompt": "character portrait, bust shot, fat smiling male merchant with gold rings on every finger, rich purple velvet robes, calculating eyes, holding a golden amulet, candlelight, dark background, " + ESTILO,
    },
    {
        "id": "demonio_fera",
        "uso": "A Fera, manifestação da Ira (Espelho da Alma / alerta de manifestação)",
        "largura": 1024, "altura": 1024, "seed": 7006,
        "prompt": "demon portrait, the embodiment of wrath, horned shadowy wolf-like beast with burning red eyes and black veins, smoke and embers, emerging from darkness, terrifying, " + ESTILO,
    },
    {
        "id": "demonio_mercador",
        "uso": "O Mercador, manifestação da Avareza (Espelho da Alma / alerta de manifestação)",
        "largura": 1024, "altura": 1024, "seed": 7007,
        "prompt": "demon portrait, the embodiment of greed, elegant faceless figure wearing a golden mask and robes made of coins, long clawed fingers dripping molten gold, eerie, " + ESTILO,
    },
]


def _snapshot(repo):
    # Carregar pelo id do repo faz o diffusers exigir arquivos que não baixamos (ex.: vae_1_0/, VAE que trocamos).
    # Pelo caminho da pasta ele só lê o que existe.
    pasta = Path(os.environ["HF_HOME"]) / "hub" / f"models--{repo.replace('/', '--')}" / "snapshots"
    return str(next(pasta.iterdir()))


def carregar_pipeline():
    vae = AutoencoderKL.from_pretrained(_snapshot(VAE), torch_dtype=torch.float16)
    pipe = StableDiffusionXLPipeline.from_pretrained(
        _snapshot(MODELO), vae=vae, torch_dtype=torch.float16, variant="fp16"
    )
    # A GPU tem 8 GB: sem offload o SDXL fp16 (~7 GB de pesos) estoura a memória no decode.
    pipe.enable_model_cpu_offload()
    return pipe


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    filtro = set(sys.argv[1:])
    SAIDA.mkdir(parents=True, exist_ok=True)
    manifesto = json.loads(MANIFESTO.read_text(encoding="utf-8")) if MANIFESTO.exists() else {}

    inicio_carga = time.perf_counter()
    pipe = carregar_pipeline()
    print(f"pipeline carregado em {time.perf_counter() - inicio_carga:.0f} s | {torch.cuda.get_device_name(0)}", flush=True)

    for item in IMAGENS:
        if filtro and item["id"] not in filtro:
            continue
        inicio = time.perf_counter()
        imagem = pipe(
            prompt=item["prompt"],
            negative_prompt=NEGATIVO,
            width=item["largura"],
            height=item["altura"],
            num_inference_steps=PASSOS,
            guidance_scale=GUIDANCE,
            generator=torch.Generator("cpu").manual_seed(item["seed"]),
        ).images[0]
        segundos = time.perf_counter() - inicio
        arquivo = SAIDA / f"{item['id']}.png"
        imagem.save(arquivo)
        manifesto[item["id"]] = {
            **item,
            "arquivo": f"assets/imagens/{arquivo.name}",
            "ferramenta": "Stable Diffusion XL 1.0 (local, diffusers)",
            "modelo": MODELO,
            "vae": VAE,
            "negative_prompt": NEGATIVO,
            "passos": PASSOS,
            "guidance_scale": GUIDANCE,
            "tempo_s": round(segundos, 1),
            "gerado_em": datetime.now().isoformat(timespec="seconds"),
        }
        MANIFESTO.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{item['id']}: {segundos:.0f} s -> {arquivo}", flush=True)


if __name__ == "__main__":
    main()
