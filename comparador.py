import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import re

st.set_page_config(layout="wide", page_title="Comparador de Simulações")

st.title("⚖️ Tira-Teima: Comparador de Simulações")
st.markdown("Verifique se os resultados da Barra 800 são idênticos nos dois arquivos.")

c1, c2 = st.columns(2)
with c1:
    file1 = st.file_uploader("📂 Arquivo 1 (Original)", type=["csv"], key="f1")
with c2:
    file2 = st.file_uploader("📂 Arquivo 2 (Com Monitores)", type=["csv"], key="f2")

if file1 and file2:
    # Ler arquivos
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)
    
    # Limpar nomes
    df1.columns = df1.columns.str.strip()
    df2.columns = df2.columns.str.strip()
    
    st.write("---")
    
    # Encontrar colunas comuns que tenham "800" e "pu"
    cols1 = set(df1.columns)
    cols2 = set(df2.columns)
    
    # Interseção: colunas que existem nos DOIS arquivos
    comuns = list(cols1.intersection(cols2))
    comuns_800 = sorted([c for c in comuns if "800" in c and "pu" in c])
    
    if not comuns_800:
        st.error("❌ Não encontrei colunas com o mesmo nome exato para a Barra 800 nos dois arquivos.")
        st.write("Colunas Arquivo 1:", [c for c in df1.columns if "800" in c])
        st.write("Colunas Arquivo 2:", [c for c in df2.columns if "800" in c])
    else:
        st.success(f"✅ Encontrei {len(comuns_800)} colunas comparáveis para a Barra 800.")
        
        col_selecionada = st.selectbox("Qual coluna comparar?", comuns_800)
        
        # Cria DataFrame de Comparação
        # Assume que os arquivos têm o mesmo tamanho. Se não tiverem, corta pelo menor.
        min_len = min(len(df1), len(df2))
        
        comp = pd.DataFrame()
        comp['Arq1'] = df1[col_selecionada].iloc[:min_len]
        comp['Arq2'] = df2[col_selecionada].iloc[:min_len]
        comp['Diferenca'] = comp['Arq1'] - comp['Arq2']
        
        # Estatísticas da diferença
        max_diff = comp['Diferenca'].abs().max()
        media_diff = comp['Diferenca'].abs().mean()
        
        col_metric1, col_metric2 = st.columns(2)
        col_metric1.metric("Diferença Máxima", f"{max_diff:.8f} pu")
        col_metric2.metric("São Idênticos?", "SIM" if max_diff < 1e-6 else "NÃO")
        
        # Gráfico
        fig = go.Figure()
        
        # Se forem diferentes, mostra as duas linhas. Se forem iguais, mostra só a diferença.
        if max_diff > 1e-6:
            st.warning("⚠️ Há diferenças nos valores!")
            fig.add_trace(go.Scatter(y=comp['Arq1'], name="Arquivo 1 (Original)", line=dict(color='blue')))
            fig.add_trace(go.Scatter(y=comp['Arq2'], name="Arquivo 2 (Monitores)", line=dict(color='red', dash='dot')))
        else:
            st.success("✨ Os gráficos estão perfeitamente sobrepostos (Diferença zero).")
            fig.add_trace(go.Scatter(y=comp['Diferenca'], name="Diferença (Erro)", line=dict(color='green')))
            fig.update_layout(yaxis_title="Erro (pu)", title="Gráfico de Diferença (Deve ser uma linha reta no zero)")

        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander("Ver dados lado a lado"):
            st.dataframe(comp)