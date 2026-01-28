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
import json
import os

# --- ESTA TEM QUE SER A PRIMEIRA LINHA 'st.' DO CÓDIGO ---
st.set_page_config(
    page_title="Dashboard OpenDSS", 
    layout="wide", 
    initial_sidebar_state="expanded"
)
# ---------------------------------------------------------

# ============================================================================
# CONFIGURAÇÃO DA TOPOLOGIA (VIA ARQUIVO JSON)
# ============================================================================

# Função para carregar a configuração
def carregar_configuracao(caminho_json):
    try:
        with open(caminho_json, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        return dados
    except FileNotFoundError:
        st.error(f"O arquivo '{caminho_json}' não foi encontrado!")
        st.stop()
    except json.JSONDecodeError:
        st.error(f"Erro ao ler o JSON. Verifique se a formatação está correta.")
        st.stop()

# 1. Carrega o arquivo JSON
config = carregar_configuracao('config_circuito.json')

# 2. Monta a estrutura que o código usará
pasta_base = config.get("pasta_arquivos", "") # Pega o nome da pasta definido no JSON
TOPOLOGIA_SISTEMA = []

for item in config["elementos"]:
    # Monta o caminho base conforme está no JSON
    caminho_original = os.path.join(pasta_base, item["arquivo"])
    
    # --- LÓGICA INTELIGENTE DE DETECÇÃO DE ARQUIVOS ---
    # Seus arquivos são separados: "...tensao..." e "...potencia..."
    # O código abaixo tenta adivinhar o par correto automaticamente.
    caminho_vi = caminho_original
    caminho_pq = caminho_original
    
    # Se o JSON apontar para o arquivo de tensão, calculamos o nome do de potência
    if "tensao" in caminho_original.lower():
        caminho_pq = caminho_original.replace("tensao", "potencia")
        
    # Se o JSON apontar para o arquivo de potência, calculamos o nome do de tensão
    elif "potencia" in caminho_original.lower():
        caminho_vi = caminho_original.replace("potencia", "tensao")
    
    # Adiciona na lista com os caminhos corretos para cada grandeza
    TOPOLOGIA_SISTEMA.append({
        "nome": item["nome"],
        "arquivo": caminho_original,
        "kv_base": item["kv_base"],
        "tipo": item.get("tipo", "generico"),
        "arquivo_vi": caminho_vi, # Usa o arquivo de Tensão/Corrente
        "arquivo_pq": caminho_pq  # Usa o arquivo de Potência
    })
# Opcional: Mostrar na tela que carregou com sucesso
st.sidebar.success(f"Cenário carregado: {config['nome_cenario']}")



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
        "https://raw.githubusercontent.com/grei-ufc/tsdq-dataview-opentes/main/imagens/Diagrama%20SEP%20FINAL.jpg", 
        caption="Diagrama Unifilar Simplificado",
        use_container_width=True
    )
    st.markdown("---")

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
# 9. FUNÇÃO DE VISUALIZAÇÃO 3D INDEPENDENTE (COM GRÁFICO 3D RESTAURADO)
# ============================================================================
def render_visualizacao_3d_independente():
    st.markdown("## Visualização 3D Detalhada (Por Elemento)")

    # 1. SELEÇÃO DO ELEMENTO
    nomes_elementos = [item["nome"] for item in TOPOLOGIA_SISTEMA]
    escolha_elemento = st.selectbox("Selecione o Elemento (Barra/Trafo):", nomes_elementos)
    
    item_selecionado = next(item for item in TOPOLOGIA_SISTEMA if item["nome"] == escolha_elemento)

    # 2. SELEÇÃO DE VARIÁVEIS
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        tipo_variavel = st.selectbox(
            "Selecione a Variável:",
            [
                "Tensão (Magnitude)", "Tensão (Ângulo)", 
                "Corrente (Magnitude)", "Corrente (Ângulo)",
                "Potência Ativa (P)", "Potência Reativa (Q)"
            ]
        )
        
    with col2:
        # Checkbox para alternar entre 2D e 3D
        modo_visualizacao = st.radio("Modo de Visualização:", ["3D (Espacial)", "2D (Plano)"])

    with col3:
        fases = st.multiselect("Fases:", ["Fase A (1)", "Fase B (2)", "Fase C (3)"], default=["Fase A (1)", "Fase B (2)", "Fase C (3)"])

    # 3. CARREGAMENTO INTELIGENTE (Mantivemos a correção aqui)
    if "Potência" in tipo_variavel:
        caminho_arquivo = item_selecionado["arquivo_pq"]
    else:
        caminho_arquivo = item_selecionado["arquivo_vi"]

    df = carregar_dados(caminho_arquivo)

    if df is None:
        st.error(f"Não foi possível carregar o arquivo para {escolha_elemento}.")
        return

    # 4. PREPARAÇÃO DOS DADOS
    mapa_fases = {"Fase A (1)": "1", "Fase B (2)": "2", "Fase C (3)": "3"}
    # Mapeamento para posicionar as fases no eixo Y do gráfico 3D
    posicao_fases = {"Fase A (1)": 0, "Fase B (2)": 1, "Fase C (3)": 2}
    
    col_tempo = next((c for c in df.columns if c.lower() in ["hour", "time", "t(h)"]), df.columns[0])
    eixo_x = df[col_tempo]
    
    colunas_para_plotar = []

    for fase_selecionada in fases:
        num_fase = mapa_fases[fase_selecionada]
        
        # Regex para encontrar a coluna (Mesma lógica da resposta anterior)
        padrao = ""
        if "Tensão (Magnitude)" in tipo_variavel: padrao = f"V{num_fase}$| V{num_fase}$|V{num_fase}\\s"
        elif "Tensão (Ângulo)" in tipo_variavel: padrao = f"Ang.*{num_fase}"
        elif "Corrente (Magnitude)" in tipo_variavel: padrao = f"I{num_fase}$| I{num_fase}$|I{num_fase}\\s"
        elif "Corrente (Ângulo)" in tipo_variavel: padrao = f"Ang.*I{num_fase}|Ang.*{num_fase}"
        elif "Potência Ativa" in tipo_variavel: padrao = f"P{num_fase}| P{num_fase}"
        elif "Potência Reativa" in tipo_variavel: padrao = f"Q{num_fase}| Q{num_fase}"

        col_encontrada = None
        for col in df.columns:
            if re.search(padrao, col, re.IGNORECASE) and col != col_tempo:
                if "Magnitude" in tipo_variavel and "Ang" in col: continue
                if "Corrente (Magnitude)" in tipo_variavel and "Ang" in col: continue
                col_encontrada = col
                break
        
        if col_encontrada:
            colunas_para_plotar.append((fase_selecionada, col_encontrada))

    # 5. PLOTAGEM (AQUI ESTÁ A CORREÇÃO PARA 3D)
    if colunas_para_plotar:
        fig = go.Figure()

        if modo_visualizacao == "3D (Espacial)":
            # --- MODO 3D ---
            for nome_fase, nome_coluna in colunas_para_plotar:
                y_pos = posicao_fases[nome_fase] # 0, 1 ou 2
                
                fig.add_trace(go.Scatter3d(
                    x=eixo_x,
                    y=[y_pos] * len(eixo_x), # Mantém o Y fixo para criar a "linha" no espaço
                    z=df[nome_coluna],
                    mode='lines',
                    line=dict(width=5),
                    name=nome_fase
                ))
            
            fig.update_layout(
                title=f"Perfil 3D: {escolha_elemento}",
                scene=dict(
                    xaxis_title="Tempo (h)",
                    yaxis=dict(
                        title="Fases",
                        tickvals=[0, 1, 2],
                        ticktext=["Fase A", "Fase B", "Fase C"]
                    ),
                    zaxis_title=tipo_variavel,
                    aspectmode="manual",
                    aspectratio=dict(x=1, y=0.5, z=0.5) # Ajusta proporção para não ficar muito largo
                ),
                height=600,
                margin=dict(l=0, r=0, b=0, t=40)
            )

        else:
            # --- MODO 2D (Tradicional) ---
            for nome_fase, nome_coluna in colunas_para_plotar:
                fig.add_trace(go.Scatter(
                    x=eixo_x,
                    y=df[nome_coluna],
                    mode='lines',
                    name=nome_fase
                ))
            fig.update_layout(
                title=f"Perfil Temporal: {escolha_elemento}",
                xaxis_title="Tempo (h)",
                yaxis_title=tipo_variavel,
                height=500
            )

        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela de dados
        with st.expander("Ver dados brutos"):
            cols_nomes = [c[1] for c in colunas_para_plotar]
            st.dataframe(df[[col_tempo] + cols_nomes])

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
# 8. FUNÇÃO COMPARATIVA 3D (TOPOLOGIA) - VERSÃO COMPLETA COM PU
# ============================================================================
def render_topologia_comparativa():
    st.markdown("## Análise das Barras (Comparativo 3D)")

    # --- 1. CONTROLES DA BARRA LATERAL OU TOPO ---
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        variavel = st.selectbox(
            "Variável:",
            ["Tensão Fase A", "Tensão Fase B", "Tensão Fase C",
             "Corrente Fase A", "Corrente Fase B", "Corrente Fase C",
             "Potência Ativa A", "Potência Ativa B", "Potência Ativa C",
             "Potência Reativa A", "Potência Reativa B", "Potência Reativa C"],
            index=0
        )

    with col2:
        usar_pu = st.checkbox("Visualizar em PU (Por Unidade)", value=True)
        
    with col3:
        # Se for usar PU, precisamos da Base de Potência
        s_base_mva = st.number_input("S Base (MVA):", value=100.0, step=10.0)

    # --- 2. CONFIGURAÇÃO INTELIGENTE (O Segredo para não dar erro) ---
    # Define qual arquivo usar e qual coluna buscar baseado na escolha
    config_map = {
        "Tensão Fase A":    {"tipo": "VI", "col_match": ["V1", " V1"], "unidade": "kV"},
        "Tensão Fase B":    {"tipo": "VI", "col_match": ["V2", " V2"], "unidade": "kV"},
        "Tensão Fase C":    {"tipo": "VI", "col_match": ["V3", " V3"], "unidade": "kV"},
        "Corrente Fase A":  {"tipo": "VI", "col_match": ["I1", " I1"], "unidade": "A"},
        "Corrente Fase B":  {"tipo": "VI", "col_match": ["I2", " I2"], "unidade": "A"},
        "Corrente Fase C":  {"tipo": "VI", "col_match": ["I3", " I3"], "unidade": "A"},
        "Potência Ativa A":   {"tipo": "PQ", "col_match": ["P1", " P1"], "unidade": "kW"},
        "Potência Ativa B":   {"tipo": "PQ", "col_match": ["P2", " P2"], "unidade": "kW"},
        "Potência Ativa C":   {"tipo": "PQ", "col_match": ["P3", " P3"], "unidade": "kW"},
        "Potência Reativa A": {"tipo": "PQ", "col_match": ["Q1", " Q1"], "unidade": "kvar"},
        "Potência Reativa B": {"tipo": "PQ", "col_match": ["Q2", " Q2"], "unidade": "kvar"},
        "Potência Reativa C": {"tipo": "PQ", "col_match": ["Q3", " Q3"], "unidade": "kvar"},
    }

    config_atual = config_map[variavel]
    tipo_arquivo_necessario = config_atual["tipo"] # "VI" ou "PQ"
    lista_colunas_possiveis = config_atual["col_match"]
    
    # --- 3. PROCESSAMENTO DOS DADOS ---
    dados_z = []      
    nomes_eixo_y = [] 
    eixo_x = None     
    
    progresso = st.progress(0, text="Processando topologia...")

    for i, item in enumerate(TOPOLOGIA_SISTEMA):
        nome_barra = item["nome"]
        kv_base_barra = item["kv_base"] # Tensão nominal daquela barra (ex: 13.8 ou 138)
        
        # LÓGICA DE SELEÇÃO DE ARQUIVO (A CORREÇÃO PRINCIPAL)
        if tipo_arquivo_necessario == "VI":
            caminho = item["arquivo_vi"]
        else:
            caminho = item["arquivo_pq"]
            
        df = carregar_dados(caminho)
        
        if df is not None:
            # Tenta achar a coluna correta (ex: V1, P1...)
            coluna_alvo = None
            for col in df.columns:
                if any(x in col for x in lista_colunas_possiveis):
                    coluna_alvo = col
                    break
            
            if coluna_alvo:
                # Captura o Eixo X (Tempo) apenas na primeira iteração válida
                if eixo_x is None:
                    # Tenta achar coluna de tempo ou usa índice
                    col_tempo = next((c for c in df.columns if c.lower() in ["hour", "time", "t(h)"]), None)
                    if col_tempo:
                        eixo_x = df[col_tempo].values
                    else:
                        eixo_x = np.arange(len(df))

                # Pega os valores brutos
                valor_bruto = df[coluna_alvo].values
                valor_final = valor_bruto

                # --- CÁLCULO DO PU (RESTAURADO) ---
                if usar_pu:
                    # 1. Tensão (Vpu = V_lida / Vbase_fase_neutro)
                    # Nota: O arquivo OpenDSS geralmente dá V em Volts ou kV. O kv_base é linha-linha.
                    if "Tensão" in variavel:
                        # Vbase fase-neutro em Volts = (kV_base * 1000) / sqrt(3)
                        # Assumindo que o arquivo CSV traz em Volts (comum em monitores mode=0)
                        # Se o arquivo já estiver em kV, ajustar a multiplicação
                        v_base_volts = (kv_base_barra * 1000) / 1.73205
                        # Se o valor bruto for muito pequeno, pode ser que o csv esteja em kV. 
                        # Aqui assumimos CSV em Volts (padrão OpenDSS Monitor V).
                        valor_final = valor_bruto / v_base_volts

                    # 2. Corrente (Ipu = I / Ibase)
                    elif "Corrente" in variavel:
                        v_base_volts = (kv_base_barra * 1000) # Tensão linha
                        s_base_va = s_base_mva * 1_000_000
                        i_base = s_base_va / (1.73205 * v_base_volts)
                        valor_final = valor_bruto / i_base

                    # 3. Potência (Ppu = P_kW / Sbase_kVA)
                    elif "Potência" in variavel:
                        s_base_kva = s_base_mva * 1000
                        valor_final = valor_bruto / s_base_kva

                dados_z.append(valor_final)
                nomes_eixo_y.append(nome_barra)
        
        # Atualiza barra de progresso
        progresso.progress((i + 1) / len(TOPOLOGIA_SISTEMA))

    progresso.empty()

    # --- 4. PLOTAGEM 3D (SUPERFÍCIE / WATERFALL) ---
    if not dados_z:
        st.error("Não foram encontrados dados compatíveis para a visualização.")
        return

    Z = np.array(dados_z)
    Y_indices = np.arange(len(nomes_eixo_y))
    # Cria malha para o plot
    # Se eixo_x for muito grande, o plot 3D pode ficar pesado. 
    # Dica: Se quiser mais performance, adicione [::5] para pular dados.
    if len(eixo_x) != Z.shape[1]:
        # Fallback se tamanhos diferem
        eixo_x = np.arange(Z.shape[1])
        
    X, Y = np.meshgrid(eixo_x, Y_indices)

    fig = go.Figure()

    # Define Cores
    if "Tensão" in variavel: cmap = 'Viridis'
    elif "Corrente" in variavel: cmap = 'Plasma'
    else: cmap = 'Inferno'

    # Adiciona Superfície
    fig.add_trace(go.Surface(
        z=Z, x=X, y=Y,
        colorscale=cmap,
        colorbar=dict(title="PU" if usar_pu else config_atual["unidade"]),
        opacity=0.9
    ))

    # Adiciona Linhas de destaque (efeito Waterfall) nas bordas
    for i, nome in enumerate(nomes_eixo_y):
        fig.add_trace(go.Scatter3d(
            x=eixo_x,
            y=[i] * len(eixo_x),
            z=Z[i],
            mode='lines',
            line=dict(width=4, color='black'), # Linha preta destaca a borda
            name=nome,
            showlegend=False
        ))

    # Layout
    unidade_z = "PU" if usar_pu else config_atual["unidade"]
    fig.update_layout(
        title=f"Topologia 3D: {variavel} ({unidade_z})",
        scene=dict(
            xaxis_title="Tempo / Amostras",
            yaxis=dict(
                title="Barras (Topologia)",
                tickvals=Y_indices,
                ticktext=nomes_eixo_y
            ),
            zaxis_title=unidade_z,
            aspectmode="manual",
            aspectratio=dict(x=1, y=1.5, z=0.8) # Estica um pouco o Y para ver as barras
        ),
        height=700,
        margin=dict(l=0, r=0, b=0, t=40)
    )

    st.plotly_chart(fig, use_container_width=True)
