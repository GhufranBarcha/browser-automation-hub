"""Browser automation runner — extracted and adapted from main.py."""
import asyncio
import logging
import os
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class RunResult:
    success: bool
    error: str | None = None
    steps_taken: int = 0


async def run_automation(
    prompt: str,
    pdf_path: str | None,
    task_id: str,
    cancel_flag: asyncio.Event,
) -> RunResult:
    """
    Run a single browser automation task.

    Args:
        prompt:      The full task instruction string.
        pdf_path:    Absolute path to the uploaded PDF (or None).
        task_id:     Our DB task UUID — passed to browser-use for correlated logs.
        cancel_flag: An asyncio.Event; when set the agent will stop at next opportunity.

    Returns:
        RunResult with success/failure and optional error message.
    """
    from app.config import ANTHROPIC_API_KEY, LLM_MODEL

    if not ANTHROPIC_API_KEY:
        return RunResult(success=False, error="ANTHROPIC_API_KEY is not configured")

    # Validate PDF if provided
    available_files: list[str] = []
    if pdf_path:
        if not Path(pdf_path).is_file():
            return RunResult(success=False, error=f"PDF file not found: {pdf_path}")
        available_files = [pdf_path]

    try:
        # Lazy imports — browser_use is heavy
        from browser_use import Agent, BrowserSession, ChatAnthropic

        async def should_stop() -> bool:
            return cancel_flag.is_set()

        browser = BrowserSession(
            headless=False,
            enable_default_extensions=False,
        )

        agent = Agent(
            task=prompt,
            llm=ChatAnthropic(model=LLM_MODEL),
            browser=browser,
            available_file_paths=available_files,
            task_id=task_id,
            register_should_stop_callback=should_stop,
        )

        logger.info(f"[task:{task_id[-8:]}] Starting automation — model={LLM_MODEL}")
        history = await agent.run()

        if cancel_flag.is_set():
            return RunResult(success=False, error="Task was cancelled", steps_taken=len(history.history))

        logger.info(f"[task:{task_id[-8:]}] Automation completed in {len(history.history)} steps")
        return RunResult(success=True, steps_taken=len(history.history))

    except Exception as exc:
        logger.exception(f"[task:{task_id[-8:]}] Automation failed: {exc}")
        return RunResult(success=False, error=str(exc))
    finally:
        # Ensure browser resources are released
        try:
            if "browser" in dir():
                await browser.close()
        except Exception:
            pass
