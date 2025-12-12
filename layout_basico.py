# ============================================================================
# 1. IMPORTAÇÕES
# ============================================================================
import streamlit as st
import pandas as pd
import plotly.express as px
import glob
import re
import plotly.graph_objects as go
import numpy as np

# ============================================================================
# 2. CONFIGURAÇÃO DA PÁGINA
# ============================================================================
st.set_page_config(page_title="Simulação Daily.dss", layout="wide")

# ============================================================================
# 3. CABEÇALHO E ELEMENTOS VISUAIS
# ============================================================================
def render_cabecalho():
    """Renderiza logo, título e badges"""
    # Logo e título
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
    
    st.markdown(
        """
        <h1 style="text-align: center;">
            OpenTES - TSDQ
        </h1>
        """,
        unsafe_allow_html=True
    )
    
    # Badges
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
    
    # Descrição
    st.markdown("""
    Painel interativo para visualização dos resultados obtidos a partir dos monitores do arquivo `Daily.dss`.
    """)

# ============================================================================
# 4. MAPEAMENTO DE ARQUIVOS E CONFIGURAÇÕES
# ============================================================================
MAPA_ARQUIVOS = {
    "Tensão Subestação": {
        "path": "Exemplos/Daily/Equivalente_Mon_tensaosub_1*.csv",
    },
    "Tensão Carga D": {
        "path": "Exemplos/Daily/Equivalente_Mon_tensaocargad_1*.csv",
    },
    "Potência Subestação": {
        "path": "Exemplos/Daily/Equivalente_Mon_potenciasub_1*.csv",
    },
    "Potência Carga D": {
        "path": "Exemplos/Daily/Equivalente_Mon_potenciacargad_1*.csv",
    },
}

# ============================================================================
# 5. FUNÇÕES AUXILIARES
# ============================================================================
def sanitize_columns(cols):
    """Remove espaços e caracteres especiais dos nomes das colunas"""
    return [c.strip().replace(" ", "_").replace("(", "").replace(")", "") for c in cols]

@st.cache_data
def carregar_dados(padrao_arquivo):
    """Carrega dados de um arquivo CSV"""
    arquivos = glob.glob(padrao_arquivo)
    if not arquivos:
        return None
    
    df = pd.read_csv(arquivos[0])
    df.columns = sanitize_columns(df.columns)
    
    return df

def detectar_grupo(df, canal):
    """Identifica grupo de variáveis relacionadas baseado no canal selecionado"""
    if canal.startswith(("V", "v")):
        grupo = [c for c in df.columns if re.match(r"V\d", c)]
        titulo = "Tensões [V]"
    elif canal.startswith(("I", "i")):
        grupo = [c for c in df.columns if re.match(r"I\d", c)]
        titulo = "Correntes [A]"
    elif canal.startswith(("P", "p")):
        grupo = [c for c in df.columns if c.startswith("P")]
        titulo = "Potências Ativas [W]"
    elif canal.startswith(("Q", "q")):
        grupo = [c for c in df.columns if c.startswith("Q")]
        titulo = "Potências Reativas [VAR]"
    else:
        grupo = []
        titulo = ""
    
    return grupo, titulo