# ============================================================================
# 9. FUNÇÃO PRINCIPAL DO APLICATIVO
# ============================================================================
def main():
    """Função principal com navegação lateral"""
    
    st.markdown(
        """
        <style>
            [data-testid="stSidebar"] { min-width: 200px; max-width: 200px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Navegação")
        pagina = st.radio(
            "Ir para:",
            ["Análise Linear (2D)", "Análise de Barras (3D)", "Topologia (3D)"]
        )
        st.divider()

    render_cabecalho()

    # ------------------------------------------------------------------------
    # ROTA 1: ANÁLISE 2D (AGORA 100% DINÂMICA)
    # ------------------------------------------------------------------------
    if pagina == "Análise Linear (2D)":
        st.subheader("Análise Linear e Desequilíbrio", divider="green")
        
        tipo_variavel = st.radio(
            "Escolha o tipo de variável:",
            ["Tensão, corrente e ângulo", "Potência ativa e reativa"],
            horizontal=True
        )
        st.divider()

        # 1. Cria as abas automaticamente baseadas no JSON
        nomes_abas = [item["nome"] for item in TOPOLOGIA_SISTEMA]
        if not nomes_abas:
            st.error("Nenhuma barra encontrada no JSON.")
            return

        abas = st.tabs(nomes_abas)

        # Variáveis para guardar dados para o desequilíbrio
        df_sub_baixa = None
        df_carga = None

        # 2. Preenche cada aba num loop inteligente
        for aba, item in zip(abas, TOPOLOGIA_SISTEMA):
            with aba:
                # Define qual arquivo usar
                if tipo_variavel == "Tensão, corrente e ângulo":
                    caminho = item["arquivo_vi"]
                    suffix_key = "vi"
                else:
                    caminho = item["arquivo_pq"]
                    suffix_key = "pq"

                # Plota o gráfico
                df_atual, _, _, _ = carregar_e_plotar(
                    item["nome"], 
                    {"path": caminho}, # Monta o dicionário temporário
                    f"key_{item['nome']}_{suffix_key}" # Chave única
                )

                # 3. Lógica para capturar dados para o Desequilíbrio
                # Tenta identificar pelo 'tipo' definido no JSON
                if item.get("tipo") == "trafo":
                    df_sub_baixa = df_atual
                elif item.get("tipo") == "carga" and df_carga is None: 
                    # Pega a primeira carga que encontrar (ou refine a lógica se precisar da D)
                    df_carga = df_atual
                    
        # -----------------------------------------------------
        # ANÁLISE DE DESEQUILÍBRIO
        # -----------------------------------------------------
        if tipo_variavel == "Tensão, corrente e ângulo":
            # Verifica se achou os dados necessários no loop acima
            if df_sub_baixa is not None and df_carga is not None:
                render_analise_desequilibrio(df_sub_baixa, df_carga)
            elif df_sub_baixa is None and len(TOPOLOGIA_SISTEMA) >= 2:
                # Fallback: Se não achou trafo, tenta usar o primeiro e o último elemento
                st.info("Nota: Usando primeira e última barra para análise de desequilíbrio.")
                # (Lógica simplificada para garantir que rode algo)
                # render_analise_desequilibrio(...) 
            else:
                st.warning("É necessário ter elementos definidos como 'trafo' e 'carga' no JSON para a análise automática de desequilíbrio.")

    # ROTA 2: ANÁLISE DE BARRAS (3D Comparativo)
    elif pagina == "Análise de Barras (3D)":
        render_topologia_comparativa()

    # ROTA 3: ANÁLISE 3D (Individual)
    elif pagina == "Topologia (3D)":
        render_visualizacao_3d_independente()

if __name__ == "__main__":
    main()