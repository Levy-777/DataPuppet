import asyncio
from playwright.async_api import async_playwright

async def login_and_get_pokemons():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 1. Acessa o site
        print("[1/5] Acessando ptd.ooo...")
        await page.goto("https://ptd.ooo", wait_until="networkidle")
        
        # 2. Aceita cookies (se aparecer)
        try:
            accept_btn = page.locator("a.accept")
            if await accept_btn.is_visible(timeout=2000):
                await accept_btn.click()
                print("[2/5] Cookies aceitos.")
        except:
            print("[2/5] Banner de cookies não apareceu, seguindo...")
        
        # 3. Faz login
        print("[3/5] Preenchendo credenciais...")
        await page.fill("#email", "broskrskr@gmail.com")
        await page.fill("#password", "trocanunca")
        await page.click("input[type='submit']")
        
        # 4. Espera a página pós-login carregar
        print("[4/5] Aguardando login...")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)
        
        # Salva a página pós-login para ver o que apareceu
        post_login_url = page.url
        post_login_html = await page.content()
        print(f"  URL pós-login: {post_login_url}")
        
        with open("C:\\Users\\Migra Tech\\Desktop\\code\\Data-Puppet\\post_login.html", "w", encoding="utf-8") as f:
            f.write(post_login_html)
        
        # 5. Tenta navegar para a aba "My Pokemons"
        print("[5/5] Procurando aba 'My Pokemons'...")
        
        # Procura por links que contenham "pokemon" no texto ou no href
        links = await page.locator("a").all()
        found_links = []
        for link in links:
            text = await link.inner_text()
            href = await link.get_attribute("href") or ""
            if "pokemon" in text.lower() or "pokemon" in href.lower() or "mypokemon" in href.lower():
                found_links.append({"text": text.strip(), "href": href})
        
        if found_links:
            print(f"  Links encontrados: {found_links}")
            # Clica no primeiro link relevante
            target = found_links[0]
            print(f"  Navegando para: {target['href']}")
            await page.goto(target["href"], wait_until="networkidle")
            await asyncio.sleep(2)
            
            pokemon_html = await page.content()
            with open("C:\\Users\\Migra Tech\\Desktop\\code\\Data-Puppet\\my_pokemons.html", "w", encoding="utf-8") as f:
                f.write(pokemon_html)
            
            # Tenta extrair nomes de pokémons
            body_text = await page.locator("body").inner_text()
            print("\n=== CONTEÚDO DA PÁGINA MY POKEMONS ===")
            print(body_text[:3000])
        else:
            print("  Nenhum link de Pokémon encontrado. Listando todos os links da página:")
            all_links = await page.locator("a").all()
            for link in all_links:
                text = (await link.inner_text()).strip()
                href = await link.get_attribute("href") or ""
                if text:
                    print(f"  - [{text}] -> {href}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(login_and_get_pokemons())
