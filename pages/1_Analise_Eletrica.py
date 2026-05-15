import streamlit as st
from utils.leitura import ler_csv
from utils.leitura import processar_tempo
from utils.mapeamento import carregar_mapeamento
from utils.mapeamento import mapear_colunas
from utils.processamento import (
    organizar_variaveis,
    preparar_serie_temporal
)
import plotly.express as px


st.set_page_config(
    page_title="Análise Elétrica",
    layout="wide"
)

st.title("Análise Elétrica")

st.markdown("""
Módulo para análise de resultados
provenientes de simulações elétricas.
""")


if "arquivo_eletrico" not in st.session_state:

    st.session_state.arquivo_eletrico = None

if st.session_state.arquivo_eletrico is None:

    uploaded_file = st.file_uploader(
        "Carregue o arquivo CSV",
        type=["csv"]
    )

    if uploaded_file is not None:

        st.session_state.arquivo_eletrico = (
            uploaded_file
        )

        st.rerun()

else:

    uploaded_file = (
        st.session_state.arquivo_eletrico
    )

    st.info(
        f"Arquivo carregado: {uploaded_file.name}"
    )

    if st.button("Carregar novo arquivo"):

        st.session_state.arquivo_eletrico = None

        st.rerun()


if uploaded_file is not None:

    df = ler_csv(uploaded_file)

    df = processar_tempo(df)

    mapeamento = carregar_mapeamento()

    colunas_mapeadas = mapear_colunas(
        df.columns,
        mapeamento
    )

    estrutura = organizar_variaveis(
        colunas_mapeadas
    )

    tipos_disponiveis = list(
        estrutura.keys()
    )

    tipo_escolhido = st.selectbox(
        "Tipo de variável",
        tipos_disponiveis
    )

    elementos = list(
        estrutura[tipo_escolhido].keys()
    )

    elemento_escolhido = st.selectbox(
        "Elemento",
        elementos
    )

    variaveis = estrutura[
        tipo_escolhido
    ][
        elemento_escolhido
    ]

    opcoes_variaveis = []

    for variavel in variaveis:

        fase = variavel.get("fase")

        unidade = variavel.get(
            "unidade_detectada"
        )

        nome = ""

        if fase:
            nome += fase

        if unidade:

            if nome:
                nome += " "

            nome += f"({unidade})"

        if not nome:
            nome = variavel["tipo"]

        opcoes_variaveis.append(nome)

    if len(variaveis) == 1:

        variavel_info = variaveis[0]

    else:

        variavel_escolhida = st.selectbox(
            "Variável",
            opcoes_variaveis
        )

        indice = opcoes_variaveis.index(
            variavel_escolhida
        )

        variavel_info = variaveis[indice]

    dados_plot = preparar_serie_temporal(
        df,
        variavel_info
    )

    df_plot = dados_plot["df_plot"]

    label_y = dados_plot["label_y"]

    coluna_real = dados_plot[
        "coluna_real"
    ]

    with st.expander(
        "Pré-visualização em código"
    ):

        st.json(variavel_info)

    st.subheader("Pré-visualização da Série")

    st.dataframe(
        df_plot.head(10)
    )

    fig = px.line(
        df_plot,
        x="Tempo",
        y="Valor",
        title=coluna_real
    )

    fig.update_layout(

        xaxis_title="Tempo",

        yaxis_title=label_y,

        hovermode="x unified"
    )

    st.subheader("Série Temporal")

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.subheader("Pré-visualização Completa")

    st.dataframe(df)