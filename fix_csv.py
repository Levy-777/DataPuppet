import duckdb

def fix_csv():
    # Caminhos
    input_file = r"C:\Users\Migra Tech\Desktop\code\Book(Planilha1).csv"
    output_file = r"C:\Users\Migra Tech\Desktop\code\Planilha_Corrigida.csv"
    
    # Query SQL monstruosa rodando via DuckDB
    query = f"""
    COPY (
        SELECT * FROM '{input_file}'
    ) TO '{output_file}' (HEADER, DELIMITER ';');
    """
    
    print("Iniciando correção do CSV com DuckDB...")
    try:
        conn = duckdb.connect(':memory:')
        conn.execute(query)
        print("Correção concluída! Arquivo salvo como Planilha_Corrigida.csv")
    except Exception as e:
        print(f"Erro ao processar: {e}")

if __name__ == "__main__":
    fix_csv()
