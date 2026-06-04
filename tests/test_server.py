import pytest
import os
import pandas as pd
from server import query_large_dataset, navigate_and_extract_text, BrowserContext

@pytest.fixture
def mock_csv(tmp_path):
    """Cria um CSV temporário com 10.000 linhas para teste."""
    filepath = tmp_path / "test_dataset.csv"
    df = pd.DataFrame({
        'id': range(10000),
        'category': ['A', 'B'] * 5000,
        'value': range(10000)
    })
    df.to_csv(filepath, index=False)
    return str(filepath)

@pytest.mark.asyncio
async def test_query_large_dataset_success(mock_csv):
    """Testa se o DuckDB conta linhas corretamente em background."""
    query = f"SELECT COUNT(*) as total FROM '{mock_csv}'"
    result = await query_large_dataset(filepath=mock_csv, sql_query=query)
    
    assert "10000" in result
    assert "ERRO" not in result

@pytest.mark.asyncio
async def test_query_large_dataset_security_validation():
    """Testa se o Pydantic bloqueia extensões inválidas (.txt)."""
    result = await query_large_dataset(filepath="C:/windows/system32/senha.txt", sql_query="SELECT * FROM foo")
    assert "ERRO DE SEGURANÇA" in result
    assert "Formato perigoso" in result

@pytest.mark.asyncio
async def test_navigate_playwright_success():
    """Testa a extração de texto em um site ultraleve (example.com)."""
    result = await navigate_and_extract_text(url="https://example.com", selector="h1")
    assert "Example Domain" in result
    
    # Limpa o Singleton do Browser para não deixar processo pendurado no teste
    await BrowserContext.cleanup()
