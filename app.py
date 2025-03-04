import os
import shutil
import pyodbc
import datetime
import re
import queue
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from concurrent.futures import ThreadPoolExecutor

# Configuração do SQL Server
SERVER = "DESKTOP-8NF46OQ"
DATABASE = "TPV1"
USERNAME = "sa"
PASSWORD = "@123mudar"
TABLE_NAME = "logs_fail"
DIRETORIO_LOGS = "D:/Logs"

# Fila de processamento de arquivos
log_queue = queue.Queue()
executor = ThreadPoolExecutor(max_workers=4)  # Controla o paralelismo

# Conectar ao banco de dados (sessão única por thread). Utilizar ODBC
def conectar_banco():
    conn_str = f"DRIVER={{SQL Server}};SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}"
    return pyodbc.connect(conn_str, autocommit=True)  # Autocommit evita locks

# Criar tabela se não existir
def criar_tabela():
    with conectar_banco() as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='{TABLE_NAME}' AND xtype='U')
                CREATE TABLE {TABLE_NAME} (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    serial_number VARCHAR(50),
                    data_hora DATETIME,
                    position VARCHAR(10),
                    parametro VARCHAR(50),
                    valor VARCHAR(50),
                    min_max VARCHAR(50),
                    status VARCHAR(10),
                    type VARCHAR(20),
                    computer_name VARCHAR(50)
                )
            """)

# Processar um único arquivo de log
def processar_log(arquivo):
    criar_tabela()
    backup_dir = os.path.join(DIRETORIO_LOGS, "Backup", datetime.datetime.now().strftime("%Y-%m-%d"))
    os.makedirs(backup_dir, exist_ok=True)

    try:
        with open(arquivo, "r", encoding="utf-8") as f:
            linhas = f.readlines()

        dados = {}
        falhas = []

        for linha in linhas:
            partes = linha.strip().split("|")
            if len(partes) == 2:
                chave, valor = partes
                dados[chave] = valor

                # Capturar o último número dentro dos parênteses
                match = re.search(r'\((?:[^,]*,)*([^,)]+)\)$', valor)
                if match:
                    ultimo_numero = match.group(1).strip()
                    if ultimo_numero == "0":  # Detectar falha
                        parametro = chave
                        valores = valor.strip("()").split(",")
                        falhas.append((parametro, valores[0], valores[1], "FAIL"))

        # Capturar informações extras
        serial_number = dados.get("SN", "N/A")
        data_hora = dados.get("Data_And_Time", "N/A")
        position = dados.get("Position_in_Rack", "N/A")
        type_ = dados.get("Type", "N/A")
        computer_name = dados.get("Computer_name", "N/A")

        if falhas:
            with conectar_banco() as conn:
                with conn.cursor() as cursor:
                    cursor.executemany(f"""
                        INSERT INTO {TABLE_NAME} (serial_number, data_hora, position, parametro, valor, min_max, status, type, computer_name)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, [(serial_number, data_hora, position, p, v, m, s, type_, computer_name) for p, v, m, s in falhas])

        # Mover para backup
        shutil.move(arquivo, os.path.join(backup_dir, os.path.basename(arquivo)))
        print(f"[✔] {arquivo} processado e movido para backup.")

    except Exception as e:
        print(f"[⚠] Erro ao processar {arquivo}: {e}")

# Classe para monitoramento da pasta
class LogHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".txt"):
            log_queue.put(event.src_path)  # Adiciona à fila para processamento

# Consumidor da fila (processa arquivos em paralelo)
def consumir_fila():
    while True:
        arquivo = log_queue.get()
        executor.submit(processar_log, arquivo)  # Executa em paralelo
        log_queue.task_done()

# Iniciar o monitoramento
def monitorar_diretorio():
    observer = Observer()
    handler = LogHandler()
    observer.schedule(handler, path=DIRETORIO_LOGS, recursive=False)
    observer.start()
    print(f"📡 Monitorando a pasta: {DIRETORIO_LOGS}...")

    thread_fila = threading.Thread(target=consumir_fila, daemon=True)
    thread_fila.start()  # Inicia o consumidor da fila

    try:
        while True:
            pass  # Mantém o programa rodando
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# Iniciar a monitoração
if __name__ == "__main__":
    monitorar_diretorio()
