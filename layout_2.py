import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re
import numpy as np
import json
import os 
# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Visualizador OpenDSS - Tensão e Corrente")

# =======================================================
# FUNÇÕES DE PROCESSAMENTO E MAPEAMENTO
# =======================================================

# 1. Função para ler o arquivo JSON de metadados
def carregar_metadados(nome_arquivo="mapeamento.json"):
    # Descobre a pasta exata onde este arquivo layout_2.py está salvo
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    # Monta o caminho completo até o JSON
    caminho_completo = os.path.join(diretorio_atual, nome_arquivo)
    
    try:
        with open(caminho_completo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        import streamlit as st
        st.error(f"❌ Arquivo de configuração não encontrado!")
        st.warning(f"O código procurou o arquivo exatamente aqui:\n`{caminho_completo}`")
        st.info("💡 Dica: Verifique se o arquivo não foi salvo acidentalmente como 'mapeamento.json.txt' (o Windows costuma ocultar o .txt final).")
        st.stop()

# 2. Nova função de mapeamento dinâmico
def realizar_mapeamento_dinamico(df, config):
    """Varre as colunas e organiza os dados com base no JSON de metadados."""
    mapas = {grandeza: {} for grandeza in config.keys()}
    padroes = {grandeza: re.compile(dados["regex"]) for grandeza, dados in config.items()}

    for col in df.columns:
        for grandeza, dados in config.items():
            match = padroes[grandeza].search(col)
            if match:
                elemento = match.group(1) 
                if dados["tem_fase"]:
                    fase = f"{dados['prefixo']}{match.group(2)}"
                else:
                    fase = dados["prefixo"]
                
                if elemento not in mapas[grandeza]:
                    mapas[grandeza][elemento] = {}
                mapas[grandeza][elemento][fase] = col
                break 
                
    return mapas

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

    # 3. Mapeamento Dinâmico via JSON
    config_metadados = carregar_metadados("mapeamento.json")
    mapas_gerais = realizar_mapeamento_dinamico(df, config_metadados)

    # 4. Interface Lateral para escolha da Grandeza
    st.sidebar.header("Configurações de Dados")
    opcoes_disponiveis = [g for g, mapa in mapas_gerais.items() if mapa]

    if not opcoes_disponiveis:
        st.error("❌ O arquivo não possui colunas que correspondam aos metadados cadastrados no JSON.")
        st.stop()

    grandeza = st.sidebar.selectbox("O que deseja analisar?", opcoes_disponiveis)

    # 5. Configuração dinâmica puxada diretamente do JSON
    mapa_ativo = mapas_gerais[grandeza]
    config_ativa = config_metadados[grandeza]
    
    prefixo = config_ativa["prefixo"]
    tem_fases = config_ativa["tem_fase"]
    label_y = grandeza 

    pagina = st.sidebar.radio("Navegação:", ["Gráfico 2D", "Superfície 3D"])

    # =======================================================
    # VISUALIZAÇÃO 2D
    # =======================================================
    if pagina == "Gráfico 2D":
        # Função para deixar os nomes mais claros no menu
        def formatar_nome(nome):
            if nome.endswith('r') and prefixo == 'V':
                return f"{nome} (Lado Secundário/Regulado)"
            elif f"{nome}r" in mapa_ativo.keys() and prefixo == 'V':
                return f"{nome} (Lado Primário da Fonte)"
            return nome

        # Botão com os nomes formatados
        elemento = st.selectbox(
            f"Selecione o Elemento:", 
            options=sorted(mapa_ativo.keys()),
            format_func=formatar_nome
        )
        
        # Caixinha de aviso inteligente (Aparece só quando necessário)
        if elemento.endswith('r') and prefixo == 'V':
            st.info(f"💡 **Você sabia?** A barra **{elemento}** representa o lado secundário de um Regulador de Tensão. A tensão aqui já sofreu a correção do Tap em relação à barra **{elemento[:-1]}**.")
        elif f"{elemento}r" in mapa_ativo.keys() and prefixo == 'V':
            st.info(f"💡 **Dica:** Esta barra é o lado primário de um Regulador. Compare-a com a barra **{elemento}r** para ver o salto de tensão causado pelo Tap!")

        fig = go.Figure()
        cores_fases = {'1': '#FF4B4B', '2': '#1C83E1', '3': '#00CC96'}
        
        chaves_para_plotar = [f"{prefixo}1", f"{prefixo}2", f"{prefixo}3"] if tem_fases else [prefixo]

        for chave in chaves_para_plotar:
            if chave in mapa_ativo[elemento]:
                # Captura os dados numéricos dessa curva
                dados_y = df[mapa_ativo[elemento][chave]]
                val_min = dados_y.min()
                val_max = dados_y.max()
                
                # NOVO: Trocamos .3f por .5g para exibir valores minúsculos com precisão!
                if tem_fases:
                    nome_legenda = f"Fase {chave[-1]} (Mín: {val_min:.5g} | Máx: {val_max:.5g})"
                    cor_linha = cores_fases.get(chave[-1], '#000')
                    formato_linha = 'linear'
                else:
                    nome_legenda = f"{grandeza} (Mín: {val_min:.5g} | Máx: {val_max:.5g})"
                    cor_linha = '#9B59B6' if prefixo == 'Tap' else '#F39C12'
                    formato_linha = 'hv' if prefixo == 'Tap' else 'linear'
                
                fig.add_trace(go.Scatter(
                    x=df[col_time], y=dados_y,
                    mode='lines', name=nome_legenda, line=dict(color=cor_linha),
                    line_shape=formato_linha
                ))

        # Adiciona limites clicáveis do PRODIST apenas se for Tensão
        if grandeza == "Tensão (pu)":
            tempo_min = df[col_time].min()
            tempo_max = df[col_time].max()
            fig.add_trace(go.Scatter(x=[tempo_min, tempo_max], y=[1.05, 1.05], mode='lines', name='🚨 Limite Sup. (1.05)', line=dict(color='red', dash='dash'), visible='legendonly'))
            fig.add_trace(go.Scatter(x=[tempo_min, tempo_max], y=[0.92, 0.92], mode='lines', name='🚨 Limite Inf. (0.92)', line=dict(color='orange', dash='dash'), visible='legendonly'))

        # A Mágica do Eixo Y Automático e Inteligente
        fig.update_layout(
            title=f"{grandeza} - {elemento}", 
            yaxis=dict(
                title=label_y,
                autorange=True,
                nticks=12,
                tickformat=".5g",  # <-- NOVO: Força o Plotly a mostrar micro-variações no eixo Y
                zeroline=False     # <-- NOVO: Desligamos a linha do zero para ela não esmagar o zoom
            ),
            xaxis_title="Tempo",
            template="plotly_white", 
            height=600,
            hovermode="x unified"
        )
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
        
        # --- NOVO: Tratamento do Eixo Y para Horário ---
        # Se a coluna de tempo for do tipo data, extrai apenas a Hora e o Minuto (HH:MM)
        if pd.api.types.is_datetime64_any_dtype(df[col_time]):
            eixo_y = df[col_time].dt.strftime('%H:%M')
        else:
            eixo_y = df[col_time] # Se for apenas um 'Passo' numérico, usa ele mesmo
            
        # Adicionamos y=eixo_y na construção da Superfície
        fig_3d = go.Figure(data=[go.Surface(
            z=z_matrix, 
            x=lista_elementos, 
            y=eixo_y, 
            colorscale='Viridis',
            colorbar=dict(
                title=label_y,
                nticks=15,        # Força 15 valores diferentes na barra de cores
                tickformat=".3f"  # Mostra 3 casas decimais (ex: 1.025)
            )
        )])
        
        fig_3d.update_layout(
            title=titulo_3d,
            scene=dict(
                xaxis_title="Elementos", 
                yaxis_title="Horário", 
                zaxis_title=label_y,
                zaxis=dict(
                    nticks=15,        # Força 15 valores na escala vertical do gráfico 3D
                    tickformat=".3f"  # Mostra 3 casas decimais
                )
            ),
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