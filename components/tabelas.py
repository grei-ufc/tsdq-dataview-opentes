import streamlit as st


def render_tabela_serie(
    df_plot
):
    """
    Renderiza série temporal.
    """

    with st.expander(
        "Série selecionada"
    ):

        st.dataframe(

            df_plot.style.format({

                "Valor": "{:.16f}"

            }),

            use_container_width=True
        )


def render_tabela_dataset(
    df
):
    """
    Renderiza dataset completo.
    """

    with st.expander(
        "Base completa do dataset"
    ):

        st.dataframe(
            df,
            use_container_width=True
        )


def render_codigo_variavel(
    variavel_info
):
    """
    Renderiza estrutura semântica.
    """

    with st.expander(
        "Pré-visualização em código"
    ):

        st.json(
            variavel_info
        )