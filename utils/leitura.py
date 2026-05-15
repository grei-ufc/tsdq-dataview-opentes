import pandas as pd


def ler_csv(uploaded_file):
    """
    Lê um CSV e normaliza as colunas.
    """

    try:
        df = pd.read_csv(uploaded_file)

    except UnicodeDecodeError:
        df = pd.read_csv(
            uploaded_file,
            encoding="latin1"
        )

    df.columns = (
        df.columns
        .str.strip()
    )

    return df


def processar_tempo(df):
    """
    Cria eixo temporal padronizado.
    """

    primeira_coluna = df.columns[0]

    tempo = pd.to_datetime(
        df[primeira_coluna]
        .astype(str)
        .str.strip(),
        format="mixed",
        errors="coerce"
    )

    if tempo.isna().all():

        df["Tempo_EixoX"] = range(len(df))

    else:

        df["Tempo_EixoX"] = tempo

    return df