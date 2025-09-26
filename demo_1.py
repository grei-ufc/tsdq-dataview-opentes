# Libraries
from haversine import haversine
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns
# biblioteca
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime,time
from PIL import Image
from plotly.subplots import make_subplots

#df = pd.read_csv('dataset_des1/results.csv')
#df1 = df.copy()

# dfx = pd.read_csv("dataset_des1/results.csv") # Carregar o arquivo CSV

# dfx.to_hdf("results_1.h5", key="dataset_to_sc1", mode="w", format="table") # Salvar no formato HDF5
# df = pd.read_hdf('results_1.h5', key='dataset_to_sc1')


def processar_dados():
    csv_path = "dataset_des1/results-demo1.csv"
    hdf5_path = "results_1.h5"
    
    try:
        # Tenta ler o CSV
        df = pd.read_csv(csv_path)
        print("CSV encontrado. Convertendo para HDF5...")
        
        # Salva como HDF5 (sobrescreve se existir)
        df.to_hdf(
            hdf5_path,
            key="dataset_to_sc1",
            mode="w",
            format="table"
        )
        
    except FileNotFoundError:
        print("CSV não encontrado. Lendo diretamente do HDF5...")
        try:
            # Tenta ler o HDF5 existente
            df = pd.read_hdf(hdf5_path, key="dataset_to_sc1")
        except Exception as e:
            print(f"Erro ao ler HDF5: {str(e)}")
            return None
            
    except Exception as e:
        print(f"Erro inesperado: {str(e)}")
        return None
        
    return df

# Uso
df = processar_dados()
if df is not None:
    print("Dados carregados com sucesso!")
else:
    print("Não foi possível carregar os dados.")
    
df1 = df.copy()


# #Convertendo date para Datetime
# df1[['Data','Hora']] = df1['date'].str.split(' ',expand=True)
# df1['Data'] = pd.to_datetime(df1['Data']).dt.strftime('%d-%m-%Y')
# df1['date'] = pd.to_datetime(df1['date'])

#============================================
#            BARRA LATERAL STREAMIT LIT
#===========================================
st.header('Mosaik')
st.header('Análise de dados para Cenário 1')

#image_path = 'imagens/Grei2.png'
image = Image.open( 'Grei2.png' )
st.sidebar.image(image, width=160)


#6st.sidebar.markdown('# Filtros')
st.sidebar.markdown("""---""")

# # Converter para datetime.datetime
# min_time = time(0, 0, 0)   # 04:00:00
# max_time = time(23, 59, 59) # 19:59:00

# # Slider apenas para horários
# start_time, end_time = st.sidebar.slider(
#     'Selecione um intervalo',
#     min_value=min_time,
#     max_value=max_time,
#     value=(min_time,max_time),  # Horário inicial
#     format="HH:mm:ss"
# )

# # Criando um datetime com a data fixa
# start_datetime = datetime(2021, 5, 21, start_time.hour, start_time.minute, start_time.second)
# end_datetime = datetime(2021, 5, 21, end_time.hour, end_time.minute, end_time.second)


# st.write("Horário start:", start_datetime)
# st.write("Horário end:", end_datetime)

# linha_selecionada = ((df1['date'] <= end_datetime) & (df1['date'] >= start_datetime ))
# df1= df1.loc[linha_selecionada,:]
#st.dataframe(df1)
mostrar_geracao = st.sidebar.checkbox('Exibir Geração Solar', value=True)
mostrar_tensao = st.sidebar.checkbox('Exibir Tensão Bus 3', value=True)
mostrar_control = st.sidebar.checkbox('Exibir Controlador', value=True)
# ============================================
#           LAYOUT STREAMLIT
#=============================================

