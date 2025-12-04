import streamlit as st
import pandas as pd
import plotly.express as px
import glob
import re
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Simulação Daily.dss", layout="wide")

col_logo, col_titulo = st.columns([1, 4])
with col_logo:
    st.markdown(
        """
        <div align="center">
        <a target="_blank" href="https://github.com/grei-ufc" style="background:none">
            <img src="https://raw.githubusercontent.com/grei-ufc/tsdq-dataview-opentes/main/imagens/Ilustra%C3%A7%C3%A3o%20fontes%20e%20transmissao.png" width="150">
        </a>
        </div>
        """,
        unsafe_allow_html=True
    )
with col_titulo:
    st.title("OpenTES - TSDQ")

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

st.markdown("""
Painel interativo para visualização dos resultados obtidos a partir dos monitores do arquivo `Daily.dss`.
""")

st.subheader("Seleção de tipo de variável")
tipo_variavel = st.radio(
    "Escolha o tipo de variável:",
    ["Tensão, corrente e ângulo", "Potência ativa e reativa"],
    horizontal=True
)

st.divider()

# Mapa de arquivos com bases para conversão pu
mapa_arquivos = {
    "Tensão Subestação": {
        "path": "Exemplos/Daily/Equivalente_Mon_tensaosub_1*.csv",
        "base": 79674.3  # Tensão base fase-neutro em V (138 kV/sqrt(3))
    },
    "Tensão Carga D": {
        "path": "Exemplos/Daily/Equivalente_Mon_tensaocargad_1*.csv",
        "base": 7967.4   # Tensão base fase-neutro em V (13.8 kV/sqrt(3))
    },
    "Potência Subestação": {
        "path": "Exemplos/Daily/Equivalente_Mon_potenciasub_1*.csv",
        "base": 3000000  # Potência base em VA (3000 kVA)
    },
    "Potência Carga D": {
        "path": "Exemplos/Daily/Equivalente_Mon_potenciacargad_1*.csv",
        "base": 2000000  # Potência base em W (2000 kW) - ajustar conforme necessidade
    },
}

def sanitize_columns(cols):
    return [c.strip().replace(" ", "_").replace("(", "").replace(")", "") for c in cols]

@st.cache_data
def carregar_dados(padrao_arquivo, base_value=None):
    arquivos = glob.glob(padrao_arquivo)
    if not arquivos:
        return None
    df = pd.read_csv(arquivos[0])
    df.columns = sanitize_columns(df.columns)
    
    # Se base_value for fornecido, converte colunas relevantes para pu
    if base_value is not None:
        # Identifica colunas de tensão (V1, V2, V3, Vmag1, etc.)
        tensao_cols = [c for c in df.columns if c.startswith('V') and c[1:].replace('mag', '').isdigit()]
        # Identifica colunas de potência (P1, P2, P3, etc.)
        potencia_cols = [c for c in df.columns if c.startswith('P') or c.startswith('Q')]
        
        cols_para_converter = tensao_cols + potencia_cols
        
        for col in cols_para_converter:
            if col in df.columns:
                df[col] = df[col] / base_value
    
    return df

def detectar_grupo(df, canal):
    if canal.startswith(("V", "v")):
        grupo = [c for c in df.columns if re.match(r"V\d", c)]
        titulo = "Tensões [pu]"
    elif canal.startswith(("I", "i")):
        grupo = [c for c in df.columns if re.match(r"I\d", c)]
        titulo = "Correntes"
    elif canal.startswith(("P", "p")):
        grupo = [c for c in df.columns if c.startswith("P")]
        titulo = "Potências Ativas [pu]"
    elif canal.startswith(("Q", "q")):
        grupo = [c for c in df.columns if c.startswith("Q")]
        titulo = "Potências Reativas [pu]"
    else:
        grupo = []
        titulo = ""
    return grupo, titulo

