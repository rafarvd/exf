import asyncio
import json
import os
import random

# uv pip install -U camoufox
from browserforge.fingerprints import Screen
from camoufox import AsyncCamoufox
from playwright.async_api import Page

from hcaptcha_challenger import AgentV, AgentConfig, CaptchaResponse
from hcaptcha_challenger.utils import SiteKey

MAX_RETRIES = 5  # None = infinito
url = os.getenv("URL")
comando = os.getenv("COMANDO")

async def challenge(page: Page) -> AgentV:
    """Automates the process of solving an hCaptcha challenge."""
    # [IMPORTANT] Initialize the Agent before triggering hCaptcha
    api_key = os.getenv("API_KEY").split('\n')
    agent_config = AgentConfig(
        DISABLE_BEZIER_TRAJECTORY=True, GEMINI_API_KEY=random.choice(api_key))
    agent = AgentV(page=page, agent_config=agent_config)

    # In your real-world workflow, you may need to replace the `click_checkbox()`
    # It may be to click the Login button or the Submit button to a trigger challenge
    await agent.robotic_arm.click_checkbox()

    # Wait for the challenge to appear and be ready for solving
    await agent.wait_for_challenge()

    return agent

async def run_browser():
    async with AsyncCamoufox(
        headless=True,
        persistent_context=True,
        user_data_dir="tmp/.cache/camoufox",
        screen=Screen(max_width=1366, max_height=768),
        humanize=0.2,  # humanize=True,
    ) as browser:
        page = browser.pages[-1] if browser.pages else await browser.new_page()

        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        await page.wait_for_selector('button.button[data-type="linux"]')
        await page.click('button.button[data-type="linux"]')
        await page.wait_for_timeout(3000)

        # --- When you encounter hCaptcha in your workflow ---
        agent: AgentV = await challenge(page)

        # Print the last CaptchaResponse
        if agent.cr_list:
            cr: CaptchaResponse = agent.cr_list[-1]
            # print(json.dumps(cr.model_dump(by_alias=True),
            #       indent=2, ensure_ascii=False))

        await page.wait_for_timeout(5000)

        await page.wait_for_selector("textarea.xterm-helper-textarea", timeout=60000)
        print("Terminal carregado com sucesso!")
        await page.wait_for_timeout(5000)
        await page.type("textarea.xterm-helper-textarea", comando, delay=40, timeout=60000)
        await page.keyboard.press("Enter")
        print("Comando digitado com sucesso!")
        await page.wait_for_timeout(30000)
        await page.screenshot(path="screen.png", full_page=True)

        # lines = await page.locator(".xterm-rows > div").all_text_contents()
        # terminal_text = "\n".join(lines)
        # print(terminal_text.strip())

        minutos = 15
        # await asyncio.sleep(minutos * 60)
        await page.wait_for_timeout(minutos * 60 * 1000)
        await page.screenshot(path="screen.png", full_page=True)

async def main():
    attempts = 0
    while True:
        try:
            print("🚀 Iniciando navegador...")
            await run_browser()
            print("✅ Finalizado com sucesso")
            break
        except Exception as e:
            attempts += 1
            print(f"❌ Erro (tentativa {attempts}): {e}")
            if MAX_RETRIES and attempts >= MAX_RETRIES:
                print("🛑 Limite de tentativas atingido")
                break
            print("♻️ Reiniciando em 5 segundos...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
