"""Gera as vozes do jogo com Piper TTS local (voz neural pt_BR-faber-medium) + pós-processamento.

Roda no ambiente F:\\ia-local\\venv:
    F:\\ia-local\\venv\\Scripts\\python.exe geracao\\gerar_vozes.py

As falas dos NPCs são as que a LLM (qwen2.5:7b / llama3.2:3b) gerou de verdade na POC:
isso demonstra a cadeia LLM -> TTS que o jogo usaria em tempo real.

v2 (após revisão do grupo): a Fera da v1 não dava medo e o Tomás soava apressado e robótico.
O Piper só tem uma voz masculina pt_BR, então a identidade de cada personagem vem de uma
cadeia de efeitos em numpy (sem dependência nova): pausas por frase, altura, dobra de voz,
rosnado, saturação, sussurro, reverberação e drone grave.
Principais em assets/audio/; alternativas para o grupo escolher em assets/audio/variantes/.
Registro em assets/manifesto_audio.json.
"""

import json
import re
import sys
import time
import wave
from datetime import datetime
from pathlib import Path

import numpy as np
from piper import PiperVoice, SynthesisConfig

BASE = Path(__file__).resolve().parent.parent
SAIDA = BASE / "assets" / "audio"
VARIANTES = SAIDA / "variantes"
MANIFESTO = BASE / "assets" / "manifesto_audio.json"
VOZ = Path(r"F:\ia-local\vozes\pt\pt_BR\faber\medium\pt_BR-faber-medium.onnx")

TEXTO_NARRADOR = "Cinzaforte, cidade tomada pela Ira. Uma multidão furiosa cerca Tomás, acusado de roubar um amuleto de ouro do mercador Odran. A Capitã Brenna quer enforcá-lo agora mesmo."
TEXTO_TOMAS = "Minha filha está doente... Precisei comprar remédio urgente. Prometo pagar o Odran de volta assim que conseguir!"
TEXTO_ODRAN = "Hmmm, 20 moedas? Isso não é nem um começo para alguém que tem um futuro brilhante. Que tal 50?"
TEXTO_FERA = "Sua sede de sangue está apenas começando. Quer saber o preço do poder que eu posso dar? A sua alma, talvez. A Ira não é barata, inquisidor."

ORIGEM_QWEN = "fala gerada por qwen2.5:7b (prototipo/logs/v2_prompt-ajustado_qwen2-5-7b.jsonl)"
ORIGEM_LLAMA = "fala gerada por llama3.2:3b (prototipo/logs/v1_prompt-original_llama3-2-3b.jsonl), trecho"


# ---------------------------------------------------------------- síntese

def sintetizar(voz, texto, sintese, pausa_frase, pausa_reticencias):
    """Sintetiza frase a frase para controlar as pausas: o Piper sozinho emenda tudo e soa apressado."""
    texto = re.sub(r"\*[^*]*\*", "", texto).strip()  # gestos entre asteriscos não são fala
    partes = [p for p in re.split(r"(\.\.\.|[.!?])", texto) if p.strip()]
    trechos, taxa = [], None
    i = 0
    while i < len(partes):
        frase = partes[i].strip()
        pontuacao = partes[i + 1] if i + 1 < len(partes) and partes[i + 1] in ("...", ".", "!", "?") else ""
        i += 2 if pontuacao else 1
        if not frase:
            continue
        for pedaco in voz.synthesize(frase + (pontuacao if pontuacao != "..." else "."), SynthesisConfig(**sintese)):
            taxa = pedaco.sample_rate
            trechos.append(np.frombuffer(pedaco.audio_int16_bytes, dtype=np.int16).astype(np.float32) / 32768)
        pausa = pausa_reticencias if pontuacao == "..." else pausa_frase
        trechos.append(np.zeros(int(taxa * pausa), dtype=np.float32))
    return np.concatenate(trechos), taxa


# ---------------------------------------------------------------- efeitos (numpy puro)

def esticar(x, fator):
    """fator > 1 deixa mais lento e mais grave (como tocar um disco devagar)."""
    n = int(len(x) * fator)
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)


def _filtro(x, taxa, resposta):
    espectro = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(len(x), 1 / taxa)
    return np.fft.irfft(espectro * resposta(freqs), n=len(x)).astype(np.float32)


