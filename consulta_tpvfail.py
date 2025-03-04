import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
from sqlalchemy.engine import URL
from sqlalchemy import create_engine

# Configuração do Streamlit
st.set_page_config(page_title="Consulta de Falhas", layout="wide")

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

# Obter dados com SQLAlchemy
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

# Carregar dados
df = obter_dados()

# Interface do usuário
st.markdown("<h1 style='text-align: center;'>📋 Consulta de Falhas</h1>", unsafe_allow_html=True)

# Filtros
col1, col2, col3 = st.columns(3)
posicoes = df["position"].unique()
status_opcoes = df["status"].unique()

posicao_selecionada = col1.selectbox("🔍 Filtrar por posição:", ["Todas"] + list(posicoes))
status_selecionado = col2.selectbox("📌 Filtrar por status:", ["Todos"] + list(status_opcoes))
serial_number_input = col3.text_input("🔢 Buscar Serial Number:", "")

# Aplicar filtros
if posicao_selecionada != "Todas":
    df = df[df["position"] == posicao_selecionada]

if status_selecionado != "Todos":
    df = df[df["status"] == status_selecionado]

if serial_number_input:
    df = df[df["serial_number"].astype(str).str.contains(serial_number_input, case=False, na=False)]

# Paginação
items_per_page = 10
total_pages = max(1, (len(df) // items_per_page) + 1)
page = st.number_input("📄 Página:", min_value=1, max_value=total_pages, step=1)
df_paginated = df.iloc[(page - 1) * items_per_page : page * items_per_page]

# Exibir dados formatados
st.dataframe(df_paginated, use_container_width=True)

# Exportar CSV
st.download_button(
    label="📥 Baixar CSV",
    data=df.to_csv(index=False, sep=";"),
    file_name="falhas.csv",
    mime="text/csv"
)

# Classe PDF formatado
class PDF(FPDF):
    def header(self):
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
        col_widths = [15, 35, 35, 15, 35, 20, 35]  # Agora tem 7 colunas
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

# Função para gerar PDF
def gerar_pdf():
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.adicionar_tabela(df)

    file_path = "relatorio_falhas.pdf"
    pdf.output(file_path)
    return file_path

# Exportar PDF
if st.button("📄 Gerar Relatório PDF"):
    file_path = gerar_pdf()
    with open(file_path, "rb") as file:
        st.download_button(label="📥 Baixar PDF", data=file, file_name="relatorio_falhas.pdf", mime="application/pdf")
