import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Dashboard Qualidade de Energia - DRP/DRC")

# =======================================================
# FUNÇÕES DE PROCESSAMENTO E MAPEAMENTO
# =======================================================

def mapear_grandezas_medidor(df):
    """
    Busca as colunas de Tensão Média e Corrente Média na planilha do medidor.
    """
    mapa_tensoes = {}
    mapa_correntes = {}
    
    for col in df.columns:
        col_lower = col.lower()
        
        # Mapeamento de Tensões de Fase (van, vbn, vcn) - Pega apenas a média
        if 'tensao.average.v' in col_lower:
            if 'an' in col_lower: mapa_tensoes['Fase A'] = col
            elif 'bn' in col_lower: mapa_tensoes['Fase B'] = col
            elif 'cn' in col_lower: mapa_tensoes['Fase C'] = col
            
        # Mapeamento de Correntes (ia, ib, ic, in) - Pega apenas a média
        elif 'corrente.average.i' in col_lower:
            if 'ia' in col_lower: mapa_correntes['Fase A'] = col
            elif 'ib' in col_lower: mapa_correntes['Fase B'] = col
            elif 'ic' in col_lower: mapa_correntes['Fase C'] = col
            elif 'in' in col_lower: mapa_correntes['Neutro'] = col
                
    return mapa_tensoes, mapa_correntes

