import streamlit as st
import pandas as pd
import plotly.express as px
import glob
import os
import re

st.set_page_config(page_title="Simulação Daily.dss", layout="wide")

# ========================
# TÍTULO
# ========================
st.title("OpenTES - TSDQ")

st.markdown("""
Painel interativo para visualização dos resultados de **tensão** e **potência**
obtidos a partir dos monitores do arquivo `Daily.dss`.
""")

# ========================
# MENU LATERAL
# ========================
st.sidebar.header("⚙️ Configurações")

tipo_variavel = st.sidebar.radio("Escolha o tipo de variável:", ["Tensão", "Potência"])

# ========================
# BADGES E LOGO
# ========================
st.sidebar.markdown("""
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)  
[![Grei](https://img.shields.io/badge/-GREI-Black?logo=INSPIRE&logoColor=blue&color=42b85a&labelColor=white&style=flat)](https://www.linkedin.com/company/grei-ufc/?originalSubdomain=br)  
[![Python](https://img.shields.io/badge/-Python%20Version%20|%203.12.11-42b85a?logo=Python&logoColor=fbec41&color=42b85a&labelColor=grey&style=flat)](https://www.python.org/downloads/release/python-31112/)  
[![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?logo=discord&logoColor=white)](https://discord.com/channels/1415180099644297368/1415431164717564065)  
""", unsafe_allow_html=True)



# ========================
# MAPEAMENTO DE ARQUIVOS
# ========================
mapa_arquivos = {
    "Tensão Subestação": "Equivalente_Mon_tensaosub_1*.csv",
    "Tensão Carga D": "Equivalente_Mon_tensaocargad_1*.csv",
    "Potência Subestação": "Equivalente_Mon_potenciasub_1*.csv",
    "Potência Carga D": "Equivalente_Mon_potenciacargad_1*.csv",
}

# ========================
# HELPERS
# ========================
def sanitize_columns(cols):
    return [c.strip().replace(" ", "_").replace("(", "").replace(")", "") for c in cols]

def find_phase_triplet(cols):
    """
    Procura por um trio de colunas que representem fases 1,2,3.
    Estratégia:
      1) procurar colunas que terminam com '1' e checar se prefix+'2' e prefix+'3' existem
      2) procurar colunas que contenham '_1' (ou '.1') e checar os correspondentes
    Retorna lista com 3 nomes ou None.
    """
    col_set = set(cols)

    # 1) padrão simples: termina com digit 1
    for c in cols:
        m = re.match(r"^(.*?)(?:[_\.])?1$", c)  # pega prefixo se terminar com 1 ou _1 ou .1
        if m:
            prefix = m.group(1)
            c2 = prefix + "2"
            c3 = prefix + "3"
            # considerar também prefix + "_2" e prefix + "_3"
            candidates = [c2, c3, prefix + "_2", prefix + "_3", prefix + ".2", prefix + ".3"]
            if any(x in col_set for x in [c2, c3]):
                if c2 in col_set and c3 in col_set:
                    return [c, c2, c3]
            elif any(x in col_set for x in candidates):
                found2 = next((x for x in candidates if x in col_set), None)
                # se encontrou algum, tentar achar o outro correspondente simples
                if found2:
                    # deduz sufixo do encontrado
                    suffix = found2[len(prefix):]  # por exemplo "_2" ou "2"
                    alt2 = prefix + "2"
                    alt3 = prefix + "3"
                    # montar nomes tentando manter formato
                    name2 = prefix + suffix  # o que achou
                    name3 = prefix + suffix.replace("2", "3")
                    if name2 in col_set and name3 in col_set:
                        return [c, name2, name3]

    # 2) fallback: procurar padrões comuns (V1,V2,V3 ou P1,P2,P3)
    for base in ["V", "Voltage", "P", "Power", "I", "Current"]:
        cand = [f"{base}1", f"{base}2", f"{base}3"]
        if all(x in col_set for x in cand):
            return cand

    return None

# ========================
# FUNÇÃO DE LEITURA E PLOT (CANAL ÚNICO)
# ========================
def carregar_e_plotar(nome_monitor, padrao_arquivo):
    arquivos = glob.glob(padrao_arquivo)
    if not arquivos:
        st.error(f"Nenhum arquivo encontrado para **{nome_monitor}**.")
        return

    arquivo = arquivos[0]
    df = pd.read_csv(arquivo)
    df.columns = sanitize_columns(df.columns)

    # Identificar eixo X (hora)
    if "hour" in df.columns:
        eixo_x = "hour"
    elif "Time" in df.columns:
        eixo_x = "Time"
    else:
        eixo_x = df.columns[0]

    colunas_y = [c for c in df.columns if c != eixo_x]

    st.subheader(f" {nome_monitor}")
    canal = st.selectbox(f"Selecione o canal para {nome_monitor}:", colunas_y, key=f"single_{nome_monitor}")

    fig = px.line(df, x=eixo_x, y=canal, title=f"{nome_monitor} - {canal}", markers=True)
    fig.update_layout(xaxis_title="Hora", yaxis_title=canal, template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("🔍 Ver tabela de dados"):
        st.dataframe(df)

    # --- novo gráfico com as 3 fases (se houver) ---
    triplet = find_phase_triplet(df.columns)
    if triplet:
        # assegurar que sejam apresentadas apenas as três fases corretas (na ordem 1,2,3)
        # ordenar para 1,2,3 conforme sufixo
        def sort_key(name):
            m = re.search(r"([_\.]?)(1|2|3)$", name)
            if m:
                return int(m.group(2))
            # tentar último caractere como fallback
            try:
                return int(name[-1])
            except:
                return 0
        triplet_sorted = sorted(triplet, key=sort_key)

        st.markdown("####  Gráfico das 3 fases")
        fig2 = px.line(df, x=eixo_x, y=triplet_sorted, title=f"{nome_monitor} - fases ({', '.join(triplet_sorted)})", markers=True)
        fig2.update_layout(xaxis_title="Hora", yaxis_title="Valor", template="plotly_white")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Não foi possível identificar automaticamente as 3 colunas de fase (1,2,3) para este monitor.")

# ========================
# EXIBIÇÃO DE ABAS DEPENDENDO DA ESCOLHA
# ========================
if tipo_variavel == "Tensão":
    tab1, tab2 = st.tabs(["Tensão Subestação", "Tensão Carga D"])
    with tab1:
        carregar_e_plotar("Tensão Subestação", mapa_arquivos["Tensão Subestação"])
    with tab2:
        carregar_e_plotar("Tensão Carga D", mapa_arquivos["Tensão Carga D"])

elif tipo_variavel == "Potência":
    tab1, tab2 = st.tabs(["Potência Subestação", "Potência Carga D"])
    with tab1:
        carregar_e_plotar("Potência Subestação", mapa_arquivos["Potência Subestação"])
    with tab2:
        carregar_e_plotar("Potência Carga D", mapa_arquivos["Potência Carga D"])
