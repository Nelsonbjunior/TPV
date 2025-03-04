# 📊 TPV - Dashboard de Falhas

Bem-vindo ao **TPV**! Este projeto é um **Dashboard de Falhas** desenvolvido em **Streamlit** com integração ao **SQL Server**. Ele permite a análise e visualização de falhas de produção, oferecendo gráficos interativos, filtros dinâmicos e exportação de relatórios.

## 🚀 Funcionalidades
- 📌 **Visualização de Dados**: Listagem detalhada das falhas registradas.
- 📊 **Gráficos Interativos**: Relatórios visuais com **Plotly**.
- 🔍 **Filtros Avançados**: Filtragem por data, posição, status, número de série e computador.
- 📥 **Exportação de Dados**: Download dos registros em **CSV** e **PDF**.
- 🖥 **Interface Amigável**: Desenvolvida com **Streamlit** para fácil navegação.

---

## 🛠 Tecnologias Utilizadas
- **Python** (Streamlit, Pandas, SQLAlchemy, Plotly, FPDF)
- **SQL Server** (Banco de dados para armazenar logs de falhas)
- **Git/GitHub** (Controle de versão)

---

## 📦 Requisitos
Certifique-se de ter instalado:
- **Python 3.8+**
- **SQL Server**
- **ODBC Driver 17 for SQL Server**
- **Bibliotecas Python** (instale com o comando abaixo)

```sh
pip install streamlit pandas sqlalchemy pyodbc plotly fpdf
```

---

## ⚙️ Configuração e Execução
### 🔧 1. Configurar Conexão com Banco de Dados
No arquivo principal, edite as credenciais para o seu banco SQL Server:
```python
SERVER = "SEU_SERVIDOR"
DATABASE = "SUA_BASE"
USERNAME = "SEU_USUARIO"
PASSWORD = "SUA_SENHA"
```

### ▶️ 2. Executar o Projeto
Após configurar, rode o seguinte comando no terminal:
```sh
streamlit run app.py
```

---

## 📝 Como Contribuir
1. **Clone o repositório**:
   ```sh
   git clone https://github.com/Nelsonbjunior/tpv.git
   ```
2. **Crie uma branch para sua feature**:
   ```sh
   git checkout -b minha-feature
   ```
3. **Faça as alterações e commit**:
   ```sh
   git commit -m "Adicionando nova funcionalidade X"
   ```
4. **Envie para o repositório**:
   ```sh
   git push origin minha-feature
   ```
5. **Crie um Pull Request no GitHub**.

---

## 📄 Licença
Este projeto está sob a **Licença MIT** - veja o arquivo [LICENSE](LICENSE) para mais detalhes.

💡 *Se gostou do projeto, não esqueça de dar uma ⭐ no repositório!* 🚀