def carregar_e_plotar(nome_monitor, monitor_info, monitor_key):
    df = carregar_dados(monitor_info["path"], monitor_info.get("base"))
    if df is None:
        st.error(f"Nenhum arquivo encontrado para {nome_monitor}.")
        return None, None, None, None

    eixo_x = next((c for c in df.columns if c.lower() in ["hour", "time"]), df.columns[0])
    colunas_y = [c for c in df.columns if c != eixo_x]

    st.subheader(f"{nome_monitor} (valores em pu)")

    canal = st.selectbox(
        f"Selecione o canal para {nome_monitor}:",
        colunas_y,
        key=f"single_{nome_monitor}_{monitor_key}"
    )

    grupo, titulo = detectar_grupo(df, canal)

    col1, col2 = st.columns(2)

    with col1:
        # Verifica se é tensão ou potência para adicionar [pu] no eixo Y
        yaxis_label = f"{canal}"
        if canal.startswith(('V', 'P', 'Q')):
            yaxis_label = f"{canal} [pu]"
            
        fig = px.line(df, x=eixo_x, y=canal, title=f"{nome_monitor} - {canal}", markers=True)
        fig.update_layout(xaxis_title="Hora", yaxis_title=yaxis_label, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        if grupo:
            fig2 = px.line(df, x=eixo_x, y=grupo, title=f"{nome_monitor} - {titulo}", markers=True)
            fig2.update_layout(xaxis_title="Hora", yaxis_title=titulo, template="plotly_white")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Tipo de variável não identificado para exibição em grupo.")

    with st.expander("Ver tabela de dados"):
        st.dataframe(df)

    return df, eixo_x, canal, grupo

# Inicializar variáveis
df_sub = None
df_carga = None

with st.container():
    if tipo_variavel == "Tensão, corrente e ângulo":
        tab1, tab2 = st.tabs(["Tensão Subestação", "Tensão Carga D"])
        with tab1:
            df_sub, eixo_x_sub, canal_sub, grupo_sub = carregar_e_plotar(
                "Tensão Subestação", mapa_arquivos["Tensão Subestação"], "sub"
            )
        with tab2:
            df_carga, eixo_x_carga, canal_carga, grupo_carga = carregar_e_plotar(
                "Tensão Carga D", mapa_arquivos["Tensão Carga D"], "carga"
            )

    elif tipo_variavel == "Potência ativa e reativa":
        tab1, tab2 = st.tabs(["Potência Subestação", "Potência Carga D"])
        with tab1:
            df_sub, eixo_x_sub, canal_sub, grupo_sub = carregar_e_plotar(
                "Potência Subestação", mapa_arquivos["Potência Subestação"], "sub"
            )
        with tab2:
            df_carga, eixo_x_carga, canal_carga, grupo_carga = carregar_e_plotar(
                "Potência Carga D", mapa_arquivos["Potência Carga D"], "carga"
            )

st.divider()
st.subheader("Visualização 3D (valores em pu)")

# Seletor para escolher qual conjunto de dados usar no 3D
opcoes_3d = []
if df_sub is not None:
    opcoes_3d.append("Subestação")
if df_carga is not None:
    opcoes_3d.append("Carga D")

if opcoes_3d:
    selecao_3d = st.selectbox("Selecione o conjunto de dados para visualização 3D:", opcoes_3d)
    
    if selecao_3d == "Subestação" and df_sub is not None:
        df = df_sub
        eixo_x = eixo_x_sub
        grupo = grupo_sub
        titulo_base = "Subestação"
    elif selecao_3d == "Carga D" and df_carga is not None:
        df = df_carga
        eixo_x = eixo_x_carga
        grupo = grupo_carga
        titulo_base = "Carga D"
    else:
        df = None
        grupo = []
    
    if df is not None and grupo:
        x_vals = df[eixo_x].values
        y_vals = np.arange(len(grupo))
        X, Y = np.meshgrid(x_vals, y_vals)
        Z = df[grupo].values.T
        
        # Determinar tipo de variável para rótulo do eixo Z
        z_label = "Magnitude"
        if grupo[0].startswith('V'):
            z_label = "Tensão [pu]"
        elif grupo[0].startswith('P'):
            z_label = "Potência Ativa [pu]"
        elif grupo[0].startswith('Q'):
            z_label = "Potência Reativa [pu]"
        
        fig3d = go.Figure(data=[go.Surface(
            x=X,
            y=Y,
            z=Z,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title=z_label)
        )])
        
        fig3d.update_layout(
            title=f"Visualização 3D - {titulo_base} (valores em pu)",
            scene=dict(
                xaxis_title="Tempo [h]",
                yaxis_title="Variáveis",
                zaxis_title=z_label,
                yaxis=dict(
                    ticktext=grupo,
                    tickvals=y_vals
                )
            ),
            height=600
        )
        
        st.plotly_chart(fig3d, use_container_width=True)
        
        # Adicionar estatísticas
        with st.expander("Estatísticas dos valores em pu"):
            col_stats1, col_stats2 = st.columns(2)
            with col_stats1:
                st.markdown("**Valores médios por variável:**")
                medias = df[grupo].mean()
                st.dataframe(medias.rename("Média [pu]").to_frame())
            with col_stats2:
                st.markdown("**Valores máximos por variável:**")
                maximos = df[grupo].max()
                st.dataframe(maximos.rename("Máximo [pu]").to_frame())
    else:
        st.warning("Não há dados suficientes para gerar o gráfico 3D.")
else:
    st.warning("Nenhum dado carregado para visualização 3D.")