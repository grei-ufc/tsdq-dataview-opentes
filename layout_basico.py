import streamlit as st
import pandas as pd
import plotly.express as px
import glob
import re

# ========================
# CONFIGURAÇÕES INICIAIS
# ========================
st.set_page_config(page_title="Simulação Daily.dss", layout="wide")

# ========================
# CABEÇALHO COM LOGO E TÍTULO
# ========================
col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    st.markdown(
        """
        <div align="center">
        <a target="_blank" href="https://github.com/grei-ufc" style="background:none">
            <img src="https://raw.githubusercontent.com/grei-ufc/tsdq-dataview-opentes/main/imagens/Grei2.png" width="100">
        </a>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_titulo:
    st.title("OpenTES - TSDQ")

# ========================
# BADGES EM LINHA
# ========================
st.markdown("""
<div style="display: flex; justify-content: center; gap: 10px; margin: 10px 0;">
    <a target="_blank" href="https://github.com/astral-sh/uv">
        <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json" alt="uv">
    </a>
    <a target="_blank" href="https://www.linkedin.com/company/grei-ufc/?originalSubdomain=br">
        <img src="https://img.shields.io/badge/-GREI-Black?logo=INSPIRE&logoColor=blue&color=42b85a&labelColor=white&style=flat" alt="Grei">
    </a>
    <a target="_blank" href="https://www.python.org/downloads/release/python-31112/">
        <img src="https://img.shields.io/badge/-Python%20Version%20|%203.12.11-42b85a?logo=Python&logoColor=fbec41&color=42b85a&labelColor=grey&style=flat" alt="Python">
    </a>
    <a target="_blank" href="https://discord.com/channels/1415180099644297368/1415431164717564065">
        <img src="https://img.shields.io/badge/Discord-%235865F2.svg?logo=discord&logoColor=white" alt="Discord">
    </a>
</div>
""", unsafe_allow_html=True)

# ========================
# DESCRIÇÃO
# ========================
st.markdown("""
Painel interativo para visualização dos resultados de **tensão** e **potência**
obtidos a partir dos monitores do arquivo `Daily.dss`.
""")

# ========================
# SELETOR DE VARIÁVEIS
# ========================
st.subheader("Seleção de tipo de variável")
tipo_variavel = st.radio(
    "Escolha o tipo de variável:",
    ["Tensão, corrente e ângulo", "Potência ativa e reativa"],
    horizontal=True
)
st.divider()

# ========================
# MAPEAMENTO DE ARQUIVOS
# ========================
mapa_arquivos = {
    "Tensão Subestação": "Exemplos/Daily/Equivalente_Mon_tensaosub_1*.csv",
    "Tensão Carga D": "Exemplos/Daily/Equivalente_Mon_tensaocargad_1*.csv",
    "Potência Subestação": "Exemplos/Daily/Equivalente_Mon_potenciasub_1*.csv",
    "Potência Carga D": "Exemplos/Daily/Equivalente_Mon_potenciacargad_1*.csv",
}

# ========================
# FUNÇÕES AUXILIARES
# ========================
def sanitize_columns(cols):
    """Remove espaços e símbolos dos nomes das colunas."""
    return [c.strip().replace(" ", "_").replace("(", "").replace(")", "") for c in cols]


@st.cache_data
def carregar_dados(padrao_arquivo):
    """Carrega e limpa dados CSV, com cache para otimizar desempenho."""
    arquivos = glob.glob(padrao_arquivo)
    if not arquivos:
        return None
    df = pd.read_csv(arquivos[0])
    df.columns = sanitize_columns(df.columns)
    return df


# ========================
# FUNÇÃO PRINCIPAL DE PLOTAGEM MODIFICADA
# ========================
def carregar_e_plotar(nome_monitor, padrao_arquivo):
    df = carregar_dados(padrao_arquivo)
    if df is None:
        st.error(f"Nenhum arquivo encontrado para **{nome_monitor}**.")
        return

    eixo_x = next((c for c in df.columns if c.lower() in ["hour", "time"]), df.columns[0])
    colunas_y = [c for c in df.columns if c != eixo_x]

    with st.container():
        st.subheader(f"{nome_monitor}")

        canal = st.selectbox(
            f"Selecione o canal para {nome_monitor}:",
            colunas_y,
            key=f"single_{nome_monitor}"
        )

        # --- Detectar grupo de variáveis ---
        if canal.startswith(("V", "v")):
            grupo = [c for c in df.columns if re.match(r"V\d", c)]
            titulo = "Tensões (V1–V4)"
            ylabel = "Tensão (V)"
        elif canal.startswith(("I", "i")):
            grupo = [c for c in df.columns if re.match(r"I\d", c)]
            titulo = "Correntes (I1–I4)"
            ylabel = "Corrente (A)"
        elif canal.startswith(("P", "p")):
            grupo = [c for c in df.columns if c.startswith("P") and "kW" in c]
            titulo = "Potências Ativas (kW)"
            ylabel = "Potência Ativa (kW)"
        elif canal.startswith(("Q", "q")):
            grupo = [c for c in df.columns if c.startswith("Q") and "kvar" in c]
            titulo = "Potências Reativas (kvar)"
            ylabel = "Potência Reativa (kvar)"
        else:
            grupo = []
            titulo = ""
            ylabel = ""

        # CRIAR COLUNAS PARA OS GRÁFICOS
        col1, col2 = st.columns(2)  # Divide o container em 2 colunas

        with col1:
            # Gráfico individual do canal selecionado
            fig = px.line(df, x=eixo_x, y=canal, title=f"{nome_monitor} - {canal}", markers=True)
            fig.update_layout(xaxis_title="Hora", yaxis_title=canal, template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Gráfico do grupo de variáveis
            if grupo:
                fig2 = px.line(df, x=eixo_x, y=grupo, title=f"{nome_monitor} - {titulo}", markers=True)
                fig2.update_layout(xaxis_title="Hora", yaxis_title=ylabel, template="plotly_white")
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Tipo de variável não identificado para exibição em grupo.")

        with st.expander("🔍 Ver tabela de dados"):
            st.dataframe(df)


# ========================
# EXIBIÇÃO DE ABAS
# ========================
with st.container():
    if tipo_variavel == "Tensão, corrente e ângulo":
        tab1, tab2 = st.tabs(["Tensão Subestação", "Tensão Carga D"])
        with tab1:
            carregar_e_plotar("Tensão Subestação", mapa_arquivos["Tensão Subestação"])
        with tab2:
            carregar_e_plotar("Tensão Carga D", mapa_arquivos["Tensão Carga D"])

    elif tipo_variavel == "Potência ativa e reativa":
        tab1, tab2 = st.tabs(["Potência Subestação", "Potência Carga D"])
        with tab1:
            carregar_e_plotar("Potência Subestação", mapa_arquivos["Potência Subestação"])
        with tab2:
            carregar_e_plotar("Potência Carga D", mapa_arquivos["Potência Carga D"])