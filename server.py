import os
import sys
import asyncio
import logging
import tempfile
import subprocess
import warnings
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator

# ==============================================================================
# PILAR 2: Sistema de Logging Real
# ==============================================================================
# Suprime warnings do OS/Python
warnings.filterwarnings("ignore")

# Configura logger em arquivo isolado (nunca polui o stdout que o MCP usa)
log_file = os.path.join(os.path.dirname(__file__), 'data-puppet.log')
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DataPuppet")
logger.info("Servidor MCP Data-Puppet inicializado.")

# ==============================================================================
# PILAR 4: Gerenciamento do Ciclo de Vida do Playwright
# ==============================================================================
class BrowserContext:
    _playwright = None
    _browser = None

    @classmethod
    async def get_browser(cls):
        if cls._browser is None:
            logger.info("Iniciando Playwright Headless (Cold Start)...")
            from playwright.async_api import async_playwright
            cls._playwright = await async_playwright().start()
            # Mantemos o navegador aquecido em background
            cls._browser = await cls._playwright.chromium.launch(headless=True)
            logger.info("Browser inicializado e aquecido com sucesso.")
        return cls._browser

    @classmethod
    async def cleanup(cls):
        if cls._browser:
            await cls._browser.close()
            cls._browser = None
        if cls._playwright:
            await cls._playwright.stop()
            cls._playwright = None
            logger.info("Playwright e Browser encerrados com sucesso.")

mcp = FastMCP("DataPuppet")

# ==============================================================================
# PILAR 3: Validação Estrita de Inputs (Pydantic)
# ==============================================================================
class DatasetArgs(BaseModel):
    filepath: str = Field(..., description="Caminho absoluto do arquivo")
    sql_query: str = Field(..., description="Query SQL válida")

    @field_validator('filepath')
    def validate_extension(cls, v):
        valid_exts = ('.csv', '.tsv', '.parquet')
        if not v.lower().endswith(valid_exts):
            raise ValueError(f"Formato perigoso ou inválido. Permitidos: {valid_exts}")
        if not os.path.exists(v):
            raise ValueError(f"O arquivo não existe no disco local: {v}")
        return v

class PlaywrightArgs(BaseModel):
    url: str = Field(..., description="URL para navegar")
    selector: str = Field("body", description="Seletor CSS para extrair texto")

    @field_validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL inválida. Deve iniciar com http ou https.")
        return v


@mcp.tool()
async def query_large_dataset(filepath: str, sql_query: str) -> str:
    """Executa consultas SQL via DuckDB em arquivos massivos (Subprocess Isolation)."""
    # Validação de Segurança
    try:
        DatasetArgs(filepath=filepath, sql_query=sql_query)
    except Exception as e:
        logger.warning(f"Tentativa de injeção ou input inválido bloqueada: {e}")
        return f"ERRO DE SEGURANÇA/VALIDAÇÃO:\n{e}"

    logger.info(f"Executando query no arquivo: {filepath}")
    
    # Sanitização extra de caminhos para o Windows/DuckDB
    safe_filepath = filepath.replace("\\", "/")
    safe_query = sql_query.replace("\\", "/")

    script_code = f"""import duckdb
import warnings
warnings.filterwarnings('ignore')
try:
    with duckdb.connect(':memory:') as conn:
        conn.execute("PRAGMA threads=1")
        conn.execute("PRAGMA enable_progress_bar=false")
        res = conn.execute(\"\"\"{safe_query}\"\"\").fetchdf()
        print("===OK===")
        print(res.to_string(max_rows=100))
except Exception as e:
    print("===ERRO===")
    print(str(e))
"""

    def _run_with_timeout():
        fd, script_path = tempfile.mkstemp(suffix=".py")
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(script_code)
            
            process = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=30,
                stdin=subprocess.DEVNULL 
            )
            
            stdout = process.stdout
            if "===OK===" in stdout:
                logger.info("Query executada com sucesso no subprocesso isolado.")
                return stdout.split("===OK===")[1].strip()
            elif "===ERRO===" in stdout:
                logger.error(f"Erro SQL no subprocesso: {stdout}")
                return f"Erro SQL:\n{stdout.split('===ERRO===')[1].strip()}"
            else:
                logger.error(f"Falha bizarra no DuckDB. Stdout: {stdout}")
                return f"Falha de execução do DuckDB. Detalhes no log interno."
                
        except subprocess.TimeoutExpired:
            logger.error("TIMEOUT! Processo DuckDB foi assassinado após 30s.")
            return "ERRO DE TIMEOUT: A query estourou 30s e foi abortada."
        except Exception as e:
            logger.error(f"Erro de infraestrutura do subprocesso: {e}")
            return f"Erro interno do servidor: {str(e)}"
        finally:
            try:
                os.remove(script_path)
            except:
                pass

    try:
        return await asyncio.to_thread(_run_with_timeout)
    except Exception as e:
        return f"Erro fatal de concorrência: {e}"


@mcp.tool()
async def navigate_and_extract_text(url: str, selector: str = "body") -> str:
    """Acessa URL via Playwright com Browser Singleton Aquecido."""
    try:
        PlaywrightArgs(url=url, selector=selector)
    except Exception as e:
        logger.warning(f"URL inválida recusada: {url}")
        return f"ERRO DE VALIDAÇÃO:\n{e}"

    try:
        logger.info(f"Requisitando página: {url} | Seletor: {selector}")
        browser = await BrowserContext.get_browser()
        
        # Apenas criamos uma nova aba, o navegador já está aberto na RAM!
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_selector(selector, timeout=10000)
        text = await page.locator(selector).first.inner_text()
        
        # Fechamos a aba, mas não o navegador.
        await page.close()
        logger.info(f"Extração concluída com sucesso ({len(text)} caracteres).")
        return text
    except Exception as e:
        logger.error(f"Erro ao extrair texto com Playwright: {e}")
        return f"Erro de navegação: {str(e)}"


def main():
    mcp.run()

if __name__ == "__main__":
    main()
