from server import query_large_dataset
import asyncio
import time

filepath = r"C:\Users\Migra Tech\Desktop\code\Book(Planilha1).csv"
sql_query = f"SELECT COUNT(*) as total_linhas FROM '{filepath}'"

print("Chamando a função diretamente...")
start = time.time()
res = query_large_dataset(filepath, sql_query)
print(f"Resultado:\n{res}")
print(f"Tempo: {time.time() - start}s")
