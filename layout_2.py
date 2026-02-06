import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import numpy as np

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Visualizador OpenDSS - Final")

# =======================================================
# FUNÇÕES VISUAIS
# =======================================================

def render_cabecalho():
    col_logo, col_titulo = st.columns([1, 4])
    with col_logo:
        st.markdown(
            """
            <div align="center">
            <a target="_blank" href="https://github.com/grei-ufc" style="background:none">
                <img src="https://raw.githubusercontent.com/grei-ufc/tsdq-dataview-opentes/main/imagens/Grei3.png" width="150">
            </a>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown(
        """
        <h1 style="text-align: center;">
            OpenTES - TSDQ
        </h1>
        """,
        unsafe_allow_html=True
    )
    st.markdown("<hr>", unsafe_allow_html=True)

# Função para colorir a tabela (Highlight PRODIST)
def colorir_tabela(val):
    color = ''
    if isinstance(val, (int, float)):
        if val < 0.87 or val > 1.06:
            color = 'background-color: #ffcccc; color: red; font-weight: bold;' # Crítico
        elif val < 0.92 or val > 1.05:
            color = 'background-color: #fff4cc; color: #b36b00;' # Precário
    return color

def render_grafico_3d(df, mapa_barras, usar_tempo_real, col_time):
    st.markdown("### 🧊 Visualização Topológica 3D")
    fase_selecionada = st.radio("Escolha a fase:", ["V1", "V2", "V3"], horizontal=True)
    
    lista_barras = sorted(list(mapa_barras.keys()))
    
    if usar_tempo_real:
        x_eixo = df[col_time]
        titulo_x = "Tempo (Data/Hora)"
    else:
        x_eixo = df.index
        titulo_x = "Passo de Simulação"

    y_barras = lista_barras
    z_data = []
    
    progresso = st.progress(0)
    for i, barra in enumerate(lista_barras):
        colunas = mapa_barras[barra]
        if fase_selecionada in colunas:
            z_data.append(df[colunas[fase_selecionada]].values)
        else:
            z_data.append(np.full(len(df), np.nan))
        progresso.progress((i + 1) / len(lista_barras))
        
    progresso.empty()
    z_matrix = np.array(z_data).T 

    fig = go.Figure(data=[go.Surface(
        z=z_matrix, x=y_barras, y=x_eixo,
        colorscale='Viridis', colorbar=dict(title='Tensão (pu)')
    )])

    fig.update_layout(
        title=f'Superfície de Tensão - Fase {fase_selecionada}',
        scene=dict(
            xaxis_title='Barras',
            yaxis_title=titulo_x,
            zaxis_title='Tensão (pu)',
            zaxis=dict(range=[0.85, 1.15]), 
        ),
        height=700, margin=dict(l=0, r=0, b=0, t=40)
    )
    st.plotly_chart(fig, use_container_width=True)

# =======================================================
# EXECUÇÃO PRINCIPAL
# =======================================================

render_cabecalho()

st.info("📂 Carregue o arquivo CSV gerado pelo OpenDSS.")
uploaded_file = st.file_uploader("Arraste seu CSV aqui", type=["csv"])

if uploaded_file is None:
    st.warning("⚠️ Aguardando upload...")
    st.stop() 

# 1. Leitura
df = pd.read_csv(uploaded_file)
df.columns = df.columns.str.strip() 

# 2. Tratamento de Tempo
if 'date' in df.columns:
    try:
        df['date'] = pd.to_datetime(df['date'], format='mixed')
    except:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    col_time = 'date'
elif 'Hora' in df.columns:
    col_time = 'Hora'
else:
    df['Passo'] = range(len(df))
    col_time = 'Passo'

# 3. MAPEAMENTO (Regex bus-xxx-v1_pu)
mapa_barras = {}
padrao = re.compile(r"Bus-([\w]+)-V(\d+)_pu")

for col in df.columns:
    match = padrao.search(col)
    if match:
        barra = match.group(1)
        fase = f"V{match.group(2)}"
        if barra not in mapa_barras: mapa_barras[barra] = {}
        mapa_barras[barra][fase] = col
        
if not mapa_barras:
    st.error("❌ Nenhuma coluna com formato 'Bus-XXX-Vn_pu' encontrada.")
    st.write("Colunas disponíveis:", df.columns.tolist())
    st.stop()

# 4. Interface Lateral
st.sidebar.header("Configurações")

modo_eixo_x = st.sidebar.radio(
    "Tipo de Eixo X (Tempo):",
    ["Passo de Simulação (Sequencial)", "Tempo Real (Data/Hora)"]
)

if modo_eixo_x == "Tempo Real (Data/Hora)" and col_time != 'Passo':
    df = df.sort_values(by=col_time)
    usar_tempo_real = True
else:
    df = df.sort_index()
    usar_tempo_real = False

st.sidebar.markdown("---")
pagina = st.sidebar.radio("Menu de Visualização:", ["Gráfico 2D (Por Barra)", "Gráfico 3D (Geral)"])
st.markdown("---")

# =======================================================
# VISUALIZAÇÃO 2D
# =======================================================
if pagina == "Gráfico 2D (Por Barra)":
    
    # --- CONTROLES (TOPO) ---
    with st.container():
        st.subheader("Configurações de Visualização")
        c1, c2, c3 = st.columns([2, 1, 1])
        
        with c1:
            barra_selecionada = st.selectbox("Selecione a Barra:", options=sorted(mapa_barras.keys()))
        
        with c2:
            st.write("") 
            st.write("")
            mostrar_limites = st.checkbox("Linhas PRODIST", value=True)
            
        with c3:
            st.write("")
            st.write("")
            travar_zoom = st.checkbox("Travar Eixo Y (0.85 - 1.15)", value=True)

    st.markdown("---")

    # --- GRÁFICO (FULL WIDTH) ---
    fig = go.Figure()
    colunas = mapa_barras[barra_selecionada]
    cores = {'V1': '#FF4B4B', 'V2': '#1C83E1', 'V3': '#00CC96'}
    
    if usar_tempo_real:
        x_data = df[col_time]
        x_title = "Horário"
    else:
        x_data = df.index
        x_title = "Passo de Simulação"

    for fase in ['V1', 'V2', 'V3']:
        if fase in colunas:
            fig.add_trace(go.Scatter(
                x=x_data,
                y=df[colunas[fase]],
                mode='lines',
                name=f"Fase {fase[-1]}",
                line=dict(color=cores[fase], width=2)
            ))

    if mostrar_limites:
        fig.add_hline(y=1.0, line_width=1, line_color="gray", opacity=0.3)
        fig.add_hline(y=1.05, line_dash="dash", line_color="#FFA500", annotation_text="Adequado (1.05)", annotation_position="top right")
        fig.add_hline(y=0.92, line_dash="dash", line_color="#FFA500", annotation_text="Adequado (0.92)", annotation_position="bottom right")
        fig.add_hline(y=0.87, line_dash="dot", line_color="red", annotation_text="CRÍTICO (0.87)", annotation_position="bottom right")

    fig.update_layout(
        title=f"Perfil de Tensão - Barra {barra_selecionada}",
        xaxis_title=x_title,
        yaxis_title="Tensão (pu)",
        template="plotly_white",
        height=600,
        hovermode="x unified",
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    if travar_zoom:
        fig.update_yaxes(range=[0.85, 1.15])

    st.plotly_chart(fig, use_container_width=True)

    # --- TABELA DE CONFERÊNCIA (ATUALIZADA 6 CASAS) ---
    st.markdown("---")
    with st.expander("📊 Tabela de Conferência (Estatísticas e Dados Brutos)", expanded=False):
        
        tab1, tab2 = st.tabs(["Resumo (Máx/Mín)", "Dados Completos (Excel)"])
        
        with tab1:
            st.markdown("Resumo estatístico de todas as barras.")
            
            dados_resumo = []
            for b in sorted(mapa_barras.keys()):
                for f, col in mapa_barras[b].items():
                    val_min = df[col].min()
                    val_max = df[col].max()
                    val_mean = df[col].mean()
                    
                    dados_resumo.append({
                        "Barra": b,
                        "Fase": f,
                        "Mínimo (pu)": val_min,
                        "Máximo (pu)": val_max,
                        "Média (pu)": val_mean
                    })
            
            df_stats = pd.DataFrame(dados_resumo)
            
            # FORMATADO PARA 6 CASAS DECIMAIS
            st.dataframe(
                df_stats.style.map(colorir_tabela, subset=["Mínimo (pu)", "Máximo (pu)", "Média (pu)"])
                .format("{:.6f}", subset=["Mínimo (pu)", "Máximo (pu)", "Média (pu)"]),
                use_container_width=True,
                height=400
            )

        with tab2:
            st.markdown("Tabela completa com todos os passos de tempo.")
            cols_tensao = []
            for b in sorted(mapa_barras.keys()):
                for f in mapa_barras[b].values():
                    cols_tensao.append(f)
            
            df_raw = df[[col_time] + cols_tensao]
            
            # FORMATADO PARA 6 CASAS DECIMAIS TAMBÉM NA TABELA GERAL
            st.dataframe(
                df_raw.style.format("{:.7f}", subset=cols_tensao),
                use_container_width=True
            )

# =======================================================
# VISUALIZAÇÃO 3D
# =======================================================
elif pagina == "Gráfico 3D (Geral)":
    render_grafico_3d(df, mapa_barras, usar_tempo_real, col_time)