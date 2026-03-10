import asyncio
import os

# First launch can exceed the default 30s timeout on some machines.
os.environ.setdefault("TIMEOUT_BrowserStartEvent", "120")
os.environ.setdefault("TIMEOUT_BrowserLaunchEvent", "120")
os.environ.setdefault("TIMEOUT_UploadFileEvent", "120")

from browser_use import Agent, Browser, ChatAnthropic
# from browser_use import ChatGoogle  # ChatGoogle(model='gemini-3-flash-preview')
# from browser_use import ChatBrowserUse

PDF_PATH = "/home/ghufranbarcha/Desktop/Freelance Task/BrowserUse-jahaadbeckford/burhan_cv.pdf"

task = f"""
Go this this website https://portal.consumerfinance.gov/consumer/s/login/ 
Then login using these details:
Userid: charlesdavison1780@gmail.com
Password: 1323Lotuscourt@


1. You will be on page Submit a complaint Step 1 of 5, Tick the fields as Follow

Step 1:

1.1 What is this complaint about?
Choose the product or service that best matches your complaint.
Credit reporting or other personal consumer reports(background checks, employment, or tenant screening)


1.2 What type of credit reporting product?
Credit reporting

Then Press Next

Step 2:

2.1 What type of problem are you having?
Most of the credit reporting complaints we get are about one of the following topics. Select the one that best describes your complaint. You will have the chance to explain your complaint in detail in the next step.
Incorrect information on your report(account or personal information incorrect, information not mine)


2.1 Which best describes your problem?
Information belongs to someone else(identity theft, error)

2.1 Have you already tried to fix this problem with the company?
Yes

2.3 Did you request information from the company?
Yes

2.4 What information did you request? (optional)
leave empty

2.5 Did the company provide this information?
No

Then Press Next:

Step 3:



3.1 What happened?
Describe what happened, and we’ll send your comments to the companies involved.
Write this : Hi after reviewing my credit file I notice I had several negative on my credit report that werent mine


3.2 What would be a fair resolution to this issue?
Write this: I want these negatives itemns removed off my credit profile

3.3 Attach documents Upload the File
{PDF_PATH}

Then press Next:

Step 4:


4.1 What company is this complaint about?
Start typing the 'Company name' below. Select a company from the list or provide the company’s contact information.

Credit Reporting company: Company Name
write exactly 'Experian' then select'Experian'

4.2 We need this information to help the company find you in their system and respond to your complaint.
Check all three - social security , Name as  , Date of Birth

4.3 Social Security number (last 4 digits)
3334

4.4 Date of birth
01 01 1990

4.5 Name as it appears on credit report
Jiquan Duck

4.6 Do you want to complain about another company?
Write 'TransUnion' and select 'TransUnion'

4.7 Have you already tried to fix this problem with the company?
Yes

4.8 Did you request information from the company?
Yes

4.9 What information did you request? (optional)
Leave empty

4.10 Did the company provide this information?
Yes

4.11 We need this information to help the company find you in their system and respond to your complaint. (optional)
Select all three: Social Security, Name, Date of Birth

4.12 Social Security number (last 4 digits)
0446

4.13 Date of birth
01 01 1990

4.14 Name as it appears on credit report
Jiquan Duck

4.15 Do you want to complain about another company?
Yes

4.16 Additional company
Company name
Write 'equifax,' and select 'EQUIFAX, INC.'


4.17 Have you already tried to fix this problem with the company?
Yes

4.18 Did you request information from the company?
Yes

4.19 What information did you request? (optional)
Leave empty

4.20 Did the company provide this information?
Yes

4.21 We need this information to help the company find you in their system and respond to your complaint. (optional)
Select all three: Social Security, Name, Date of Birth

4.22 Social Security number (last 4 digits)
0446

4.23 Date of birth
01 01 1990

4.24 Name as it appears on credit report
Jiquan Duck


Then Press Next:

Step 5:

5.1 Who are you submitting this complaint for?
Myself (I am submitting this complaint for myself)

5.2 Address line 1
465 wood street

5.3 
City: mt laurel
state: selet New Jersey from dropdown
zip: 08046

And then Just click review at the bottom


Then
Review your complaint Page:

Scroll Down and click both:
I authorize and direct (1) the consumer reporting agency identified.

The information given is true to

Then Submit Your Compliant Button




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

    if not os.path.isfile(PDF_PATH):
        raise RuntimeError(
            f"PDF file not found at: {PDF_PATH}\n"
            "Set PDF_PATH to an existing absolute file path."
        )

    agent = Agent(
        task=task,
        llm=ChatAnthropic(model='claude-sonnet-4-6'),
        # llm=ChatGoogle(model='gemini-3-flash-preview'),
        # llm=ChatBrowserUse(),
        browser=browser,
        available_file_paths=[PDF_PATH],
    )
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
