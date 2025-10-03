import streamlit as st

# ========================
# TITULOS E TEXTOS
# ========================
st.title("Exemplo de Layout no Streamlit")
st.header("Demonstração de componentes de layout")
st.subheader("Subseção com texto formatado")
st.text("Texto simples")
st.markdown("Texto em **Markdown** com formatação")

# ========================
# SIDEBAR (MENU LATERAL)
# ========================
st.sidebar.title("Menu Lateral")
opcao = st.sidebar.selectbox("Escolha uma opção", ["Opção A", "Opção B", "Opção C"])
st.sidebar.write(f"Você escolheu: {opcao}")

# ========================
# CONTAINERS
# ========================
with st.container():
    st.write("Este é um container fixo")
    st.line_chart([1, 2, 3, 4, 5])  # Exemplo de gráfico dentro do container

# ========================
# EXPANSOR
# ========================
with st.expander("Clique para expandir"):
    st.write("Conteúdo oculto que aparece ao expandir")

# ========================
# COLUNAS
# ========================
st.write("Exemplo de colunas lado a lado")

col1, col2 = st.columns(2)

with col1:
    st.write("Coluna 1")
    st.button("Botão 1")

with col2:
    st.write("Coluna 2")
    st.button("Botão 2")

# Colunas com tamanhos diferentes
st.write("Colunas com larguras diferentes")
col1, col2, col3 = st.columns([3, 1, 2])

with col1:
    st.write("Coluna mais larga (3x)")
with col2:
    st.write("Coluna estreita (1x)")
with col3:
    st.write("Coluna média (2x)")

# ========================
# TABS (ABAS)
# ========================
tab1, tab2 = st.tabs(["Página 1", "Página 2"])

with tab1:
    st.write("Conteúdo da aba 1")
    st.area_chart([1, 2, 3, 4])

with tab2:
    st.write("Conteúdo da aba 2")
    st.bar_chart([3, 1, 2, 4])

# ========================
# CSS CUSTOMIZADO
# ========================
st.markdown(
    """
    <style>
    .big-font {
        font-size:30px !important;
        color: blue;
    }
    </style>
    """, unsafe_allow_html=True
)

st.markdown('<p class="big-font">Texto customizado com CSS</p>', unsafe_allow_html=True)
