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
# UTILITÁRIO DE ESCALA (ADICIONAR LOGO APÓS OS IMPORTS)
# =======================================================

def auto_scale(value, unit):
    if value == 0:
        return 0, unit

    exp = int(np.floor(np.log10(abs(value)) / 3) * 3)

    scale_map = {
        -3: ("m", 1e-3),
        0: ("", 1),
        3: ("k", 1e3),
        6: ("M", 1e6),
        9: ("G", 1e9),
    }

    exp = max(min(exp, 9), -3)

    prefix, factor = scale_map.get(exp, ("", 1))

    return value / factor, prefix + unit

unit_map = {
    "Potência Ativa": ("W", 1e6),
    "Potência Reativa": ("var", 1e6),
    "Tensão (pu)": ("pu", 1),
    "Corrente": ("A", 1),
}

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
    # Compila os padrões regex, IGNORANDO as configurações de sistema que começam com "_"
    padroes = {
        grandeza: re.compile(dados["regex"]) 
        for grandeza, dados in config.items() 
            if not grandeza.startswith("_")
    }

    for col in df.columns:
        for grandeza, dados in config.items():
            if grandeza.startswith("_"):
                continue
            match = padroes[grandeza].search(col)
            if match:
                elemento = match.group(1) 
                if dados["tem_fase"]:
                    fase_num = match.group(2)
                    fase = f"{dados['prefixo']}{fase_num}" if fase_num else dados["prefixo"]
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

    pagina = st.sidebar.radio(
        "Navegação:",
        ["Gráfico 2D", "Superfície 3D", "Mapa Geográfico", "Comunicação"]
    )

    # =======================================================
    # VISUALIZAÇÃO 2D
    # =======================================================
    
    if pagina == "Gráfico 2D":

        def formatar_nome(nome):
            if nome.endswith('r') and prefixo == 'V':
                return f"{nome} (Lado Secundário/Regulado)"
            elif f"{nome}r" in mapa_ativo.keys() and prefixo == 'V':
                return f"{nome} (Lado Primário da Fonte)"
            return nome

        elemento = st.selectbox(
            f"Selecione o Elemento:", 
            options=sorted(mapa_ativo.keys()),
            format_func=formatar_nome
        )

        fig = go.Figure()
        cores_fases = {'1': '#FF4B4B', '2': '#1C83E1', '3': '#00CC96'}

        # DEFINIÇÃO DAS CHAVES
        if tem_fases:
            chaves_para_plotar = [f"{prefixo}1", f"{prefixo}2", f"{prefixo}3", prefixo]
        else:
            chaves_para_plotar = [prefixo]

        # ESCALA GLOBAL
        
        primeira_chave_valida = next((c for c in chaves_para_plotar if c in mapa_ativo[elemento]), None)

        coluna_exemplo = mapa_ativo[elemento][primeira_chave_valida]

        if "_MW" in coluna_exemplo:
            unidade_base = "W"
            fator = 1e6
        elif "_Mvar" in coluna_exemplo:
            unidade_base = "var"
            fator = 1e6
        elif "P_gen" in coluna_exemplo:
            if "_MW" in coluna_exemplo:
                unidade_base = "W"
                fator = 1e6
            elif "_kW" in coluna_exemplo:
                unidade_base = "W"
                fator = 1e3
            else:
                unidade_base = "W"
                fator = 1
        elif "_kW" in coluna_exemplo:
            unidade_base = "W"
            fator = 1e3
        elif "_W" in coluna_exemplo:
            unidade_base = "W"
            fator = 1
        elif "_pu" in coluna_exemplo:
            unidade_base = "pu"
            fator = 1
        elif "_kV" in coluna_exemplo:
            unidade_base = "V"
            fator = 1e3
        elif "_V" in coluna_exemplo:
            unidade_base = "V"
            fator = 1
        elif "_A" in coluna_exemplo:
            unidade_base = "A"
            fator = 1
        else:
            unidade_base = ""
            fator = 1

        # ESCALA GLOBAL CORRIGIDA
        todos_valores = []

        for chave in chaves_para_plotar:
            if chave in mapa_ativo[elemento]:
                dados_temp = df[mapa_ativo[elemento][chave]] * fator
                todos_valores.append(dados_temp.abs().max())

        valor_referencia = max(todos_valores) if todos_valores else 0

        if valor_referencia > 0:
            if unidade_base in ["W", "var"] and valor_referencia < 1:
                unidade_final = unidade_base
                fator_escala_global = 1
            else:
                valor_ref_scaled, unidade_final = auto_scale(valor_referencia, unidade_base)
                fator_escala_global = valor_referencia / valor_ref_scaled
        else:
            unidade_final = unidade_base
            fator_escala_global = 1

        for chave in chaves_para_plotar:
            if chave in mapa_ativo[elemento]:
                dados_y = df[mapa_ativo[elemento][chave]]

                dados_convertidos = dados_y * fator
                dados_plot = dados_convertidos / fator_escala_global

                val_min = dados_plot.min()
                val_max = dados_plot.max()

                cor_linha = '#000000'  # padrão (preto)

                if tem_fases:
                    nome_legenda = f"Fase {chave[-1]} (Mín: {val_min:.5g} | Máx: {val_max:.5g})"
                    cor_linha = cores_fases.get(chave[-1], '#000000')
                    formato_linha = 'linear'
                else:
                    nome_legenda = f"{elemento} (Mín: {val_min:.5g} | Máx: {val_max:.5g})"
                    cor_linha = '#9B59B6' if prefixo == 'Tap' else '#F39C12'
                    formato_linha = 'hv' if prefixo == 'Tap' else 'linear'

                fig.add_trace(go.Scatter(
                    x=df[col_time],
                    y=dados_plot,
                    mode='lines',
                    name=nome_legenda,
                    line=dict(color=cor_linha),
                    line_shape=formato_linha
                ))

        # LIMITES PRODIST
        if grandeza == "Tensão":
            tempo_min = df[col_time].min()
            tempo_max = df[col_time].max()

            fig.add_trace(go.Scatter(
                x=[tempo_min, tempo_max],
                y=[1.05, 1.05],
                mode='lines',
                name='🚨 Limite Sup. (1.05)',
                line=dict(color='red', dash='dash'),
                visible='legendonly'
            ))

            fig.add_trace(go.Scatter(
                x=[tempo_min, tempo_max],
                y=[0.92, 0.92],
                mode='lines',
                name='🚨 Limite Inf. (0.92)',
                line=dict(color='orange', dash='dash'),
                visible='legendonly'
            ))

        nome_limpo = re.sub(r"\s*\(.*?\)", "", grandeza)

        # LIMITE DINÂMICO LOCAL (por elemento)
        y_min = float('inf')
        y_max = float('-inf')

        for chave in chaves_para_plotar:
            if chave in mapa_ativo[elemento]:
                dados_y = df[mapa_ativo[elemento][chave]] * fator
                dados_plot = dados_y / fator_escala_global

                y_min = min(y_min, dados_plot.min())
                y_max = max(y_max, dados_plot.max())

        # proteção contra erro
        if y_min == float('inf') or y_max == float('-inf'):
            y_min, y_max = 0, 1

        # margem de 5%
        margem = 0.05 * (y_max - y_min) if y_max != y_min else 0.01

        fig.update_layout(
            title=f"{grandeza} - {elemento}",
            yaxis=dict(
                title=f"{nome_limpo} [{unidade_final}]",
                range=[y_min - margem, y_max + margem],
                nticks=12,
                tickformat=".5g",
                zeroline=False
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
    # VISUALIZAÇÃO GEOGRÁFICA (MAPA)
    # =======================================================
    elif pagina == "Mapa Geográfico":
        st.header("🗺️ Visualização Geográfica do Sistema")
        st.markdown("Faça o upload do ficheiro de coordenadas do seu circuito para visualizar a topologia da rede.")
        
        # 1. Puxa as regras de colunas do JSON (com valores padrão por segurança)
        col_nome = "Barra"
        col_x = "X"
        col_y = "Y"
        
        if "_Configuracoes_Geograficas" in config_metadados:
            config_geo = config_metadados["_Configuracoes_Geograficas"]
            col_nome = config_geo.get("coluna_elemento", col_nome)
            col_x = config_geo.get("coluna_x", col_x)
            col_y = config_geo.get("coluna_y", col_y)
            
        st.info(f"ℹ️ **Padrão esperado pelo JSON:** Coluna do Elemento: `{col_nome}` | Eixo X: `{col_x}` | Eixo Y: `{col_y}`")

        # 2. Componente de Upload Seguro (usando o parâmetro KEY)
        arquivo_geo_upload = st.file_uploader(
            "Selecione o ficheiro de coordenadas (CSV ou TXT)", 
            type=["csv", "txt"], 
            key="upload_coordenadas" # <-- O segredo para não haver conflitos!
        )
        
        if arquivo_geo_upload is not None:
            # 3. Lê os dados do ficheiro carregado
            df_geo = pd.read_csv(arquivo_geo_upload)
            
            # 4. Verifica se as colunas configuradas no JSON realmente existem no ficheiro
            if col_nome in df_geo.columns and col_x in df_geo.columns and col_y in df_geo.columns:
                
                fig_mapa = go.Figure()
                
                # Adiciona os pontos (barras/equipamentos) no gráfico
                fig_mapa.add_trace(go.Scatter(
                    x=df_geo[col_x],
                    y=df_geo[col_y],
                    mode='markers+text',
                    text=df_geo[col_nome],
                    textposition="top center",
                    marker=dict(size=12, color='#2ECC71', line=dict(width=2, color='DarkSlateGrey')),
                    name="Elementos da Rede",
                    hoverinfo="text"
                ))
                
                fig_mapa.update_layout(
                    title="Topologia do Circuito",
                    xaxis_title=f"Eixo X ({col_x})",
                    yaxis_title=f"Eixo Y ({col_y})",
                    height=750,
                    template="plotly_white",
                    # scaleanchor e scaleratio garantem que o mapa não fique achatado ou esticado
                    yaxis=dict(scaleanchor="x", scaleratio=1) 
                )
                
                st.plotly_chart(fig_mapa, use_container_width=True)
                
                with st.expander("📊 Ver Tabela de Coordenadas"):
                    st.dataframe(df_geo)
                    
            else:
                st.error("❌ O ficheiro carregado não possui as colunas esperadas!")
                st.warning(f"O sistema procurou por: `{col_nome}`, `{col_x}` e `{col_y}` (conforme configurado no `mapeamento.json`).")
                st.write("**Colunas encontradas no seu ficheiro:**", list(df_geo.columns))
    # =======================================================
    # VISUALIZAÇÃO DE COMUNICAÇÃO (OMNeT)
    # =======================================================
    elif pagina == "Comunicação":
        st.header("📡 Comunicação - OMNeT++")

        arquivo_com = st.file_uploader(
            "Selecione o arquivo de comunicação (results.csv)",
            type=["csv"],
            key="upload_comunicacao"
        )

        if arquivo_com is not None:
            # leitura
            df_com = pd.read_csv(arquivo_com)

            # limpeza
            df_com.columns = df_com.columns.str.strip()

            # validação do seu padrão
            colunas_necessarias = ["Tempo", "Origem", "Atributo", "Valor"]

            if all(col in df_com.columns for col in colunas_necessarias):

                # conversões
                df_com["Tempo"] = pd.to_numeric(df_com["Tempo"], errors="coerce")
                df_com["Valor_num"] = pd.to_numeric(df_com["Valor"], errors="coerce")

                # remove inválidos
                df_com = df_com.dropna(subset=["Tempo", "Valor_num"])

                # cria variável
                df_com["variavel"] = df_com["Origem"] + " | " + df_com["Atributo"]

                # pivot correto
                df_pivot = df_com.pivot_table(
                    index="Tempo",
                    columns="variavel",
                    values="Valor_num",
                    aggfunc="mean"
                ).reset_index()

                df_pivot = df_pivot.sort_values("Tempo")

                st.success("Arquivo de comunicação carregado corretamente.")

            else:
                st.error(f"""
            Formato inválido.

            Esperado:
            Tempo | Origem | Atributo | Valor

            Encontrado:
            {list(df_com.columns)}
            """)
                st.stop()

                # seleção de variável
                st.success("Arquivo de comunicação carregado corretamente.")

                colunas_validas = [
                    c for c in df_pivot.columns
                    if c != "Tempo" and df_pivot[c].notna().sum() > 0
                ]

                if len(colunas_validas) == 0:
                    st.warning("Nenhuma variável numérica disponível para plotagem.")
                    st.stop()

                variavel = st.selectbox(
                    "Selecione a variável",
                    colunas_validas
                )

                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=df_pivot["Tempo"],
                    y=df_pivot[variavel],
                    mode='lines',
                    name=variavel
                ))

                st.plotly_chart(fig, use_container_width=True)

                with st.expander("📊 Ver dados de comunicação"):
                    st.dataframe(df_pivot)
            #else:
            #    st.error("Formato do arquivo OMNeT inválido (esperado: colunas 'time' e 'value').")
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