tab1,tab2,tab3 = st.tabs(['Cenário 1','-','-'])
with tab1:
    with st.container():
        st.title("Informações relevantes")
        col1,col2 = st.columns(2, gap='small')
        with col1:
            col1.metric('Média Pot Bar 3(MW):','{:.3f}'.format(df1.loc[:,'Grid-0.0-Bus 3-p_mw'].mean()))
        with col2:
            col2.metric('Média Tensao Bar 3(p.u.):','{:.3f}'.format(df1.loc[:,'Grid-0.0-Bus 3-vm_pu'].mean()))
    with st.container():
        col3,col4,col5 = st.columns(3,gap='small')
        with col3:
            col3.metric('Média da Geração(MW):','{:.3f}'.format(df1.loc[:,'PV-0.PV_0-P_gen'].mean()))
        with col4:
            col4.metric('Média Controlador:','{:.3f}'.format(df1.loc[:,'PV-0.PV_0-mod'].mean()))  
        with col5:
            col5.metric('Média da Linha (%):','{:.3f}'.format(df1.loc[:,'Grid-0.0-Line-loading_percent'].mean()))
    with st.container():
                    
        df1["date"] = pd.to_datetime(df1["date"], format='mixed')
        
        fig = px.line(
            df1,
            x="date",
            y="PV-0.PV_0-P_gen",
            title="Geração Fotovoltaica ao Longo do Tempo",
            labels={"date": "Tempo", "PV-0.PV_0-P_gen": "Potência Gerada (MW)"},
        )
        
        fig.update_traces(line_color='orange', name='Geração PV (MW)')
        
        fig.update_layout(
            xaxis=dict(
                tickformat="%H:%M",
                tickangle=45
            ),
            yaxis_title="Potência Gerada (MW)",
            xaxis_title="Tempo",
            template="simple_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)


        

    with st.container():

        df1['date'] = pd.to_datetime(df1['date'], format='mixed')
        
        # Criar a figura com dois eixos y
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Plotar geração solar (eixo da esquerda)
        if mostrar_geracao:
            fig.add_trace(
                go.Scatter(
                    x=df1['date'],
                    y=df1['PV-0.PV_0-P_gen'],
                    name="Geração Solar (MW)",
                    line=dict(color="blue", width=2)
                ),
                secondary_y=False,
            )
        
        # Plotar tensão (eixo da direita)
        if mostrar_tensao:
            fig.add_trace(
                go.Scatter(
                    x=df1['date'],
                    y=df1['Grid-0.0-Bus 3-vm_pu'],
                    name="Tensão Bus 3 (pu)",
                    line=dict(color="red", width=2, dash='dot')
                ),
                secondary_y=True,
            )
        
        # Atualizar os títulos dos eixos
        fig.update_layout(
            title_text="Geração Fotovoltaica vs Tensão no Barramento 3",
            xaxis_title="Horário",
            template="simple_white"
        )
        
        fig.update_xaxes(
            tickformat="%H:%M",
            tickangle=45,
        )
        
        fig.update_yaxes(
            title_text="Geração Solar (MW)", 
            secondary_y=False, 
            color="blue"
        )
        
        fig.update_yaxes(
            title_text="Tensão Bus 3 (pu)", 
            secondary_y=True, 
            color="red"
        )
        
        # Mostrar no Streamlit
        st.plotly_chart(fig, use_container_width=True)



    with st.container():
        df1['data'] = pd.to_datetime(df1['date'])
        # Criando uma figura com 2 eixos
        fig = make_subplots(specs=[[{'secondary_y':True}]])

        # Plotando geração solar
        if mostrar_geracao:
            fig.add_trace(
                go.Scatter(
                    x=df1['date'],
                    y=df1['PV-0.PV_0-P_gen'],
                    name='Geração Solar (MW)',
                    line=dict(color='blue',width=2)
                ),
                secondary_y = False,
            )

        #Plotando controlador
        if mostrar_control:
            fig.add_trace(
                go.Scatter(
                    x=df1['date'],
                    y=df1['PV-0.PV_0-mod'],
                    name='Controlador',
                    line=dict(color='red',width=2, dash='dot')
                ),
                secondary_y = True,
            )

        # Atualizando o titulo dos eixos
        fig.update_layout(
            title_text = 'Geração solar vs Controlador',
            xaxis_title='Horário',
            template= 'simple_white'
        )

        fig.update_xaxes(
            tickformat="%H:%M",
            tickangle=45,
        )

        fig.update_yaxes(
            title_text="Geração Solar (MW)", 
            secondary_y=False, 
            color="blue"
        )
            
        fig.update_yaxes(
            title_text="Controlador", 
            secondary_y=True, 
            color="red"
        )
        st.plotly_chart(fig, use_container_width=True)

    with st.container():
                     
        df1["date"] = pd.to_datetime(df1["date"], format='mixed')
        
        fig = px.line(
            df1,
            x="date",
            y="Grid-0.0-Line-loading_percent",
            title="Percentual da linha ao longo do tempo",
            labels={"date": "Tempo", "Grid-0.0-Line-loading_percent": "Percentual da linha (%)"},
        )
        
        fig.update_traces(line_color='green', name='Percentual linha')
        
        fig.update_layout(
            xaxis=dict(
                tickformat="%H:%M",
                tickangle=45
            ),
            yaxis_title="Percentual da linha (%)",
            xaxis_title="Tempo",
            template="simple_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)