# ============================================================================
# 6. FUNÇÃO PRINCIPAL DE PLOTAGEM
# ============================================================================
def carregar_e_plotar(nome_monitor, monitor_info, monitor_key):
    """Carrega dados e cria visualizações para um monitor específico"""
    # Carregar dados
    df = carregar_dados(monitor_info["path"])
    if df is None:
        st.error(f"Nenhum arquivo encontrado para {nome_monitor}.")
        return None, None, None, None
    
    # Identificar colunas
    eixo_x = next((c for c in df.columns if c.lower() in ["hour", "time"]), df.columns[0])
    colunas_y = [c for c in df.columns if c != eixo_x]
    
    # Interface de seleção
    st.subheader(f"{nome_monitor} (valores reais)")
    
    canal = st.selectbox(
        f"Selecione o canal para {nome_monitor}:",
        colunas_y,
        key=f"single_{nome_monitor}_{monitor_key}"
    )
    
    grupo, titulo = detectar_grupo(df, canal)
    
    # Layout de colunas para os gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico individual
        yaxis_label = canal
        if canal.startswith(('V', 'v')):
            yaxis_label = f"{canal} [V]"
        elif canal.startswith(('I', 'i')):
            yaxis_label = f"{canal} [A]"
        elif canal.startswith(('P', 'p')):
            yaxis_label = f"{canal} [W]"
        elif canal.startswith(('Q', 'q')):
            yaxis_label = f"{canal} [VAR]"
        
        fig = px.line(df, x=eixo_x, y=canal, title=f"{nome_monitor} - {canal}", markers=True)
        fig.update_layout(xaxis_title="Hora", yaxis_title=yaxis_label, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Gráfico de grupo (se aplicável)
        if grupo:
            fig2 = px.line(df, x=eixo_x, y=grupo, title=f"{nome_monitor} - {titulo}", markers=True)
            fig2.update_layout(xaxis_title="Hora", yaxis_title=titulo, template="plotly_white")
            
            # Símbolos diferentes para cada linha
            symbols = ["circle", "square", "diamond", "cross", "x", "triangle-up", "triangle-down"]
            for i, col in enumerate(grupo):
                fig2.update_traces(selector=dict(name=col), marker_symbol=symbols[i % len(symbols)])
            
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Tipo de variável não identificado para exibição em grupo.")
    
    # Tabela de dados expandível
    with st.expander("Ver tabela de dados"):
        st.dataframe(df)
    
    return df, eixo_x, canal, grupo

# ============================================================================
# 7. FUNÇÃO DE VISUALIZAÇÃO 3D (VERSÃO CORRIGIDA)
# ============================================================================
def render_visualizacao_3d(df_sub, eixo_x_sub, grupo_sub, df_carga, eixo_x_carga, grupo_carga):
    """Versão melhorada com contêiner expansível para gráfico 3D"""
    st.divider()
    st.subheader("Visualização 3D (valores reais)")
    
    # Verificar quais dados estão disponíveis
    opcoes_3d = []
    if df_sub is not None and grupo_sub:
        opcoes_3d.append("Subestação")
    if df_carga is not None and grupo_carga:
        opcoes_3d.append("Carga D")
    
    if not opcoes_3d:
        st.info("Nenhum dado disponível para visualização 3D ou grupo de variáveis não identificado.")
        return
    
    # Seleção do conjunto de dados
    selecao_3d = st.selectbox("Selecione o conjunto de dados para visualização 3D:", opcoes_3d)
    
    # Definir dados baseado na seleção
    if selecao_3d == "Subestação" and df_sub is not None and grupo_sub:
        df = df_sub
        eixo_x = eixo_x_sub
        grupo = grupo_sub
        titulo_base = "Subestação"
    elif selecao_3d == "Carga D" and df_carga is not None and grupo_carga:
        df = df_carga
        eixo_x = eixo_x_carga
        grupo = grupo_carga
        titulo_base = "Carga D"
    else:
        st.warning("Grupo de variáveis não disponível para visualização 3D.")
        return
    
    # Container expansível para controles
    with st.expander(" Configurações do Gráfico 3D", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            altura = st.slider("Altura do gráfico", 600, 1200, 800, 50)
        with col2:
            proporcao = st.selectbox("Proporção padrão", 
                                    ["Automática", "1:1:1", "2:1:1", "1:2:1", "1:1:2"])
        with col3:
            rotacao_inicial = st.selectbox("Rotação inicial",
                                          ["Padrão", "Vista Superior", "Vista Lateral", "Vista Isométrica"])
    
    # Criar gráfico 3D
    with st.container():
        # Usar CSS para criar um contêiner maior
        st.markdown(
            """
            <style>
            .big-plot-container {
                border: 1px solid #ddd;
                border-radius: 10px;
                padding: 10px;
                background-color: #f9f9f9;
                margin-bottom: 20px;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown('<div class="big-plot-container">', unsafe_allow_html=True)
        
        # Preparar dados para o gráfico 3D
        x_vals = df[eixo_x].values
        
        # IMPORTANTE: Usar os nomes reais das variáveis, não números
        y_vals = grupo  # Lista com os nomes das variáveis (ex: ['I1', 'I2', 'I3', 'I4'])
        y_indices = np.arange(len(grupo))  # Índices numéricos para o meshgrid
        
        # Criar meshgrid
        X, Y_indices = np.meshgrid(x_vals, y_indices)
        Z = df[grupo].values.T  # Transpor para ter dimensões (variáveis, tempo)
        
        # Definir label do eixo Z baseado no tipo de variável
        if grupo[0].startswith('V'):
            z_label = "Tensão [V]"
            titulo_tipo = "Tensões"
            colorscale = 'Viridis'
        elif grupo[0].startswith('I'):
            z_label = "Corrente [A]"
            titulo_tipo = "Correntes"
            colorscale = 'Plasma'
        elif grupo[0].startswith('P'):
            z_label = "Potência Ativa [W]"
            titulo_tipo = "Potências Ativas"
            colorscale = 'RdYlBu'
        elif grupo[0].startswith('Q'):
            z_label = "Potência Reativa [VAR]"
            titulo_tipo = "Potências Reativas"
            colorscale = 'RdBu'
        else:
            z_label = "Magnitude"
            titulo_tipo = "Variáveis"
            colorscale = 'Viridis'
        
        # Configurar câmera baseado na seleção
        if rotacao_inicial == "Vista Superior":
            camera = dict(eye=dict(x=0, y=0, z=2.5))
        elif rotacao_inicial == "Vista Lateral":
            camera = dict(eye=dict(x=2.5, y=0, z=0))
        elif rotacao_inicial == "Vista Isométrica":
            camera = dict(eye=dict(x=1.5, y=1.5, z=1.5))
        else:  # Padrão
            camera = dict(eye=dict(x=1.8, y=1.8, z=1.2))
        
        # Configurar proporções
        if proporcao == "1:1:1":
            aspect = dict(x=1, y=1, z=1)
        elif proporcao == "2:1:1":
            aspect = dict(x=2, y=1, z=1)
        elif proporcao == "1:2:1":
            aspect = dict(x=1, y=2, z=1)
        elif proporcao == "1:1:2":
            aspect = dict(x=1, y=1, z=2)
        else:
            # Automática: baseada nos dados
            x_range = x_vals.max() - x_vals.min()
            y_range = len(grupo)
            z_range = Z.max() - Z.min()
            max_range = max(x_range, y_range, z_range)
            aspect = dict(
                x=x_range/max_range if max_range > 0 else 1,
                y=y_range/max_range if max_range > 0 else 1,
                z=z_range/max_range if max_range > 0 else 1
            )
        
        # Criar o gráfico de superfície
        fig3d = go.Figure(data=[go.Surface(
            x=X,  # Eixo X: tempo
            y=Y_indices,  # Eixo Y: índices numéricos das variáveis
            z=Z,  # Eixo Z: valores das variáveis
            colorscale=colorscale,
            showscale=True,
            colorbar=dict(
                title=z_label,
                title_side='right'
            ),
            contours={
                "z": {"show": True, "usecolormap": True, "highlightcolor": "limegreen", "project": {"z": True}}
            },
            hovertemplate=(
                "Hora: %{x:.2f}<br>" +
                "Variável: %{text}<br>" +
                f"{z_label}: %{{z:.4f}}<br>" +
                "<extra></extra>"
            ),
            text=[[y_vals[int(y)] for _ in range(len(x_vals))] for y in range(len(y_vals))]
        )])
        
        # Configurar layout
        fig3d.update_layout(
            title=f"Visualização 3D - {titulo_base} - {titulo_tipo}",
            scene=dict(
                xaxis=dict(
                    title="Hora",
                    gridcolor="lightgray",
                    showbackground=True,
                    backgroundcolor="rgba(240, 240, 240, 0.1)"
                ),
                yaxis=dict(
                    title="Variáveis",
                    tickvals=y_indices,  # Posições dos ticks
                    ticktext=y_vals,     # Labels dos ticks (nomes das variáveis)
                    gridcolor="lightgray",
                    showbackground=True,
                    backgroundcolor="rgba(240, 240, 240, 0.1)"
                ),
                zaxis=dict(
                    title=z_label,
                    gridcolor="lightgray",
                    showbackground=True,
                    backgroundcolor="rgba(240, 240, 240, 0.1)"
                ),
                aspectmode="manual",
                aspectratio=aspect,
                camera=camera
            ),
            template="plotly_white",
            height=altura,
            margin=dict(l=10, r=10, t=50, b=10)
        )
        
        # Adicionar botão de reset da câmera
        fig3d.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    showactive=False,
                    buttons=[
                        dict(
                            label="Reset View",
                            method="relayout",
                            args=["scene.camera", camera]
                        )
                    ],
                    x=0.05,
                    y=0.98,
                    xanchor="left",
                    yanchor="top"
                )
            ]
        )
        
        st.plotly_chart(fig3d, use_container_width=True, config={
            'displayModeBar': True,
            'scrollZoom': True,
            'modeBarButtonsToAdd': ['resetCameraDefault3d'],
            'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
            'displaylogo': False
        })
        
        # Legenda das variáveis
        st.markdown("**Legenda das variáveis no eixo Y:**")
        
        # Criar uma tabela com as variáveis e seus índices
        legend_data = []
        for i, var in enumerate(grupo):
            # Determinar tipo de variável
            if var.startswith('V'):
                tipo = "Tensão"
                unidade = "V"
            elif var.startswith('I'):
                tipo = "Corrente"
                unidade = "A"
            elif var.startswith('P'):
                tipo = "Potência Ativa"
                unidade = "W"
            elif var.startswith('Q'):
                tipo = "Potência Reativa"
                unidade = "VAR"
            else:
                tipo = "Desconhecido"
                unidade = ""
            
            legend_data.append({
                "Índice": i,
                "Variável": var,
                "Tipo": tipo,
                "Unidade": unidade
            })
        
        # Mostrar legenda em formato de tabela
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Correspondência no gráfico 3D:**")
            for item in legend_data:
                st.markdown(f"**{item['Índice']}** = {item['Variável']}")
        
        with col2:
            st.markdown("**Estatísticas das variáveis:**")
            # Calcular estatísticas básicas
            stats_df = pd.DataFrame({
                "Variável": grupo,
                "Mínimo": [df[var].min() for var in grupo],
                "Máximo": [df[var].max() for var in grupo],
                "Média": [df[var].mean() for var in grupo],
                "Desvio Padrão": [df[var].std() for var in grupo]
            })
            
            # Formatar números
            styled_stats = stats_df.style.format({
                'Mínimo': '{:.4f}',
                'Máximo': '{:.4f}',
                'Média': '{:.4f}',
                'Desvio Padrão': '{:.4f}'
            })
            
            st.dataframe(styled_stats, use_container_width=True, height=200)
        
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# 8. FUNÇÃO PARA CÁLCULO DE DESEQUILÍBRIO DE TENSÃO (PRODIST MÓDULO 8)
# ============================================================================
def calcular_componentes_simetricas(Va_mag, Va_ang, Vb_mag, Vb_ang, Vc_mag, Vc_ang):
    """
    Calcula componentes simétricas (positiva, negativa, zero)
    a partir de tensões de fase.
    
    Parâmetros:
        Va_mag, Vb_mag, Vc_mag: Magnitudes das tensões (V)
        Va_ang, Vb_ang, Vc_ang: Ângulos das tensões (graus)
    
    Retorna:
        V_pos: Tensão de sequência positiva (módulo e ângulo)
        V_neg: Tensão de sequência negativa (módulo e ângulo)
        V_zero: Tensão de sequência zero (módulo e ângulo)
    """
    # Converter para radianos e forma complexa
    Va = Va_mag * np.exp(1j * np.radians(Va_ang))
    Vb = Vb_mag * np.exp(1j * np.radians(Vb_ang))
    Vc = Vc_mag * np.exp(1j * np.radians(Vc_ang))
    
    # Operador 'a' (rotação de 120°)
    a = np.exp(1j * np.radians(120))
    a2 = np.exp(1j * np.radians(240))
    
    # Matriz de transformação de componentes simétricas
    # [V0] = 1/3 * [1   1   1] [Va]
    # [V1] = 1/3 * [1   a  a2] [Vb]
    # [V2] = 1/3 * [1  a2   a] [Vc]
    
    V_zero = (Va + Vb + Vc) / 3
    V_pos = (Va + a * Vb + a2 * Vc) / 3
    V_neg = (Va + a2 * Vb + a * Vc) / 3
    
    # Converter de volta para módulo e ângulo
    def polar(complex_num):
        magnitude = np.abs(complex_num)
        angle = np.degrees(np.angle(complex_num))
        return magnitude, angle
    
    V_pos_mag, V_pos_ang = polar(V_pos)
    V_neg_mag, V_neg_ang = polar(V_neg)
    V_zero_mag, V_zero_ang = polar(V_zero)
    
    return {
        'positiva': (V_pos_mag, V_pos_ang),
        'negativa': (V_neg_mag, V_neg_ang),
        'zero': (V_zero_mag, V_zero_ang)
    }

def calcular_fator_desequilibrio(df):
    """
    Calcula o fator de desequilíbrio de tensão para cada ponto no tempo.
    
    Fator de desequilíbrio = (V_negativa / V_positiva) × 100%
    """
    resultados = []
    
    for idx, row in df.iterrows():
        # Obter magnitudes e ângulos (ajustar nomes das colunas se necessário)
        Va_mag = row['V1'] if 'V1' in df.columns else row.get('V1mag', 0)
        Va_ang = row['VAngle1'] if 'VAngle1' in df.columns else row.get('V1ang', 0)
        
        Vb_mag = row['V2'] if 'V2' in df.columns else row.get('V2mag', 0)
        Vb_ang = row['VAngle2'] if 'VAngle2' in df.columns else row.get('V2ang', 0)
        
        Vc_mag = row['V3'] if 'V3' in df.columns else row.get('V3mag', 0)
        Vc_ang = row['VAngle3'] if 'VAngle3' in df.columns else row.get('V3ang', 0)
        
        # Calcular componentes simétricas
        componentes = calcular_componentes_simetricas(
            Va_mag, Va_ang, Vb_mag, Vb_ang, Vc_mag, Vc_ang
        )
        
        V_pos_mag, _ = componentes['positiva']
        V_neg_mag, _ = componentes['negativa']
        V_zero_mag, _ = componentes['zero']
        
        # Calcular fator de desequilíbrio
        if V_pos_mag > 0:
            fator_desequilibrio = (V_neg_mag / V_pos_mag) * 100
        else:
            fator_desequilibrio = 0
        
        resultados.append({
            'hora': row['hour'] if 'hour' in df.columns else idx,
            'V_positiva': V_pos_mag,
            'V_negativa': V_neg_mag,
            'V_zero': V_zero_mag,
            'FD (%)': fator_desequilibrio,
            'FD_limite': 3.0  # Limite PRODIST (ajustável)
        })
    
    return pd.DataFrame(resultados)

def render_analise_desequilibrio(df_sub, df_carga):
    """Renderiza análise de desequilíbrio de tensão conforme PRODIST"""
    st.divider()
    st.subheader(" Análise de Desequilíbrio de Tensão (PRODIST Módulo 8)")
    
    st.markdown("""
    **Cálculo conforme PRODIST Módulo 8 - Item 5:**
    - Fator de Desequilíbrio = (Componente Negativa / Componente Positiva) × 100%
    - Limite máximo permitido: **3.0%** (para sistemas de distribuição)
    """)
    
    # Verificar quais dados estão disponíveis
    dados_disponiveis = []
    if df_sub is not None:
        dados_disponiveis.append(("Subestação", df_sub))
    if df_carga is not None:
        dados_disponiveis.append(("Carga D", df_carga))
    
    if not dados_disponiveis:
        st.warning("Nenhum dado disponível para análise de desequilíbrio.")
        return
    
    # Criar abas para cada conjunto de dados
    tabs = st.tabs([nome for nome, _ in dados_disponiveis])
    
    for idx, (tab, (nome, df)) in enumerate(zip(tabs, dados_disponiveis)):
        with tab:
            # Calcular fator de desequilíbrio
            df_fd = calcular_fator_desequilibrio(df)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Gráfico do fator de desequilíbrio
                fig = go.Figure()
                
                # Linha do fator de desequilíbrio
                fig.add_trace(go.Scatter(
                    x=df_fd['hora'],
                    y=df_fd['FD (%)'],
                    mode='lines+markers',
                    name='Fator de Desequilíbrio',
                    line=dict(color='blue', width=2),
                    marker=dict(size=8)
                ))
                
                # Linha do limite PRODIST
                fig.add_trace(go.Scatter(
                    x=df_fd['hora'],
                    y=df_fd['FD_limite'],
                    mode='lines',
                    name='Limite PRODIST (3.0%)',
                    line=dict(color='red', width=2, dash='dash'),
                    fillcolor='rgba(255, 0, 0, 0.1)',
                    fill='tonexty'
                ))
                
                fig.update_layout(
                    title=f'Fator de Desequilíbrio - {nome}',
                    xaxis_title='Hora',
                    yaxis_title='Fator de Desequilíbrio (%)',
                    template='plotly_white',
                    height=400,
                    hovermode='x unified'
                )
                
                # Destacar pontos acima do limite
                acima_limite = df_fd[df_fd['FD (%)'] > 3.0]
                if not acima_limite.empty:
                    fig.add_trace(go.Scatter(
                        x=acima_limite['hora'],
                        y=acima_limite['FD (%)'],
                        mode='markers',
                        name='Acima do Limite',
                        marker=dict(color='red', size=10, symbol='x')
                    ))
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Gráfico das componentes simétricas
                fig2 = go.Figure()
                
                fig2.add_trace(go.Scatter(
                    x=df_fd['hora'],
                    y=df_fd['V_positiva'],
                    mode='lines+markers',
                    name='Sequência Positiva (V+)',
                    line=dict(color='green', width=2)
                ))
                
                fig2.add_trace(go.Scatter(
                    x=df_fd['hora'],
                    y=df_fd['V_negativa'],
                    mode='lines+markers',
                    name='Sequência Negativa (V-)',
                    line=dict(color='orange', width=2)
                ))
                
                fig2.add_trace(go.Scatter(
                    x=df_fd['hora'],
                    y=df_fd['V_zero'],
                    mode='lines+markers',
                    name='Sequência Zero (V0)',
                    line=dict(color='purple', width=2)
                ))
                
                fig2.update_layout(
                    title=f'Componentes Simétricas - {nome}',
                    xaxis_title='Hora',
                    yaxis_title='Tensão [V]',
                    template='plotly_white',
                    height=400
                )
                
                st.plotly_chart(fig2, use_container_width=True)
            
            # Estatísticas
            st.markdown("###  Estatísticas do Desequilíbrio")
            
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            
            with col_stat1:
                fd_max = df_fd['FD (%)'].max()
                cor = "🔴" if fd_max > 3.0 else "🟢"
                st.metric(
                    label=f"{cor} Máximo",
                    value=f"{fd_max:.2f}%",
                    delta="Acima do limite" if fd_max > 3.0 else "Dentro do limite"
                )
            
            with col_stat2:
                fd_medio = df_fd['FD (%)'].mean()
                st.metric(
                    label="Média",
                    value=f"{fd_medio:.2f}%"
                )
            
            with col_stat3:
                fd_min = df_fd['FD (%)'].min()
                st.metric(
                    label="Mínimo",
                    value=f"{fd_min:.2f}%"
                )
            
            with col_stat4:
                horas_acima = len(df_fd[df_fd['FD (%)'] > 3.0])
                total_horas = len(df_fd)
                percentual = (horas_acima / total_horas * 100) if total_horas > 0 else 0
                st.metric(
                    label="Horas > 3%",
                    value=f"{horas_acima}/{total_horas}",
                    delta=f"{percentual:.1f}%"
                )
            
            # Tabela com resultados detalhados
            with st.expander(" Ver Tabela de Resultados Detalhados"):
                st.dataframe(
                    df_fd.style.format({
                        'V_positiva': '{:.2f}',
                        'V_negativa': '{:.2f}',
                        'V_zero': '{:.2f}',
                        'FD (%)': '{:.4f}%'
                    }).apply(
                        lambda x: ['background-color: #ffcccc' if v > 3.0 and k == 'FD (%)' 
                                 else '' for k, v in x.items()],
                        axis=1
                    ),
                    use_container_width=True
                )
            
            # Recomendações baseadas nos resultados
            st.markdown("###  Recomendações Técnicas")
            
            if fd_max > 3.0:
                st.warning("""
                ** ATENÇÃO: Desequilíbrio acima do limite permitido!**
                
                **Possíveis causas:**
                - Cargas monofásicas desbalanceadas
                - Falhas em equipamentos trifásicos
                - Desigualdade de impedâncias nas fases
                - Conexões inadequadas
                
                **Ações recomendadas:**
                1. Redistribuir cargas monofásicas entre as fases
                2. Verificar condições de conexões e contatos
                3. Investigar equipamentos com possíveis falhas
                4. Considerar uso de bancos de capacitores com controle de desequilíbrio
                """)
            else:
                st.success("""
                 Sistema dentro dos limites de desequilíbrio!
                
                O fator de desequilíbrio está abaixo de 3.0% em todos os pontos,
                atendendo aos requisitos do PRODIST Módulo 8.
                """)
    
    # Análise comparativa se tiver ambos os conjuntos
    if len(dados_disponiveis) == 2:
        st.divider()
        st.subheader(" Análise Comparativa")
        
        # Calcular para ambos
        df_fd_sub = calcular_fator_desequilibrio(df_sub)
        df_fd_carga = calcular_fator_desequilibrio(df_carga)
        
        fig_comp = go.Figure()
        
        fig_comp.add_trace(go.Scatter(
            x=df_fd_sub['hora'],
            y=df_fd_sub['FD (%)'],
            mode='lines+markers',
            name='Subestação',
            line=dict(color='blue', width=2)
        ))
        
        fig_comp.add_trace(go.Scatter(
            x=df_fd_carga['hora'],
            y=df_fd_carga['FD (%)'],
            mode='lines+markers',
            name='Carga D',
            line=dict(color='green', width=2)
        ))
        
        # Linha do limite
        fig_comp.add_trace(go.Scatter(
            x=df_fd_sub['hora'],
            y=[3.0] * len(df_fd_sub),
            mode='lines',
            name='Limite 3.0%',
            line=dict(color='red', width=2, dash='dash')
        ))
        
        fig_comp.update_layout(
            title='Comparação do Fator de Desequilíbrio',
            xaxis_title='Hora',
            yaxis_title='Fator de Desequilíbrio (%)',
            template='plotly_white',
            height=500
        )
        
        st.plotly_chart(fig_comp, use_container_width=True)
        
        # Insights
        st.markdown("#### Análise Comparativa")
        
        dif_max = abs(df_fd_sub['FD (%)'].max() - df_fd_carga['FD (%)'].max())
        dif_media = abs(df_fd_sub['FD (%)'].mean() - df_fd_carga['FD (%)'].mean())
        
        if dif_max > 1.0:
            st.info(f"""
            **Variação significativa detectada:**
            - Diferença máxima: {dif_max:.2f}%
            - Diferença média: {dif_media:.2f}%
            
            Isso indica que o desequilíbrio aumenta ao longo da rede,
            sugerindo possíveis problemas na distribuição ou nas cargas.
            """)

# ============================================================================
# 9. FUNÇÃO PRINCIPAL DO APLICATIVO
# ============================================================================
def main():
    """Função principal que orquestra todo o aplicativo"""
    # Renderizar cabeçalho
    render_cabecalho()
    
    # Seleção do tipo de variável
    st.subheader("Seleção de tipo de variável")
    tipo_variavel = st.radio(
        "Escolha o tipo de variável:",
        ["Tensão, corrente e ângulo", "Potência ativa e reativa"],
        horizontal=True
    )
    
    st.divider()
    
    # Variáveis para armazenar dados
    df_sub = None
    df_carga = None
    eixo_x_sub = None
    eixo_x_carga = None
    grupo_sub = None
    grupo_carga = None
    
    # Layout principal com abas
    with st.container():
        if tipo_variavel == "Tensão, corrente e ângulo":
            tab1, tab2 = st.tabs(["Tensão Subestação", "Tensão Carga D"])
            
            with tab1:
                df_sub, eixo_x_sub, _, grupo_sub = carregar_e_plotar(
                    "Tensão Subestação", 
                    MAPA_ARQUIVOS["Tensão Subestação"], 
                    "sub"
                )
            
            with tab2:
                df_carga, eixo_x_carga, _, grupo_carga = carregar_e_plotar(
                    "Tensão Carga D", 
                    MAPA_ARQUIVOS["Tensão Carga D"], 
                    "carga"
                )
        
        elif tipo_variavel == "Potência ativa e reativa":
            tab1, tab2 = st.tabs(["Potência Subestação", "Potência Carga D"])
            
            with tab1:
                df_sub, eixo_x_sub, _, grupo_sub = carregar_e_plotar(
                    "Potência Subestação", 
                    MAPA_ARQUIVOS["Potência Subestação"], 
                    "sub"
                )
            
            with tab2:
                df_carga, eixo_x_carga, _, grupo_carga = carregar_e_plotar(
                    "Potência Carga D", 
                    MAPA_ARQUIVOS["Potência Carga D"], 
                    "carga"
                )
    
    # Renderizar visualização 3D
    render_visualizacao_3d(df_sub, eixo_x_sub, grupo_sub, df_carga, eixo_x_carga, grupo_carga)
    
    # Renderizar análise de desequilíbrio de tensão
    render_analise_desequilibrio(df_sub, df_carga)

# ============================================================================
# 10. EXECUÇÃO DO APLICATIVO
# ============================================================================
if __name__ == "__main__":
    main()