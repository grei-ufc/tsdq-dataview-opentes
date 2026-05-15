import streamlit as st


def render_upload(
    session_key,
    label="Carregue um arquivo",
    file_types=None
):
    """
    Renderiza uploader persistente.
    """

    if file_types is None:
        file_types = ["csv"]

    if session_key not in st.session_state:

        st.session_state[session_key] = None

    if st.session_state[session_key] is None:

        uploaded_file = st.file_uploader(
            label,
            type=file_types
        )

        if uploaded_file is not None:

            st.session_state[
                session_key
            ] = uploaded_file

            st.rerun()

    else:

        uploaded_file = st.session_state[
            session_key
        ]

        st.caption(
            f"Arquivo carregado: "
            f"{uploaded_file.name}"
        )

        if st.button(
            "Carregar novo arquivo"
        ):

            st.session_state[
                session_key
            ] = None

            st.rerun()

    return st.session_state[
        session_key
    ]