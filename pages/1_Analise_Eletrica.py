import streamlit as st
from utils.leitura import ler_csv
from utils.leitura import processar_tempo
from utils.mapeamento import carregar_mapeamento
from utils.mapeamento import mapear_colunas
from utils.processamento import (
    organizar_variaveis,
    preparar_serie_temporal,
    preparar_multiplas_series
)
import plotly.express as px
from components.uploader import render_upload
from utils.prodist import (
    obter_limites_prodist
)
from utils.escalas import auto_scale

st.set_page_config(
    page_title="Análise Elétrica",
    layout="wide"
)

st.title("Análise Elétrica")

st.markdown("""
Módulo para análise de resultados
provenientes de simulações elétricas.
""")


uploaded_file = render_upload(
    session_key="arquivo_eletrico",
    label="Carregue o arquivo CSV",
    file_types=["csv"]
)


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

    opcoes_unicas = list(
        dict.fromkeys(opcoes_variaveis)
    )

    if len(opcoes_unicas) == 1:

        variavel_info = variaveis[0]

    else:

        variavel_escolhida = st.selectbox(
            "Variável",
            opcoes_unicas
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

    valor_maximo = (
        df_plot["Valor"]
        .abs()
        .max()
    )

    unidade_original = (
        variavel_info.get(
            "unidade_detectada"
        )
    )

    fator_escala = 1

    unidade_final = unidade_original

    unidades_base = [
        "V",
        "W",
        "A",
        "var",
        "VA"
    ]

    if unidade_original in unidades_base:

        (
            _,
            unidade_final,
            fator_escala
        ) = auto_scale(
            valor_maximo,
            unidade_original
        )

        df_plot["Valor"] = (
            df_plot["Valor"]
            / fator_escala
        )

    tipo_variavel = variavel_info[
        "tipo"
    ]

    if unidade_final:

        label_grafico = (
            f"{tipo_variavel} "
            f"[{unidade_final}]"
        )

    else:

        label_grafico = tipo_variavel

    coluna_real = dados_plot[
        "coluna_real"
    ]   

    if len(opcoes_unicas) > 1:

        col_esquerda, col_direita = st.columns(2)

    else:

        col_esquerda = st.container()

    fig = px.line(
        df_plot,
        x="Tempo",
        y="Valor",
        title=coluna_real
    )

    if (
        variavel_info["tipo"] == "Tensão"
        and
        variavel_info.get(
            "unidade_detectada"
        ) == "pu"
    ):

        limites = obter_limites_prodist()

        tempo_min = df_plot[
            "Tempo"
        ].min()

        tempo_max = df_plot[
            "Tempo"
        ].max()

        fig.add_hline(

            y=limites["adequado_max"],

            line_dash="dash",

            line_color="red",

            annotation_text="Limite Sup. PRODIST"
        )

        fig.add_hline(

            y=limites["adequado_min"],

            line_dash="dash",

            line_color="orange",

            annotation_text="Limite Inf. PRODIST"
        )

    fig.update_layout(

        xaxis_title="Tempo",

        yaxis_title=label_grafico,

        hovermode="x unified"
    )

    with col_esquerda:

        st.subheader(
            "Série Temporal"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    if len(opcoes_unicas) > 1:

        df_multiserie = (
            preparar_multiplas_series(
                df,
                variaveis
            )
        )

        colunas_plot = [

            coluna

            for coluna in df_multiserie.columns

            if coluna != "Tempo"
        ]

        fig_multiserie = px.line(
            df_multiserie,
            x="Tempo",
            y=colunas_plot
        )

        if (
            variavel_info["tipo"] == "Tensão"
            and
            variavel_info.get(
                "unidade_detectada"
            ) == "pu"
        ):

            limites = obter_limites_prodist()

            fig_multiserie.add_hline(

                y=limites["adequado_max"],

                line_dash="dash",

                line_color="red",

                annotation_text="Limite Sup. PRODIST"
            )

            fig_multiserie.add_hline(

                y=limites["adequado_min"],

                line_dash="dash",

                line_color="orange",

                annotation_text="Limite Inf. PRODIST"
            )

        fig_multiserie.update_layout(

            title="Variáveis combinadas",

            xaxis_title="Tempo",

            yaxis_title=label_grafico,

            hovermode="x unified"
        )

        with col_direita:

            st.subheader(
                "Visualização conjunta"
            )

            st.plotly_chart(
                fig_multiserie,
                use_container_width=True
            )

    

    with st.expander(
        "Série selecionada"
    ):

        st.dataframe(

            df_plot.style.format({

                "Valor": "{:.16f}"

            })

        )

    with st.expander(
        "Base completa do dataset"
    ):

        st.dataframe(df)

    with st.expander(
        "Pré-visualização em código"
    ):

        st.json(variavel_info)