def passa_baixa(x, taxa, corte):
    return _filtro(x, taxa, lambda f: 1 / np.sqrt(1 + (f / corte) ** 4))


def passa_alta(x, taxa, corte):
    return _filtro(x, taxa, lambda f: 1 / np.sqrt(1 + (corte / np.maximum(f, 1)) ** 4))


def atrasar(x, taxa, segundos, comprimento):
    y = np.zeros(comprimento, dtype=np.float32)
    inicio = int(taxa * segundos)
    trecho = x[: max(0, comprimento - inicio)]
    y[inicio:inicio + len(trecho)] = trecho
    return y


def dobrar(x, taxa, desafino, atraso, ganho):
    """Duas vozes quase iguais, levemente desafinadas: soa como algo que fala por dentro do personagem."""
    segunda = esticar(x, desafino)
    comprimento = max(len(x), len(segunda) + int(taxa * atraso))
    base = np.pad(x, (0, comprimento - len(x)))
    return base + ganho * atrasar(segunda, taxa, atraso, comprimento)


def rosnar(x, taxa, frequencia, profundidade):
    """Modulação em anel grave: vira um tremor áspero na garganta."""
    t = np.arange(len(x)) / taxa
    return x * (1 - profundidade + profundidade * np.sin(2 * np.pi * frequencia * t)).astype(np.float32)


def saturar(x, ganho):
    return (np.tanh(ganho * x) / np.tanh(ganho)).astype(np.float32)


def envelope(x, taxa, janela=0.02):
    n = max(1, int(taxa * janela))
    return np.convolve(np.abs(x), np.ones(n) / n, mode="same").astype(np.float32)


def sussurro(x, taxa, ganho, semente):
    """Ruído que segue o volume da fala: uma respiração/chiado junto das palavras."""
    ruido = np.random.default_rng(semente).standard_normal(len(x)).astype(np.float32)
    # Banda 1,8–5 kHz: ruído branco puro virava chiado de rádio e escondia o grave (brilho medido 4,2 kHz).
    banda = passa_baixa(passa_alta(ruido, taxa, 1800), taxa, 5000)
    banda /= np.max(np.abs(banda)) + 1e-9
    return ganho * banda * envelope(x, taxa)


def reverberar(x, taxa, duracao, mistura, semente):
    """Reverb por convolução com resposta sintética (ruído com decaimento): sala grande de pedra."""
    n_ir = int(taxa * duracao)
    rng = np.random.default_rng(semente)
    ir = rng.standard_normal(n_ir).astype(np.float32) * np.exp(-np.linspace(0, 6.9, n_ir)).astype(np.float32)
    ir = passa_baixa(ir, taxa, 4000)
    ir /= np.sqrt(np.sum(ir**2)) + 1e-9
    comprimento = len(x) + n_ir
    molhado = np.fft.irfft(np.fft.rfft(x, comprimento) * np.fft.rfft(ir, comprimento), n=comprimento).astype(np.float32)
    seco = np.pad(x, (0, n_ir))
    molhado *= np.max(np.abs(seco)) / (np.max(np.abs(molhado)) + 1e-9)
    return (1 - mistura) * seco + mistura * molhado


def drone(comprimento, taxa, ganho, semente):
    """Zumbido grave de fundo que entra e sai devagar: sensação de ameaça antes da primeira palavra."""
    t = np.arange(comprimento) / taxa
    tom = np.sin(2 * np.pi * 43 * t) + 0.6 * np.sin(2 * np.pi * 64.5 * t + 1.3)
    ronco = passa_baixa(np.random.default_rng(semente).standard_normal(comprimento).astype(np.float32), taxa, 120)
    ronco /= np.max(np.abs(ronco)) + 1e-9
    fade = np.minimum(1, np.minimum(t / 1.2, (t[-1] - t) / 1.5))
    return (ganho * (0.6 * tom + 0.8 * ronco) * np.clip(fade, 0, 1)).astype(np.float32)


def com_respiro_inicial(x, taxa, segundos):
    return np.concatenate([np.zeros(int(taxa * segundos), dtype=np.float32), x])


def normalizar(x, pico=0.89):
    return (x * (pico / (np.max(np.abs(x)) + 1e-9))).astype(np.float32)


# ---------------------------------------------------------------- personagens

