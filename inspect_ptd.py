import asyncio
from playwright.async_api import async_playwright

async def get_html():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Acessando ptd.ooo...")
        await page.goto("https://ptd.ooo", wait_until="networkidle")
        html = await page.content()
        
        # Salva o HTML para podermos analisar os botões
        with open("C:\\Users\\Migra Tech\\Desktop\\code\\Data-Puppet\\ptd_source.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        print("HTML salvo com sucesso!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(get_html())
