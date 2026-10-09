"""Painel de teste da API do OS 7 PECADOS (Streamlit + requests).

Rodar (com a API no ar):
    streamlit run painel/app.py
"""

import json
import os
import sys
from pathlib import Path

import streamlit as st
from cliente_api import ClienteAPI, ErroAPI

# Reaproveita os prompts e schemas reais do jogo: o painel testa exatamente o que o jogo envia.
PROTOTIPO = Path(__file__).resolve().parent.parent / "prototipo"
sys.path.insert(0, str(PROTOTIPO))
import prompts  # noqa: E402
from estado import NPC, Jogador, carregar_mundo  # noqa: E402
from jogo import SCHEMA_CLASSIFICACAO, SCHEMA_TURNO  # noqa: E402

MUNDO = carregar_mundo(PROTOTIPO / "dados" / "mundo.json")

st.set_page_config(page_title="OS 7 PECADOS · Painel da API", layout="wide")
st.title("OS 7 PECADOS · Painel da API")
st.caption("Consome a API FastAPI do grupo via requests. Nenhuma chamada sai daqui direto para o Ollama ou o Piper.")

# ---------- conexão ----------

with st.sidebar:
    st.header("Conexão")
    url = st.text_input("URL da API", os.environ.get("OS7_API_URL", "http://localhost:8000"))
    chave = st.text_input("X-API-Key", os.environ.get("OS7_API_KEY", ""), type="password")
    api = ClienteAPI(url, chave)

    if st.button("Verificar status", width="stretch"):
        try:
            api.health()
            status = api.status()
        except ErroAPI as erro:
            st.error(str(erro))
        else:
            st.write(f"Modelo de texto: `{status['modelo_texto']}`")
            for modalidade in ("texto", "voz"):
                rotulo = f"{modalidade.capitalize()}: {status['detalhe'][modalidade]}"
                (st.success if status[modalidade] else st.warning)(rotulo)
    st.link_button("Abrir Swagger (/docs)", f"{url.rstrip('/')}/docs", width="stretch")


def mostrar_chamada():
    if api.ultima:
        c = api.ultima
        st.caption(f"`{c['metodo']} {c['rota']}` · HTTP {c['codigo']} · {c['ms']} ms")


def falhou(erro):
    mostrar_chamada()
    if erro.codigo == 401:
        st.error("Chave recusada (401). Confira a X-API-Key na barra lateral.")
    elif erro.codigo == 503:
        st.warning(f"IA indisponível (503). No jogo, isso ativa o modo offline.\n\n{erro}")
    else:
        st.error(str(erro))


aba_npc, aba_class, aba_voz, aba_livre = st.tabs(["Fala de NPC", "Classificar intenção", "Voz", "Texto livre"])

# ---------- NPC: a mesma cadeia de um turno do jogo ----------

with aba_npc:
    st.write("Simula um turno do jogo: classifica a intenção, gera a fala do NPC e, se quiser, a voz.")
    nomes = {ficha["nome"]: ficha for ficha in MUNDO["npcs"]}
    nome = st.selectbox("NPC", list(nomes))
    fala_jogador = st.text_input("O inquisitor diz", "Solte esse homem ou eu arranco sua cabeça!", key="fala_npc")
    com_voz = st.checkbox("Gerar voz da resposta", value=True)

    if st.button("Enviar", type="primary"):
        npc, jogador = NPC(**nomes[nome]), Jogador()
        try:
            with st.spinner("Classificando intenção..."):
                classe = api.texto(prompts.mensagens_classificacao(fala_jogador), SCHEMA_CLASSIFICACAO, 0)
            intencao = classe["conteudo"]["intencao"]
            intensidade = classe["conteudo"]["intensidade"]
            with st.spinner(f"{nome} está pensando..."):
                turno = api.texto(
                    prompts.mensagens_turno(npc, jogador, MUNDO["cena"], fala_jogador, intencao, intensidade),
                    SCHEMA_TURNO,
                )
        except ErroAPI as erro:
            falhou(erro)
        else:
            conteudo = turno["conteudo"]
            st.markdown(f"**{nome}** ({conteudo['emocao']}): {conteudo['fala']}")
            col1, col2, col3 = st.columns(3)
            col1.metric("Intenção", f"{intencao} ({intensidade})")
            col2.metric("Latência total", f"{classe['latencia_ms'] + turno['latencia_ms']} ms")
            col3.metric("Modelo", turno["modelo"])
            if conteudo.get("memoria"):
                st.caption(f"Memória gravada pelo NPC: {conteudo['memoria']}")
            if com_voz:
                try:
                    with st.spinner("Sintetizando voz..."):
                        st.audio(api.voz(conteudo["fala"]), format="audio/wav")
                except ErroAPI as erro:
                    falhou(erro)
            mostrar_chamada()

# ---------- classificador ----------

with aba_class:
    st.write("Usa o mesmo prompt few-shot e o mesmo JSON Schema do jogo (temperatura 0).")
    frase = st.text_input("Frase do jogador", "Te pago 50 moedas para esquecer isso.", key="frase_class")
    if st.button("Classificar"):
        try:
            resultado = api.texto(prompts.mensagens_classificacao(frase), SCHEMA_CLASSIFICACAO, 0)
        except ErroAPI as erro:
            falhou(erro)
        else:
            st.json(resultado)
            mostrar_chamada()

# ---------- voz ----------

with aba_voz:
    texto_voz = st.text_area(
        "Texto",
        "Cinzaforte, cidade tomada pela Ira. Uma multidão furiosa cerca Tomás, acusado de roubar um amuleto de ouro.",
    )
    velocidade = st.slider("Velocidade", 0.5, 2.0, 1.0, 0.1)
    if st.button("Sintetizar"):
        try:
            audio = api.voz(texto_voz, velocidade)
        except ErroAPI as erro:
            falhou(erro)
        else:
            st.audio(audio, format="audio/wav")
            st.download_button("Baixar WAV", audio, "voz.wav", "audio/wav")
            mostrar_chamada()

# ---------- texto livre ----------

with aba_livre:
    sistema = st.text_area("Mensagem de sistema", "Você é o Demônio Interior do inquisitor. Fale em uma frase curta.")
    usuario = st.text_area("Mensagem do usuário", "Acabei de matar a Capitã Brenna.")
    schema_txt = st.text_area("JSON Schema da resposta (opcional)", "", placeholder='{"type": "object", ...}')
    temperatura = st.slider("Temperatura", 0.0, 1.5, 0.5, 0.1)
    if st.button("Gerar"):
        try:
            schema = json.loads(schema_txt) if schema_txt.strip() else None
        except json.JSONDecodeError as erro:
            st.error(f"JSON Schema inválido: {erro}")
        else:
            mensagens = [{"role": "system", "content": sistema}, {"role": "user", "content": usuario}]
            try:
                st.json(api.texto(mensagens, schema, temperatura))
            except ErroAPI as erro:
                falhou(erro)
            else:
                mostrar_chamada()