def calcular_limites(vn):
    """Calcula limites simplificados de DRP/DRC baseados na Tensão Nominal (Vn)."""
    # Atenção: Ajuste estas porcentagens conforme a norma exata do PRODIST
    limite_adequada_min = vn * 0.92
    limite_adequada_max = vn * 1.05
    limite_precaria_min = vn * 0.87
    limite_precaria_max = vn * 1.06
    
    return limite_adequada_min, limite_adequada_max, limite_precaria_min, limite_precaria_max

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
    st.markdown("<h1 style='text-align: center;'>Análise de Qualidade de Energia - DRP / DRC</h1>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

# =======================================================
# EXECUÇÃO PRINCIPAL
# =======================================================

render_cabecalho()

st.info("📂 Carregue o arquivo CSV ou XLSX com as medições do equipamento.")
uploaded_file = st.file_uploader("Arraste seu arquivo aqui", type=["csv", "xlsx"])

if uploaded_file:
    # 1. Leitura Robusta
    try:
        if uploaded_file.name.endswith('.csv'):
            try:
                df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8')
            except Exception:
                uploaded_file.seek(0)
                df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
            
        df.columns = df.columns.str.strip()
        
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")
        st.stop()

    # 2. TRATAMENTO DE TEMPO
    primeira_coluna = df.columns[0]
    df['Tempo_EixoX'] = pd.to_datetime(df[primeira_coluna].astype(str).str.strip(), format='mixed', errors='coerce')
    if df['Tempo_EixoX'].isna().all():
        df['Tempo_EixoX'] = range(len(df))
    col_time = 'Tempo_EixoX'

    # 3. Mapeamento de Variáveis
    mapa_tensoes, mapa_correntes = mapear_grandezas_medidor(df)

    if not mapa_tensoes:
        st.error("❌ Não foram encontradas colunas de tensão no arquivo.")
        st.stop()

    # 4. Interface Lateral
    st.sidebar.header("Configurações PRODIST")
    vn = st.sidebar.number_input("Tensão Nominal (Vn) em Volts:", min_value=110.0, max_value=38000.0, value=220.0, step=1.0)
    
    # Adicionada a nova página para o Gráfico de Correntes
    pagina = st.sidebar.radio("Navegação:", ["Gráfico de Tensões 2D", "Gráfico de Correntes (Equilíbrio)", "Relatório DRP e DRC"])

    l_adq_min, l_adq_max, l_prec_min, l_prec_max = calcular_limites(vn)
    
    # Dicionário de cores padrão para manter a coerência visual
    cores_grafico = {'Fase A': '#FF4B4B', 'Fase B': '#1C83E1', 'Fase C': '#00CC96', 'Neutro': '#555555'}

    # =======================================================
    # VISUALIZAÇÃO 2D (Perfil de Tensão)
    # =======================================================
    if pagina == "Gráfico de Tensões 2D":
        st.subheader("Perfil de Tensão ao Longo do Tempo")
        fig = go.Figure()

        for nome_fase, col_name in mapa_tensoes.items():
            fig.add_trace(go.Scatter(
                x=df[col_time], y=df[col_name],
                mode='lines', name=nome_fase, 
                line=dict(color=cores_grafico.get(nome_fase, '#333')),
            ))

        fig.add_hline(y=l_adq_max, line_dash="dash", line_color="orange", annotation_text="Max Adequada")
        fig.add_hline(y=l_adq_min, line_dash="dash", line_color="orange", annotation_text="Min Adequada")
        fig.add_hline(y=l_prec_max, line_dash="dot", line_color="red", annotation_text="Crítica Superior")
        fig.add_hline(y=l_prec_min, line_dash="dot", line_color="red", annotation_text="Crítica Inferior")

        fig.update_layout(yaxis_title="Tensão (V)", template="plotly_white", height=600)
        st.plotly_chart(fig, use_container_width=True)

    # =======================================================
    # NOVO: VISUALIZAÇÃO DE CORRENTES
    # =======================================================
    elif pagina == "Gráfico de Correntes (Equilíbrio)":
        st.subheader("Perfil de Correntes - Análise de Equilíbrio das Fases")
        
        if mapa_correntes:
            fig_i = go.Figure()

            for nome_fase, col_name in mapa_correntes.items():
                fig_i.add_trace(go.Scatter(
                    x=df[col_time], y=df[col_name],
                    mode='lines', name=nome_fase, 
                    line=dict(color=cores_grafico.get(nome_fase, '#333')),
                ))

            fig_i.update_layout(yaxis_title="Corrente (A)", template="plotly_white", height=600)
            st.plotly_chart(fig_i, use_container_width=True)
            
            # Caixa de informação com dicas técnicas
            st.info("""
            **💡 Como analisar este gráfico:**
            - **Equilíbrio:** Em um cenário ideal, as linhas das Fases A, B e C (vermelho, azul e verde) deveriam se sobrepor ou estarem bem próximas.
            - **Corrente de Neutro:** A linha cinza (Neutro) deve estar sempre o mais próxima possível de zero. Se o neutro apresentar correntes elevadas, as fases estão desequilibradas.
            """)
        else:
            st.warning("⚠️ Não foram encontradas colunas de corrente nesta planilha.")

    # =======================================================
    # RELATÓRIO DRP / DRC
    # =======================================================
    elif pagina == "Relatório DRP e DRC":
        st.subheader("Cálculo de Duração Relativa (DRP e DRC)")
        st.write(f"**Tensão Nominal de Referência:** {vn} V")
        
        col1, col2, col3 = st.columns(3)
        total_medicoes = len(df)
        
        for nome_fase, col_name in mapa_tensoes.items():
            tensoes = df[col_name].dropna()
            
            leituras_adequadas = tensoes[(tensoes >= l_adq_min) & (tensoes <= l_adq_max)].count()
            leituras_precarias = tensoes[((tensoes >= l_prec_min) & (tensoes < l_adq_min)) | 
                                         ((tensoes > l_adq_max) & (tensoes <= l_prec_max))].count()
            leituras_criticas = tensoes[(tensoes < l_prec_min) | (tensoes > l_prec_max)].count()
            
            drp = (leituras_precarias / total_medicoes) * 100
            drc = (leituras_criticas / total_medicoes) * 100
            
            with (col1 if 'A' in nome_fase else col2 if 'B' in nome_fase else col3):
                st.markdown(f"### {nome_fase}")
                st.metric(label="DRP (Tensão Precária)", value=f"{drp:.2f} %", 
                          delta="Atenção" if drp > 3 else "Normal", delta_color="inverse")
                st.metric(label="DRC (Tensão Crítica)", value=f"{drc:.2f} %", 
                          delta="Crítico" if drc > 0.5 else "Normal", delta_color="inverse")
                st.write(f"Leituras Adequadas: {leituras_adequadas}")

    # =======================================================
    # TABELA DE DADOS
    # =======================================================
    with st.expander("📊 Ver Tabela de Dados Originais"):
        st.dataframe(df, use_container_width=True)

else:
    st.warning("⚠️ Aguardando upload da planilha de medições...")