import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
from datetime import datetime
from sqlalchemy.engine import URL
from sqlalchemy import create_engine

# Configuração do Streamlit
st.set_page_config(page_title="📊 Dashboard de Falhas", layout="wide")

# Configuração do SQL Server
SERVER = "DESKTOP-8NF46OQ"
DATABASE = "TPV1"
USERNAME = "sa"
PASSWORD = "@123mudar"
TABLE_NAME = "logs_fail"

# Criar conexão SQLAlchemy
connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}"
connection_url = URL.create("mssql+pyodbc", query={"odbc_connect": connection_string})
engine = create_engine(connection_url)

# Obter dados do banco
@st.cache_data
def obter_dados():
    query = f"""
        SELECT serial_number, position, data_hora, status, parametro, type, computer_name
        FROM {TABLE_NAME}
        ORDER BY data_hora DESC
    """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df

df = obter_dados()

# Interface principal
st.markdown("""
    <h1 style='text-align: center;'>📊 Dashboard de Falhas</h1>
""", unsafe_allow_html=True)

# Filtros no sidebar
with st.sidebar:
    st.header("🔍 Filtros de Consulta")
    posicoes = df["position"].unique()
    status_opcoes = df["status"].unique()

    posicao_selecionada = st.selectbox("📍 Filtrar por posição:", ["Todas"] + list(posicoes))
    status_selecionado = st.selectbox("📌 Filtrar por status:", ["Todos"] + list(status_opcoes))
    serial_number_input = st.text_input("🔢 Buscar Serial Number:", "")
    computer_name_input = st.text_input("💻 Buscar Nome do Computador:", "")

    # Conversão para datetime
    df["data_hora"] = pd.to_datetime(df["data_hora"])  

    # Valores mínimo e máximo da data
    data_min = df["data_hora"].min().date()
    data_max = df["data_hora"].max().date()

    # Entrada de data no sidebar
    data_selecionada = st.date_input("📅 Selecionar intervalo de datas:", [data_min, data_max])

# Tratamento da seleção de data
if len(data_selecionada) == 2:
    data_inicial, data_final = data_selecionada
else:
    data_inicial, data_final = data_min, data_max

# Aplicar filtros
df_filtrado = df.copy()
if posicao_selecionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado["position"] == posicao_selecionada]
if status_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["status"] == status_selecionado]
if serial_number_input:
    df_filtrado = df_filtrado[df_filtrado["serial_number"].astype(str).str.contains(serial_number_input, case=False, na=False)]
if computer_name_input:
    df_filtrado = df_filtrado[df_filtrado["computer_name"].astype(str).str.contains(computer_name_input, case=False, na=False)]
if data_inicial and data_final:
    df_filtrado = df_filtrado[(df_filtrado["data_hora"].dt.date >= data_inicial) & (df_filtrado["data_hora"].dt.date <= data_final)]

# Criar gráficos
st.markdown("### 📊 Análise de Falhas")
col1, col2 = st.columns(2)

df_top_falhas = df_filtrado.groupby("parametro")["serial_number"].count().reset_index()
df_top_falhas.columns = ["parametro", "falhas"]
df_top_falhas = df_top_falhas.nlargest(10, "falhas")

fig_bar = px.bar(df_top_falhas, x="parametro", y="falhas", text_auto=True, 
    title="Top 10 Parâmetros com Mais Falhas", labels={"parametro": "Parâmetro", "falhas": "Quantidade"},
    color="falhas", height=500)
fig_bar.update_layout(yaxis_title="Quantidade de Falhas", xaxis_title="Parâmetro", xaxis_tickangle=-45)
col1.plotly_chart(fig_bar, use_container_width=True)

fig_pie = px.pie(df_top_falhas, names="parametro", values="falhas", 
    title="Distribuição das Falhas", color_discrete_sequence=px.colors.qualitative.Set3)
col2.plotly_chart(fig_pie, use_container_width=True)

# Exibir tabela com paginação
st.markdown("### 📋 Dados Detalhados")
items_per_page = 10
total_pages = max(1, (len(df_filtrado) // items_per_page) + 1)
page = st.number_input("📄 Página:", min_value=1, max_value=total_pages, step=1)
df_paginated = df_filtrado.iloc[(page - 1) * items_per_page : page * items_per_page]
st.dataframe(df_paginated, use_container_width=True)

# Botão de Exportação CSV
st.download_button(
    label="📥 Baixar CSV",
    data=df_filtrado.to_csv(index=False, sep=";"),
    file_name="falhas.csv",
    mime="text/csv"
)

# Classe PDF formatado com logomarca
class PDF(FPDF):
    def __init__(self, logo_path=None):
        super().__init__()
        self.logo_path = logo_path  # Caminho para a logomarca

    def header(self):
        # Adicionar logomarca
        if self.logo_path:
            self.image(self.logo_path, x=10, y=8, w=33)  # Ajuste x, y, w conforme necessário
        
        # Título e data de geração
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "Relatório de Falhas", ln=True, align="C")
        self.set_font("Arial", "", 10)
        self.cell(0, 10, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")

    def adicionar_tabela(self, df):
        col_widths = [15, 35, 35, 15, 35, 20, 35]  # Largura das colunas
        headers = ["Estação", "SN", "Máquina", "Berço", "Data", "Resultado", "Parâmetros"]

        self.set_fill_color(200, 200, 200)
        self.set_font("Arial", "B", 10)

        for i, header in enumerate(headers):
            self.cell(col_widths[i], 8, header, border=1, align="C", fill=True)
        self.ln()

        self.set_font("Arial", "", 9)
        for _, row in df.iterrows():
            self.cell(col_widths[0], 8, str(row["type"]), border=1, align="C")
            self.cell(col_widths[1], 8, str(row["serial_number"]), border=1, align="C")
            self.cell(col_widths[2], 8, str(row["computer_name"]), border=1, align="C")
            self.cell(col_widths[3], 8, str(row["position"]), border=1, align="C")
            self.cell(col_widths[4], 8, str(row["data_hora"]), border=1, align="C")
            self.cell(col_widths[5], 8, str(row["status"]), border=1, align="C")
            self.cell(col_widths[6], 8, str(row["parametro"]), border=1, align="C")
            self.ln()

# Função para gerar PDF com base nos filtros aplicados e logomarca
def gerar_pdf(df_filtrado, logo_path=None):
    pdf = PDF(logo_path=logo_path)  # Passar o caminho da logomarca
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.adicionar_tabela(df_filtrado)  # Usar o DataFrame filtrado

    file_path = "relatorio_falhas.pdf"
    pdf.output(file_path)
    return file_path

# Botão para gerar e baixar o PDF
if st.button("📄 Gerar Relatório PDF"):
    # Caminho para a logomarca (ajuste conforme necessário)
    logo_path = "tpv.png"  # Substitua pelo caminho correto da sua imagem
    file_path = gerar_pdf(df_filtrado, logo_path=logo_path)  # Passar o DataFrame filtrado e o caminho da logomarca
    with open(file_path, "rb") as file:
        st.download_button(
            label="📥 Baixar PDF",
            data=file,
            file_name="relatorio_falhas.pdf",
            mime="application/pdf"
        )