def voz_simples(fator_grave=1.0, reverb=0.0):
    def cadeia(x, taxa):
        y = esticar(x, 1 / fator_grave) if fator_grave != 1.0 else x
        if reverb:
            y = reverberar(y, taxa, 0.6, reverb, 3)
        return normalizar(y)
    return cadeia


def fera_principal(x, taxa):
    y = esticar(x, 1.38)                      # ~5,5 semitons abaixo e mais lento
    y = dobrar(y, taxa, 1.04, 0.035, 0.55)    # segunda voz desafinada, atrás da primeira
    y = rosnar(y, taxa, 33, 0.45)
    y = saturar(y, 2.6)
    y = passa_baixa(y, taxa, 3000)
    y = y + sussurro(y, taxa, 0.9, 11)
    y = com_respiro_inicial(y, taxa, 0.6)
    y = reverberar(y, taxa, 2.6, 0.42, 7)
    return normalizar(y + drone(len(y), taxa, 0.10, 5))


def fera_abismo(x, taxa):
    y = esticar(x, 1.6)
    y = dobrar(y, taxa, 1.06, 0.05, 0.7)
    y = rosnar(y, taxa, 27, 0.35)
    y = saturar(y, 1.8)
    y = passa_baixa(y, taxa, 2300)
    y = com_respiro_inicial(y, taxa, 1.2)
    y = reverberar(y, taxa, 3.4, 0.55, 8)
    return normalizar(y + drone(len(y), taxa, 0.14, 6))


def fera_sussurro(x, taxa):
    base = esticar(x, 1.22)
    y = 0.45 * passa_alta(base, taxa, 250) + sussurro(base, taxa, 2.5, 12)
    y = dobrar(y, taxa, 0.97, 0.02, 0.5)      # voz dupla levemente mais aguda: sensação de "duas bocas"
    y = com_respiro_inicial(y, taxa, 0.7)
    y = reverberar(y, taxa, 2.0, 0.35, 9)
    return normalizar(y + drone(len(y), taxa, 0.07, 7))


PAUSAS_TOMAS = {"pausa_frase": 0.28, "pausa_reticencias": 0.55}

FALAS = [
    {
        "id": "narrador_intro", "personagem": "Narrador", "texto": TEXTO_NARRADOR, "origem": "texto da cena (dados/mundo.json)",
        "sintese": {"length_scale": 1.1}, "pausas": {"pausa_frase": 0.35, "pausa_reticencias": 0.5},
        "cadeia": voz_simples(0.95), "efeitos": "altura -0,9 semitom; pausas de 0,35 s entre frases",
    },
    {
        "id": "tomas_filha", "personagem": "Tomás", "texto": TEXTO_TOMAS, "origem": ORIGEM_QWEN,
        "sintese": {"length_scale": 1.02, "noise_scale": 0.78, "noise_w_scale": 0.95}, "pausas": PAUSAS_TOMAS,
        "cadeia": voz_simples(1.04, reverb=0.07),
        "efeitos": "fala frase a frase (pausa de 0,55 s nas reticências), mais variação de entonação (noise 0,78), altura +0,7 semitom, ambiente leve",
    },
    {
        "id": "odran_preco", "personagem": "Odran, o Mercador", "texto": TEXTO_ODRAN, "origem": ORIGEM_QWEN,
        "sintese": {"length_scale": 1.15}, "pausas": {"pausa_frase": 0.3, "pausa_reticencias": 0.5},
        "cadeia": voz_simples(0.92), "efeitos": "altura -1,4 semitom; pausas de 0,3 s",
    },
    {
        "id": "fera_desperta", "personagem": "A Fera (manifestação da Ira)", "texto": TEXTO_FERA, "origem": ORIGEM_LLAMA,
        "sintese": {"length_scale": 1.08, "noise_scale": 0.85, "noise_w_scale": 1.0}, "pausas": {"pausa_frase": 0.45, "pausa_reticencias": 0.7},
        "cadeia": fera_principal,
        "efeitos": "altura -5,5 semitons; segunda voz desafinada (+4%, 35 ms); rosnado por modulação em anel (33 Hz); saturação; passa-baixa 3 kHz; sussurro que segue a fala; 0,9 s de silêncio inicial; reverb de 2,6 s; drone grave (43/64 Hz)",
    },
]

