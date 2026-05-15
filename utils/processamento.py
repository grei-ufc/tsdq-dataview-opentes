import pandas as pd


def organizar_variaveis(colunas_mapeadas):
    """
    Organiza variáveis por tipo e elemento.
    """

    estrutura = {}

    for coluna, info in colunas_mapeadas.items():

        tipo = info["tipo"]

        elemento = info["elemento"]

        if tipo not in estrutura:
            estrutura[tipo] = {}

        if elemento not in estrutura[tipo]:
            estrutura[tipo][elemento] = []

        estrutura[tipo][elemento].append(info)

    return estrutura


def preparar_serie_temporal(
    df,
    variavel_info
):
    """
    Prepara série temporal para visualização.
    """

    coluna_real = variavel_info[
        "coluna_original"
    ]

    df_plot = df[
        [
            "Tempo_EixoX",
            coluna_real
        ]
    ].copy()

    df_plot.columns = [
        "Tempo",
        "Valor"
    ]

    tipo = variavel_info["tipo"]

    unidade = variavel_info.get(
        "unidade_detectada"
    )

    label_y = tipo

    if unidade:
        label_y += f" [{unidade}]"

    return {

        "df_plot": df_plot,

        "label_y": label_y,

        "coluna_real": coluna_real
    }