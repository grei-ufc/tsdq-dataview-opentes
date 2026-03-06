import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import numpy as np

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Visualizador OpenDSS - Tensão e Corrente")

# =======================================================
# FUNÇÕES DE PROCESSAMENTO E MAPEAMENTO
# =======================================================

def realizar_mapeamento(df):
    """Varre as colunas e organiza todas as grandezas usando Regex."""
    mapa_barras = {}     
    mapa_correntes = {}  
    mapa_angulos = {}    
    mapa_taps = {}       
    mapa_gen_p = {}      # NOVO: Potência de Geradores
    mapa_dni = {}        # NOVO: Irradiância
    mapa_pv_p = {}       # NOVO: Potência PV

    padrao_v = re.compile(r"Bus-([\w]+)-V(\d+)_pu")
    padrao_i = re.compile(r"Line-([\w]+)-I(\d+)_A")
    padrao_a = re.compile(r"Line-([\w]+)-I(\d+)_ang")
    padrao_tap = re.compile(r"RegControl-([\w]+)-tap")
    
    # NOVOS PADRÕES
    padrao_gen_p = re.compile(r"Generator-([\w.-]+)-P_mw")
    padrao_dni = re.compile(r"([\w.-]+)-DNI")
    padrao_pv_p = re.compile(r"([\w.-]+)-P_gen")

    for col in df.columns:
        # Tensão
        m_v = padrao_v.search(col)
        if m_v:
            barra, fase = m_v.group(1), f"V{m_v.group(2)}"
            if barra not in mapa_barras: mapa_barras[barra] = {}
            mapa_barras[barra][fase] = col
            continue

        # Corrente
        m_i = padrao_i.search(col)
        if m_i:
            linha, fase = m_i.group(1), f"I{m_i.group(2)}"
            if linha not in mapa_correntes: mapa_correntes[linha] = {}
            mapa_correntes[linha][fase] = col
            continue
            
        # Ângulo
        m_a = padrao_a.search(col)
        if m_a:
            linha, fase = m_a.group(1), f"I{m_a.group(2)}"
            if linha not in mapa_angulos: mapa_angulos[linha] = {}
            mapa_angulos[linha][fase] = col
            continue

        # Taps
        m_tap = padrao_tap.search(col)
        if m_tap:
            reg = m_tap.group(1)
            if reg not in mapa_taps: mapa_taps[reg] = {}
            mapa_taps[reg]["Tap"] = col
            continue

        # Gerador (MW)
        m_gen = padrao_gen_p.search(col)
        if m_gen:
            gen = m_gen.group(1)
            if gen not in mapa_gen_p: mapa_gen_p[gen] = {}
            mapa_gen_p[gen]["P"] = col
            continue

        # Irradiância (DNI)
        m_dni = padrao_dni.search(col)
        if m_dni:
            sensor = m_dni.group(1)
            if sensor not in mapa_dni: mapa_dni[sensor] = {}
            mapa_dni[sensor]["DNI"] = col
            continue

        # Fotovoltaico (Potência Gerada)
        m_pv = padrao_pv_p.search(col)
        if m_pv:
            pv = m_pv.group(1)
            if pv not in mapa_pv_p: mapa_pv_p[pv] = {}
            mapa_pv_p[pv]["P"] = col
            continue

    return mapa_barras, mapa_correntes, mapa_angulos, mapa_taps, mapa_gen_p, mapa_dni, mapa_pv_p

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
    st.markdown("<h1 style='text-align: center;'>OpenTES - TSDQ</h1>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

def colorir_tabela(val, grandeza_ativa):
    """Aplica cores apenas se a grandeza for Tensão (PRODIST)."""
    if grandeza_ativa != "Tensão (pu)":
        return ''
    color = ''
    if isinstance(val, (int, float)):
        if val < 0.87 or val > 1.06:
            color = 'background-color: #ffcccc; color: red; font-weight: bold;'
        elif val < 0.92 or val > 1.05:
            color = 'background-color: #fff4cc; color: #b36b00;'
    return color

# =======================================================
# EXECUÇÃO PRINCIPAL
# =======================================================

render_cabecalho()

st.info("📂 Carregue o arquivo CSV (Tensão ou Corrente) gerado pelo OpenDSS.")
uploaded_file = st.file_uploader("Arraste seu CSV aqui", type=["csv"])

if uploaded_file:
    # 1. Leitura e Limpeza
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip() 

   # =======================================================
    # 2. TRATAMENTO DE TEMPO (Força Bruta Elegante)
    # =======================================================
    # Pega o nome da primeira coluna do CSV (geralmente é a data)
    primeira_coluna = df.columns[0]
    
    # Tenta converter forçando a inferência de formato do Pandas
    df['Tempo_EixoX'] = pd.to_datetime(df[primeira_coluna].astype(str).str.strip(), format='mixed', errors='coerce')
    
    # Se falhou tudo (tudo virou NaT), cria um Passo numérico
    if df['Tempo_EixoX'].isna().all():
        df['Tempo_EixoX'] = range(len(df))
        
    col_time = 'Tempo_EixoX'

    # 3. Mapeamento de todas as grandezas possíveis
    m_v, m_i, m_ang, m_tap, m_gen, m_dni, m_pv = realizar_mapeamento(df)

    # 4. Interface Lateral para escolha da Grandeza
    st.sidebar.header("Configurações de Dados")
    opcoes_disponiveis = []
    if m_v: opcoes_disponiveis.append("Tensão (pu)")
    if m_i: opcoes_disponiveis.append("Corrente (A)")
    if m_ang: opcoes_disponiveis.append("Ângulo de Corrente (°)")
    if m_tap: opcoes_disponiveis.append("Taps dos Reguladores")
    if m_gen: opcoes_disponiveis.append("Potência do Gerador (MW)")
    if m_dni: opcoes_disponiveis.append("Irradiância Solar (DNI)")
    if m_pv: opcoes_disponiveis.append("Potência Fotovoltaica")

    if not opcoes_disponiveis:
        st.error("❌ O arquivo não possui colunas nos padrões reconhecidos.")
        st.stop()

    grandeza = st.sidebar.selectbox("O que deseja analisar?", opcoes_disponiveis)

    # Configuração dinâmica baseada na grandeza
    if grandeza == "Tensão (pu)":
        mapa_ativo, label_y, prefixo = m_v, "Tensão (pu)", "V"
    elif grandeza == "Corrente (A)":
        mapa_ativo, label_y, prefixo = m_i, "Corrente (A)", "I"
    elif grandeza == "Ângulo de Corrente (°)":
        mapa_ativo, label_y, prefixo = m_ang, "Ângulo (°)", "I"
    elif grandeza == "Taps dos Reguladores":
        mapa_ativo, label_y, prefixo = m_tap, "Posição do Tap", "Tap"
    elif grandeza == "Potência do Gerador (MW)":
        mapa_ativo, label_y, prefixo = m_gen, "Potência Ativa (MW)", "P"
    elif grandeza == "Irradiância Solar (DNI)":
        mapa_ativo, label_y, prefixo = m_dni, "DNI (W/m²)", "DNI"
    elif grandeza == "Potência Fotovoltaica":
        mapa_ativo, label_y, prefixo = m_pv, "Potência Gerada", "P"

    pagina = st.sidebar.radio("Navegação:", ["Gráfico 2D", "Superfície 3D"])

    # Verifica se a grandeza tem 3 fases ou é valor único (Tap, DNI, P)
    tem_fases = grandeza in ["Tensão (pu)", "Corrente (A)", "Ângulo de Corrente (°)"]

    # =======================================================
    # VISUALIZAÇÃO 2D
    # =======================================================
    if pagina == "Gráfico 2D":
        elemento = st.selectbox(f"Selecione o Elemento:", options=sorted(mapa_ativo.keys()))
        
        fig = go.Figure()
        cores_fases = {'1': '#FF4B4B', '2': '#1C83E1', '3': '#00CC96'}
        
        chaves_para_plotar = [f"{prefixo}1", f"{prefixo}2", f"{prefixo}3"] if tem_fases else [prefixo]

        for chave in chaves_para_plotar:
            if chave in mapa_ativo[elemento]:
                # Configurações visuais (nome da legenda, cor, formato da linha)
                if tem_fases:
                    nome_legenda = f"Fase {chave[-1]}"
                    cor_linha = cores_fases.get(chave[-1], '#000')
                    formato_linha = 'linear'
                else:
                    nome_legenda = grandeza
                    cor_linha = '#9B59B6' if prefixo == 'Tap' else '#F39C12'
                    formato_linha = 'hv' if prefixo == 'Tap' else 'linear'
                
                fig.add_trace(go.Scatter(
                    x=df[col_time], y=df[mapa_ativo[elemento][chave]],
                    mode='lines', name=nome_legenda, line=dict(color=cor_linha),
                    line_shape=formato_linha
                ))

        fig.update_layout(title=f"{grandeza} - {elemento}", yaxis_title=label_y, template="plotly_white", height=600)
        st.plotly_chart(fig, use_container_width=True)

    # =======================================================
    # VISUALIZAÇÃO 3D
    # =======================================================
    elif pagina == "Superfície 3D":
        if tem_fases:
            f_esc = st.radio("Escolha a Fase para o Mapa:", [1, 2, 3], horizontal=True)
            f_key = f"{prefixo}{f_esc}"
            titulo_3d = f"Mapa de {grandeza} - Fase {f_esc}"
        else:
            f_key = prefixo
            titulo_3d = f"Mapa de {grandeza}"
            st.info(f"💡 Exibindo o mapa 3D geral para {grandeza}.")
        
        lista_elementos = sorted(mapa_ativo.keys())
        z_data = []
        for el in lista_elementos:
            if f_key in mapa_ativo[el]:
                z_data.append(df[mapa_ativo[el][f_key]].values)
            else:
                z_data.append(np.full(len(df), np.nan))
        
        z_matrix = np.array(z_data).T
        fig_3d = go.Figure(data=[go.Surface(z=z_matrix, x=lista_elementos, colorscale='Viridis')])
        
        fig_3d.update_layout(
            title=titulo_3d,
            scene=dict(xaxis_title="Elementos", yaxis_title="Tempo", zaxis_title=label_y),
            height=750
        )
        st.plotly_chart(fig_3d, use_container_width=True)

    # =======================================================
    # TABELA DE DADOS
    # =======================================================
    with st.expander("📊 Ver Tabela de Dados"):
        # 1. Identifica quais colunas são numéricas (exclui a coluna de tempo/data)
        colunas_numericas = df.select_dtypes(include=['float64', 'float32']).columns
        
        # 2. Aplica a formatação e as cores apenas nesse subconjunto (subset)
        st.dataframe(
            df.style
            .format("{:.6f}", subset=colunas_numericas)
            .map(colorir_tabela, grandeza_ativa=grandeza, subset=colunas_numericas),
            use_container_width=True
        )

else:
    st.warning("⚠️ Aguardando upload do arquivo CSV...")