VARIANTES_FALAS = [
    {
        "id": "fera_v2_abismo", "personagem": "A Fera", "texto": TEXTO_FERA, "origem": ORIGEM_LLAMA,
        "sintese": {"length_scale": 1.0, "noise_scale": 0.85}, "pausas": {"pausa_frase": 0.5, "pausa_reticencias": 0.8},
        "cadeia": fera_abismo, "efeitos": "mais grave (-8 semitons), voz dupla mais afastada, reverb de catedral (3,4 s), drone mais alto",
    },
    {
        "id": "fera_v3_sussurro", "personagem": "A Fera", "texto": TEXTO_FERA, "origem": ORIGEM_LLAMA,
        "sintese": {"length_scale": 1.12, "noise_scale": 0.9}, "pausas": {"pausa_frase": 0.45, "pausa_reticencias": 0.7},
        "cadeia": fera_sussurro, "efeitos": "sussurro rouco dominante com voz dupla, como algo falando dentro da cabeça",
    },
    {
        "id": "tomas_v2_calmo", "personagem": "Tomás", "texto": TEXTO_TOMAS, "origem": ORIGEM_QWEN,
        "sintese": {"length_scale": 1.12, "noise_scale": 0.65}, "pausas": {"pausa_frase": 0.35, "pausa_reticencias": 0.7},
        "cadeia": voz_simples(1.0, reverb=0.05), "efeitos": "mais lento e cansado, pausas longas, sem mudar a altura",
    },
    {
        "id": "tomas_v3_nervoso", "personagem": "Tomás", "texto": TEXTO_TOMAS, "origem": ORIGEM_QWEN,
        "sintese": {"length_scale": 0.95, "noise_scale": 0.9, "noise_w_scale": 1.1}, "pausas": {"pausa_frase": 0.2, "pausa_reticencias": 0.45},
        "cadeia": voz_simples(1.08, reverb=0.07), "efeitos": "mais rápido e agudo (+1,3 semitom), entonação irregular",
    },
]


def gravar(arquivo, y, taxa):
    with wave.open(str(arquivo), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(taxa)
        wav.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    SAIDA.mkdir(parents=True, exist_ok=True)
    VARIANTES.mkdir(parents=True, exist_ok=True)
    voz = PiperVoice.load(VOZ)
    manifesto = {}
    for lista, pasta, principal in ((FALAS, SAIDA, True), (VARIANTES_FALAS, VARIANTES, False)):
        for item in lista:
            inicio = time.perf_counter()
            bruto, taxa = sintetizar(voz, item["texto"], item["sintese"], **item["pausas"])
            final = item["cadeia"](bruto, taxa)
            segundos = time.perf_counter() - inicio
            arquivo = pasta / f"{item['id']}.wav"
            gravar(arquivo, final, taxa)
            espectro = np.abs(np.fft.rfft(final)) ** 2
            freqs = np.fft.rfftfreq(len(final), 1 / taxa)
            centroide = float(np.sum(freqs * espectro) / (np.sum(espectro) + 1e-9))
            grave = float(np.sum(espectro[freqs < 300]) / np.sum(espectro) * 100)
            agudo = float(np.sum(espectro[freqs > 4000]) / np.sum(espectro) * 100)
            registro = {k: v for k, v in item.items() if k != "cadeia"}
            manifesto[item["id"]] = {
                **registro,
                "principal": principal,
                "arquivo": str(arquivo.relative_to(BASE)).replace("\\", "/"),
                "ferramenta": "Piper TTS 1.8 (local, ONNX) + pós-processamento numpy",
                "modelo": "rhasspy/piper-voices pt_BR-faber-medium",
                "duracao_s": round(len(final) / taxa, 1),
                "tempo_geracao_s": round(segundos, 2),
                "brilho_hz": round(centroide),
                "energia_abaixo_300hz_pct": round(grave, 1),
                "energia_acima_4khz_pct": round(agudo, 1),
                "gerado_em": datetime.now().isoformat(timespec="seconds"),
            }
            print(f"{item['id']:<18} {len(final) / taxa:5.1f} s · gerado em {segundos:.2f} s · brilho {centroide:5.0f} Hz"
                  f" · grave {grave:4.1f}% · agudo {agudo:4.1f}%")
    MANIFESTO.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
