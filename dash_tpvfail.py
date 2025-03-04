import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy.engine import URL
from sqlalchemy import create_engine

# Configuração do Streamlit
st.set_page_config(page_title="Dashboard de Falhas", layout="wide")

# Configuração do SQL Server
SERVER = "DESKTOP-8NF46OQ"
DATABASE = "TPV1"
USERNAME = "sa"
PASSWORD = "@123mudar"
TABLE_NAME = "logs_fail"

# Criar conexão usando SQLAlchemy. Precisa do ODBC configurando para Banco
connection_string = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};"
    f"UID={USERNAME};PWD={PASSWORD}"
)
connection_url = URL.create("mssql+pyodbc", query={"odbc_connect": connection_string})
engine = create_engine(connection_url)

# Conectar ao banco de dados e obter dados com cache
@st.cache_data
def obter_dados():
    query = f"""
        SELECT position, parametro, COUNT(*) AS falhas
        FROM {TABLE_NAME}
        GROUP BY position, parametro
        ORDER BY falhas DESC
    """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df

# Carregar dados
df = obter_dados()

# Interface do usuário
st.markdown(
    "<h1 style='text-align: center;'>🔧 Dashboard de Falhas por Posição</h1>", 
    unsafe_allow_html=True
)

# Filtro de posição no rack no menu lateral
with st.sidebar:
    st.header("Filtros")
    posicoes = df["position"].unique()
    posicao_selecionada = st.selectbox("Selecione a posição no Berço:", posicoes)

df_filtrado = df[df["position"] == posicao_selecionada].nlargest(10, "falhas")

# Criar gráficos
col1, col2 = st.columns(2)

fig_bar = px.bar(
    df_filtrado, x="parametro", y="falhas", text_auto=True,
    title=f"Top 10 Falhas - {posicao_selecionada}",
    labels={"parametro": "Parâmetro", "falhas": "Quantidade de Falhas"},
    color="falhas", height=500
)
fig_bar.update_layout(yaxis_title="Quantidade de Falhas", xaxis_title="Parâmetro", xaxis_tickangle=-45)
col1.plotly_chart(fig_bar, use_container_width=True)

fig_pie = px.pie(
    df_filtrado, names="parametro", values="falhas", title=f"Distribuição das Falhas - {posicao_selecionada}",
    color_discrete_sequence=px.colors.qualitative.Set3
)
col2.plotly_chart(fig_pie, use_container_width=True)
