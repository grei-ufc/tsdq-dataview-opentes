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
    Este aplicativo realiza a visualização e análise de dados elétricos provenientes da simulação `Daily.dss`, com foco em qualidade da energia elétrica, conforme diretrizes do PRODIST – Módulo 8.
    O sistema foi desenvolvido para apoiar estudos em redes de distribuição, permitindo avaliar o comportamento das tensões ao longo do tempo e entre diferentes barras.
    """)

    st.markdown("---") # Uma linha divisória
    st.markdown("### Topologia do Sistema Analisado")
    st.image(
        "https://raw.githubusercontent.com/grei-ufc/tsdq-dataview-opentes/main/imagens/Diagrama%20SEP%20cargac.jpg", 
        caption="Diagrama Unifilar Simplificado",
        use_container_width=True
    )
    st.markdown("---")

# ============================================================================
# 4. MAPEAMENTO DE ARQUIVOS E CONFIGURAÇÕES
# ============================================================================
MAPA_ARQUIVOS = {
    "Tensão e Corrente Subestação": {
        "path": "Exemplos/Daily/Equivalente_Mon_tensaosub_1*.csv",
    },
    "Tensão e Corrente Carga D": {
        "path": "Exemplos/Daily/Equivalente_Mon_tensaocargad_1*.csv",
    },
    "Potências Subestação": {
        "path": "Exemplos/Daily/Equivalente_Mon_potenciasub_1*.csv",
    },
    "Potências Carga D": {
        "path": "Exemplos/Daily/Equivalente_Mon_potenciacargad_1*.csv",
    },
    "Tensão e Corrente Carga C": {
        "path": "Exemplos/Daily/Equivalente_Mon_tensaocargac_1*.csv",
    },
    "Potências Carga C": {
        "path": "Exemplos/Daily/Equivalente_Mon_potenciacargac_1*.csv"
    }
}

# ============================================================================
# MAPA DE LEGENDAS (Tradução de V1 -> Fase A)
# ============================================================================
MAPA_LEGENDAS = {
    # Tensões
    "V1": "Fase A (kV)",
    "V2": "Fase B (kV)",
    "V3": "Fase C (kV)",
    "Angle1": "Ângulo A (°)",
    "Angle2": "Ângulo B (°)",
    "Angle3": "Ângulo C (°)",
    
    # Correntes
    "I1": "Corrente A (A)",
    "I2": "Corrente B (A)",
    "I3": "Corrente C (A)",
    
    # Potências (Depende do mode=1 ppolar=no do DSS)
    "P1": "Pot. Ativa A (kW)",
    "P2": "Pot. Ativa B (kW)",
    "P3": "Pot. Ativa C (kW)",
    "Q1": "Pot. Reativa A (kvar)",
    "Q2": "Pot. Reativa B (kvar)",
    "Q3": "Pot. Reativa C (kvar)"
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

def listar_grupos_para_3d(df):
    """Varre o dataframe e encontra grupos (V, I, P, Q) para o 3D"""
    grupos = {}
    
    # Procura colunas de Tensão (V1, V2...)
    v_cols = [c for c in df.columns if re.match(r"V\d", c, re.IGNORECASE)]
    if v_cols: grupos["Tensões"] = v_cols
        
    # Procura colunas de Corrente (I1, I2...)
    i_cols = [c for c in df.columns if re.match(r"I\d", c, re.IGNORECASE)]
    if i_cols: grupos["Correntes"] = i_cols
        
    # Procura Potências (P...)
    p_cols = [c for c in df.columns if c.lower().startswith("p")]
    if p_cols: grupos["Potência Ativa"] = p_cols
        
    # Procura Reativos (Q...)
    q_cols = [c for c in df.columns if c.lower().startswith("q")]
    if q_cols: grupos["Potência Reativa"] = q_cols
        
    return grupos

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
    
    # Filtro de colunas zeradas
    colunas_com_dados = [
        c for c in df.columns 
        if not (df[c] == 0).all() or c.lower() in ["hour", "time", "step"]
    ]
    df = df[colunas_com_dados]

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
    
    col1, col2 = st.columns(2)
    
    with col1:
        # --- GRÁFICO INDIVIDUAL ---
        # Define o título do eixo Y
        yaxis_label = canal
        if canal.startswith(('V', 'v')): yaxis_label = "Tensão [V]"
        elif canal.startswith(('I', 'i')): yaxis_label = "Corrente [A]"
        elif canal.startswith(('P', 'p')): yaxis_label = "Potência [kW]"
        
        # Cria o gráfico usando o nome original (V1)
        fig = px.line(df, x=eixo_x, y=canal, title=f"{nome_monitor} - Detalhe", markers=True)
        
        # AQUI ACONTECE A MÁGICA: Renomeia a legenda visualmente
        novo_nome = MAPA_LEGENDAS.get(canal, canal)
        fig.for_each_trace(lambda t: t.update(name=novo_nome, legendgroup=novo_nome, hovertemplate=t.hovertemplate.replace(t.name, novo_nome)))
        
        fig.update_layout(xaxis_title="Hora", yaxis_title=yaxis_label, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # --- GRÁFICO DE GRUPO (Todas as fases) ---
        if grupo:
            fig2 = px.line(df, x=eixo_x, y=grupo, title=f"{nome_monitor} - Trifásico", markers=True)
            
            # Renomeia todas as linhas do grupo (V1->Fase A, V2->Fase B...)
            fig2.for_each_trace(lambda t: t.update(name=MAPA_LEGENDAS.get(t.name, t.name)))
            
            fig2.update_layout(xaxis_title="Hora", yaxis_title=titulo, template="plotly_white")
            
            # Símbolos diferentes
            symbols = ["circle", "square", "diamond", "cross", "x", "triangle-up"]
            for i, col in enumerate(grupo):
                # Precisamos usar o nome original 'col' para selecionar, depois atualizar
                nome_legenda = MAPA_LEGENDAS.get(col, col)
                fig2.update_traces(selector=dict(name=nome_legenda), marker_symbol=symbols[i % len(symbols)])
            
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Visualização em grupo não disponível para esta variável.")
    
    with st.expander("Ver tabela de dados"):
        st.dataframe(df)
    
    return df, eixo_x, canal, grupo

# ============================================================================
# 7. FUNÇÃO DE VISUALIZAÇÃO 3D (VERSÃO CORRIGIDA)
# ============================================================================
# --- SUBSTITUA A FUNÇÃO render_visualizacao_3d POR ESTA ---
def render_visualizacao_3d_independente():
    st.markdown("## Visualização Espacial (3D)")

    # 1. SELEÇÃO DO ARQUIVO (Agora independente)
    monitor_selecionado = st.selectbox(
        "Selecione o Monitor/Arquivo:", 
        list(MAPA_ARQUIVOS.keys()),
        key="sel_3d_source"
    )

    # 2. CARREGAMENTO (Backend)
    caminho = MAPA_ARQUIVOS[monitor_selecionado]["path"]
    df = carregar_dados(caminho)
    
    if df is None:
        st.error("Dados não encontrados.")
        return

    # Filtro de colunas zeradas
    colunas_validas = [
        c for c in df.columns 
        if not (df[c] == 0).all() or c.lower() in ["hour", "time", "step"]
    ]
    df = df[colunas_validas]

    # Eixo X
    eixo_x = next((c for c in df.columns if c.lower() in ["hour", "time"]), df.columns[0])

    # 3. IDENTIFICAR GRUPOS
    grupos_disponiveis = listar_grupos_para_3d(df)
    
    if not grupos_disponiveis:
        st.warning("Nenhum grupo compatível (V, I, P, Q) encontrado para 3D.")
        return

    tipo_visualizacao = st.selectbox(
        "Selecione o Grupo de Variáveis:", 
        list(grupos_disponiveis.keys()),
        key="sel_3d_type"
    )
    
    grupo = grupos_disponiveis[tipo_visualizacao] # ex: ['V1', 'V2', 'V3']

    # 4. CONFIGURAÇÕES VISUAIS
    with st.expander("⚙️ Configurações do Gráfico", expanded=True):
        altura = st.slider("Altura do gráfico", 600, 1200, 800, 50)

    # 5. PLOTAGEM
    with st.container():
        # CSS para borda
        st.markdown('<div style="border:1px solid #ddd; padding:10px; border-radius:10px;">', unsafe_allow_html=True)
        
        x_vals = df[eixo_x].values
        y_vals_originais = grupo
        y_vals_legiveis = [MAPA_LEGENDAS.get(c, c) for c in grupo] # Transforma [V1, V2] em [Fase A, Fase B]
        y_indices = np.arange(len(y_vals_originais))
        
        # Meshgrid
        X, Y_indices = np.meshgrid(x_vals, y_indices)
        Z = df[grupo].values.T
        
        # Cor baseada no tipo
        colorscale = 'RdYlBu' if "Potência" in tipo_visualizacao else 'Viridis'
        
        # Câmera e Aspecto Fixos
        camera = dict(eye=dict(x=1.8, y=1.8, z=1.2))
        aspect = dict(x=1, y=1, z=1)

        fig3d = go.Figure(data=[go.Surface(
            x=X, y=Y_indices, z=Z,
            colorscale=colorscale,
            colorbar=dict(title=tipo_visualizacao)
        )])
        
        fig3d.update_layout(
        title=f"3D: {monitor_selecionado} - {tipo_visualizacao}",
        scene=dict(
            xaxis_title="Tempo",
            # AQUI: Usa os nomes legíveis no eixo Y
            yaxis=dict(title="Fases", tickvals=y_indices, ticktext=y_vals_legiveis),
            zaxis_title="Magnitude",
                aspectmode="manual",
                aspectratio=aspect,
                camera=camera
            ),
            height=altura,
            margin=dict(l=0, r=0, b=0, t=40)
        )
        
        st.plotly_chart(fig3d, use_container_width=True)
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
    """Função principal com navegação lateral"""
    
    # --- CSS PARA ESTREITAR A SIDEBAR ---
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] {
                min-width: 200px;
                max-width: 200px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Menu Lateral
    with st.sidebar:
        # DICA: Troque st.title por st.markdown ou st.header para reduzir margem vertical
        st.header("Navegação")
        pagina = st.radio(
            "Ir para:",
            ["Análise Linear (2D)", "Topologia (3D)"]
        )
        st.divider()

    render_cabecalho()

   # ROTA 1: ANÁLISE 2D
    if pagina == "Análise Linear (2D)":
        st.subheader("Análise Linear e Desequilíbrio", divider="green")
        
        tipo_variavel = st.radio(
            "Escolha o tipo de variável:",
            ["Tensão, corrente e ângulo", "Potência ativa e reativa"],
            horizontal=True
        )
        st.divider()

        # Inicializa variáveis para garantir que existam
        df_sub = None
        df_carga = None # Este representará a Carga D (Trifásica)
        
        # -----------------------------------------------------
        # CASO 1: TENSÃO, CORRENTE E ÂNGULO
        # -----------------------------------------------------
        if tipo_variavel == "Tensão, corrente e ângulo":
            # Agora são 3 abas
            tab1, tab2, tab3 = st.tabs([
                "Subestação (AT)", 
                "Carga D (Ind. Trifásica)", 
                "Carga C (Res. Monofásica)"
            ])
            
            with tab1:
                df_sub, _, _, _ = carregar_e_plotar(
                    "Tensão e Corrente Subestação", 
                    MAPA_ARQUIVOS["Tensão e Corrente Subestação"], 
                    "sub_tensao"
                )
            
            with tab2:
                # df_carga captura os dados da Carga D para o desequilíbrio
                df_carga, _, _, _ = carregar_e_plotar(
                    "Tensão e Corrente Carga D", 
                    MAPA_ARQUIVOS["Tensão e Corrente Carga D"], 
                    "carga_d_tensao"
                )
            
            with tab3:
                # Carga C (Apenas visualização, não salva em variável de análise global)
                # OBS: Mudei o id final para "carga_c_tensao" para não conflitar
                carregar_e_plotar(
                    "Tensão e Corrente Carga C", 
                    MAPA_ARQUIVOS["Tensão e Corrente Carga C"], 
                    "carga_c_tensao"
                )

        # -----------------------------------------------------
        # CASO 2: POTÊNCIA ATIVA E REATIVA
        # -----------------------------------------------------
        elif tipo_variavel == "Potência ativa e reativa":
            # Aqui também precisamos de 3 abas agora
            tab1, tab2, tab3 = st.tabs([
                "Subestação (AT)", 
                "Carga D (Ind. Trifásica)", 
                "Carga C (Res. Monofásica)"
            ])
            
            with tab1:
                # Note que aqui não salvamos em df_sub/df_carga pois não faremos analise de desequilibrio com potência
                carregar_e_plotar(
                    "Potências Subestação", 
                    MAPA_ARQUIVOS["Potências Subestação"], 
                    "sub_pot"
                )
            
            with tab2:
                carregar_e_plotar(
                    "Potências Carga D", 
                    MAPA_ARQUIVOS["Potências Carga D"], 
                    "carga_d_pot"
                )
                
            with tab3:
                carregar_e_plotar(
                    "Potências Carga C", 
                    MAPA_ARQUIVOS["Potências Carga C"], 
                    "carga_c_pot"
                )

        # -----------------------------------------------------
        # ANÁLISE DE DESEQUILÍBRIO
        # -----------------------------------------------------
        # Só executamos se estivermos no modo Tensão e se os dados foram carregados
        if tipo_variavel == "Tensão, corrente e ângulo":
            if df_sub is not None and df_carga is not None:
                render_analise_desequilibrio(df_sub, df_carga)
            else:
                st.warning("Aguardando carregamento dos dados para análise de desequilíbrio...")

    # ROTA 2: ANÁLISE 3D (Totalmente isolada)
    elif pagina == "Topologia (3D)":
        render_visualizacao_3d_independente()

# ============================================================================
# 10. EXECUÇÃO DO APLICATIVO
# ============================================================================
if __name__ == "__main__":
    main()