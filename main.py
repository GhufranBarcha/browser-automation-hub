import asyncio
import os

# First launch can exceed the default 30s timeout on some machines.
os.environ.setdefault("TIMEOUT_BrowserStartEvent", "120")
os.environ.setdefault("TIMEOUT_BrowserLaunchEvent", "120")

from browser_use import Agent, Browser, ChatAnthropic
# from browser_use import ChatGoogle  # ChatGoogle(model='gemini-3-flash-preview')
# from browser_use import ChatBrowserUse

task = """
Go this this website https://portal.consumerfinance.gov/consumer/s/login/ 
Then login using these details userid charlesdavison1780@gmail.com  password: 1323Lotuscourt@
1. You will be on page Submit a complaint Step 1 of 5, Tick the fields as Follow
Choose the project  or services that best matches your complaint:
Credit reporting or other personal consumer reports

What type of credit reporting product?
Credit reporting

Then Press Next

2. What type of Problem are you having?
Incorrect information on your report


what best describe your problem?
Information belong to someone else

Have you tried to fix this problem with the company?
yes

Did you request from the company?
Yes

What information Did you request?
leave empty

Did the company provide this information?
No

Then Press Next:
Describe what happend and we'll send your comments to the companies involved.
Write this : Hi after reviewing my credit file I notice I had several negative on my credit report that werent mine


What would be a fair resolution to this?
I want these negatives itemns removed off my credit profile

Then press Next:

Credit reporting company
write exactly 'Experian'

We need this information to help the company find you in their system and respond to your complaint
Check all three - social security , Name as  , Date of Birth

Social Security Number (last 4 Digit)

"""

async def main() -> None:
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "Missing ANTHROPIC_API_KEY.\n"
            "Set it first, then run again (example: export ANTHROPIC_API_KEY='your_key')."
        )

    browser = Browser(
        headless=False,
        enable_default_extensions=False,
        # use_cloud=True,  # Use a stealth browser on Browser Use Cloud
    )

    agent = Agent(
        task=task,
        llm=ChatAnthropic(model='claude-sonnet-4-6'),
        # llm=ChatGoogle(model='gemini-3-flash-preview'),
        # llm=ChatBrowserUse(),
        browser=browser,
    )
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
