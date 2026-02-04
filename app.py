import asyncio
import json
import random
import os

# uv pip install -U camoufox
from browserforge.fingerprints import Screen
from camoufox import AsyncCamoufox
from playwright.async_api import Page
from hcaptcha_challenger import AgentV, AgentConfig, CaptchaResponse
from hcaptcha_challenger.utils import SiteKey

URLS = os.getenv("URLS").split("\n")
LOGIN = os.getenv("LOGIN").split("\n")
REF = os.getenv("REF")
API_KEY = os.getenv("API_KEY").split("\n")

async def challenge(page: Page) -> AgentV:
    """Automates the process of solving an hCaptcha challenge."""
    # [IMPORTANT] Initialize the Agent before triggering hCaptcha
    agent_config = AgentConfig(
        DISABLE_BEZIER_TRAJECTORY=True, GEMINI_API_KEY=random.choice(API_KEY))
    agent = AgentV(page=page, agent_config=agent_config)

    # In your real-world workflow, you may need to replace the `click_checkbox()`
    # It may be to click the Login button or the Submit button to a trigger challenge
    await agent.robotic_arm.click_checkbox()

    # Wait for the challenge to appear and be ready for solving
    await agent.wait_for_challenge()

    return agent


async def main():
    async with AsyncCamoufox(
        headless=True,
        #headless="virtual",
        persistent_context=True,
        user_data_dir="tmp/.cache/camoufox",
        screen=Screen(max_width=1366, max_height=768),
        # window=(1366, 657),
        humanize=0.2,  # humanize=True,
    ) as browser:
        page = browser.pages[-1] if browser.pages else await browser.new_page()

        for i in range(1, 21):
            try:
                # await page.wait_for_timeout(5000)
                URL = random.choice(URLS)
                msg = f"[{i}/15] Accessing..."
                print(f"╔{'═' * (len(msg) + 4)}╗")
                print(f"║  {msg}  ║")
                print(f"╚{'═' * (len(msg) + 4)}╝")
                await page.goto(f"{URL}?r={REF}", wait_until="domcontentloaded")
                await page.wait_for_timeout(2000)
                await page.wait_for_selector("#address")
                if not await page.input_value("#address"):
                    await page.type("#address", random.choice(LOGIN), delay=50)
                await page.wait_for_timeout(2000)
                await page.wait_for_selector('button:has-text("Start Claim")')
                await page.click('button:has-text("Start Claim")')
                await page.wait_for_timeout(2000)

                # --- When you encounter hCaptcha in your workflow ---
                agent: AgentV = await challenge(page)

                # Print the last CaptchaResponse
                if agent.cr_list:
                    cr: CaptchaResponse = agent.cr_list[-1]
                    # print(json.dumps(cr.model_dump(by_alias=True),
                    #       indent=2, ensure_ascii=False))

                await page.screenshot(path="screen.png", full_page=True)
                await page.wait_for_timeout(2000)
                await page.wait_for_selector('input#login')
                await page.click('input#login')
                await page.screenshot(path="screen.png", full_page=True)
                await page.wait_for_timeout(2000)
                try:
                    await page.wait_for_selector("div.alert-success", timeout=5000)
                    sucesso = await page.inner_text("div.alert-success")
                    print(f"\n\033[1;32mSUCCESS\033[0m | {sucesso}\n")
                except Exception as e:
                    print(f"\n\033[1;31mFAILURE\033[0m | No success message found.\n")
                    continue
            except Exception as e:
                print(f"\n\033[1;31mERROR\033[0m | Critical error occurred.\n")
                continue

if __name__ == "__main__":
    asyncio.run(main())






