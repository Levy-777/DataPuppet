import duckdb
import sys
import time

print("Iniciando teste...")
start = time.time()
query = "SELECT COUNT(*) as Total_Linhas FROM 'C:\\Users\\Migra Tech\\Desktop\\code\\Book(Planilha1).csv'"
try:
    conn = duckdb.connect(':memory:')
    print("Conectado. Executando query...")
    res = conn.execute(query).df()
    print("Resultado:")
    print(res)
except Exception as e:
    print(f"Erro: {e}")

print(f"Tempo total: {time.time() - start} segundos")
