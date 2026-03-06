import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- 1. CONFIGURAÇÃO (1ª LINHA) ---
st.set_page_config(layout="wide", page_title="Comparador Universal")

st.title("🕵️ Comparador Universal OpenDSS")
st.markdown("Compare qualquer barra entre os dois arquivos.")

# --- 2. UPLOAD ---
c1, c2 = st.columns(2)
with c1:
    file1 = st.file_uploader("📂 Arquivo 1 (Original do Luís)", type=["csv"], key="f1")
with c2:
    file2 = st.file_uploader("📂 Arquivo 2 (Monitores)", type=["csv"], key="f2")

if file1 and file2:
    try:
        # Leitura
        df1 = pd.read_csv(file1)
        df2 = pd.read_csv(file2)
        
        # Limpeza
        df1.columns = df1.columns.str.strip()
        df2.columns = df2.columns.str.strip()
        
        st.write("---")
        
        # --- 3. FILTRO DE BARRA ---
        col_filtro, col_vazio = st.columns([1, 2])
        with col_filtro:
            st.info("Passo 1: Escolha a Barra")
            # O valor padrão é vazio para mostrar tudo, ou você pode por "840"
            filtro_barra = st.text_input("Digite o número da barra para filtrar:", value="")
            
        # Filtra as colunas baseadas no que você digitou
        # Se deixar vazio, mostra todas as colunas que tem "pu"
        cols1 = sorted([c for c in df1.columns if filtro_barra in c and "pu" in c])
        cols2 = sorted([c for c in df2.columns if filtro_barra in c and "pu" in c])
        
        if not cols1:
            st.warning(f"⚠️ Nenhuma coluna com '{filtro_barra}' encontrada no Arquivo 1.")
        if not cols2:
            st.warning(f"⚠️ Nenhuma coluna com '{filtro_barra}' encontrada no Arquivo 2.")

        if cols1 and cols2:
            # --- 4. SELEÇÃO DAS COLUNAS ---
            st.write("---")
            st.info("Passo 2: Selecione as Fases para cruzar")
            
            sel_c1, sel_c2 = st.columns(2)
            
            with sel_c1:
                coluna_a = st.selectbox("Coluna do Arq 1:", cols1)
                
            with sel_c2:
                # Tenta achar o match automático pelo nome
                idx_padrao = 0
                if coluna_a in cols2:
                    idx_padrao = cols2.index(coluna_a)
                coluna_b = st.selectbox("Coluna do Arq 2:", cols2, index=idx_padrao)

           # --- 5. CÁLCULOS E VISUALIZAÇÃO PONTUAL ---
            min_len = min(len(df1), len(df2))
            val_a = df1[coluna_a].iloc[:min_len]
            val_b = df2[coluna_b].iloc[:min_len]
            
            diff = val_a - val_b
            max_diff = diff.abs().max()
            idx_max_diff = diff.abs().idxmax() # Acha a linha onde o erro é maior
            
            # --- SELETOR DE TEMPO ---
            st.write("---")
            st.markdown("#### ⏱️ Navegar no Tempo")
            
            # Botão para pular para o pior caso
            if st.button(f"Pular para Maior Diferença (Linha {idx_max_diff})"):
                step_inicial = int(idx_max_diff)
            else:
                step_inicial = 0
            
            # Slider para escolher a linha
            step = st.slider("Escolha a Linha (Passo de Tempo):", 
                             min_value=0, max_value=min_len-1, value=step_inicial)

            # Pega o valor EXATO daquela linha
            v1_atual = val_a.iloc[step]
            v2_atual = val_b.iloc[step]
            diff_atual = v1_atual - v2_atual

            # Métricas
            m1, m2, m3 = st.columns(3)
            m1.metric(f"Valor Arq 1 (Linha {step})", f"{v1_atual:.5f}")
            m2.metric(f"Valor Arq 2 (Linha {step})", f"{v2_atual:.5f}")
            
            tolerancia = st.select_slider("Tolerância", options=[1e-6, 1e-4, 0.01], value=1e-4)
            
            if abs(diff_atual) <= tolerancia:
                m3.metric("Diferença", "IGUAIS ✅", delta=f"{diff_atual:.5f}", delta_color="off")
            else:
                m3.metric("Diferença", "DIFERENTES ❌", delta=f"{diff_atual:.5f}", delta_color="inverse")

            # --- 6. GRÁFICO ---
            fig = go.Figure()
            fig.add_trace(go.Scatter(y=val_a, name=f"Arquivo Luís ({coluna_a})", line=dict(color='blue', width=2)))
            fig.add_trace(go.Scatter(y=val_b, name=f"Arquivo com mais monitores ({coluna_b})", line=dict(color='red', width=1, dash='dot')))
            fig.update_layout(title=f"Comparação Visual: {filtro_barra}", height=450, hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.error(f"Erro: {e}")