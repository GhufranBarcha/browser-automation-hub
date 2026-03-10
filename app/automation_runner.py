"""Browser automation runner — extracted and adapted from main.py.

SDK Reference: https://docs.browser-use.com/open-source/customize/agent/all-parameters
Output Format:  https://docs.browser-use.com/open-source/customize/agent/output-format
"""
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
    final_result: str | None = None


async def run_automation(
    prompt: str,
    pdf_path: str | None,
    task_id: str,
    cancel_flag: asyncio.Event,
    step_callback=None,  # Optional async fn(step_num: int, goal: str, url: str | None) -> None
) -> RunResult:
    """
    Run a single browser automation task using the browser-use Python SDK.

    Args:
        prompt:        The full task instruction string.
        pdf_path:      Absolute path to the uploaded PDF (or None).
        task_id:       Our DB task UUID — passed to browser-use for correlated logs.
        cancel_flag:   An asyncio.Event; when set the agent will stop at next opportunity.
        step_callback: Optional async callback called after each agent step.

    Returns:
        RunResult with success/failure, optional error message, and step count.

    SDK Notes (https://docs.browser-use.com/open-source/customize/agent/all-parameters):
        - `register_should_stop_callback`: async () -> bool  → stop agent at next step
        - `register_new_step_callback`: (BrowserStateSummary, AgentOutput, int) -> None
        - `available_file_paths`: list[str] of paths agent may upload
        - `task_id`: str — passed through for browser-use internal logging
        - `max_failures` (default 3): internal retry budget before aborting
        - `step_timeout` (default 120s): seconds before a single step times out

    History methods (https://docs.browser-use.com/open-source/customize/agent/output-format):
        - `history.is_successful()` → bool | None  (None = not done yet)
        - `history.is_done()`       → bool
        - `history.has_errors()`    → bool
        - `history.errors()`        → list[str | None]
        - `history.final_result()`  → str | None
        - `history.number_of_steps()` → int  (or len(history.history))
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

    browser = None
    try:
        # Lazy imports — browser_use is heavy
        from browser_use import Agent, BrowserSession, ChatAnthropic

        # ── Cancellation callback ────────────────────────────────────────────
        # SDK: register_should_stop_callback: async () -> bool
        # Checked by agent before each new step; returning True causes graceful stop.
        async def should_stop() -> bool:
            return cancel_flag.is_set()

        # ── Step progress callback ───────────────────────────────────────────
        # SDK: register_new_step_callback: (BrowserStateSummary, AgentOutput, int) -> None
        # Called AFTER each step completes. We use it to stream live updates to DB.
        async def on_new_step(browser_state, agent_output, step_number: int):
            try:
                next_goal = ""
                if hasattr(agent_output, "next_goal") and agent_output.next_goal:
                    next_goal = agent_output.next_goal
                elif hasattr(agent_output, "current_state") and agent_output.current_state:
                    next_goal = getattr(agent_output.current_state, "next_goal", "")

                url = getattr(browser_state, "url", None) or ""
                msg_parts = [f"Step {step_number}"]
                if next_goal:
                    msg_parts.append(f"→ {next_goal}")
                if url:
                    msg_parts.append(f"[{url}]")

                log_msg = " ".join(msg_parts)
                logger.info(f"[task:{task_id[-8:]}] {log_msg}")

                if step_callback:
                    await step_callback(step_number, next_goal, url)
            except Exception as e:
                logger.debug(f"[task:{task_id[-8:]}] step callback error (non-fatal): {e}")

        # ── Browser session ──────────────────────────────────────────────────
        # SDK: BrowserSession(headless=...) — use headless=True for server/worker runs.
        # User explicitly set headless=False to see the browser window.
        browser = BrowserSession(
            headless=os.environ.get("BROWSER_HEADLESS", "true").lower() == "true",
            enable_default_extensions=False,
        )

        # ── Agent configuration ──────────────────────────────────────────────
        agent = Agent(
            task=prompt,
            llm=ChatAnthropic(model=LLM_MODEL),
            browser=browser,
            available_file_paths=available_files if available_files else None,
            task_id=task_id,
            register_should_stop_callback=should_stop,
            register_new_step_callback=on_new_step,
            # Speed optimizations
            # max_actions_per_step=10,  # Fill multiple form fields per LLM call (default: 4)
            use_vision='auto',        # Only take screenshots when needed (default: True = every step)
        )

        logger.info(f"[task:{task_id[-8:]}] Starting automation — model={LLM_MODEL}")
        history = await agent.run()

        # ── Cancellation check ───────────────────────────────────────────────
        # If cancel_flag was set while agent was running, treat as cancelled.
        if cancel_flag.is_set():
            steps = len(history.history)
            return RunResult(success=False, error="Task was cancelled", steps_taken=steps)

        steps = len(history.history)

        # ── Success check using official SDK API ─────────────────────────────
        # is_successful() returns:
        #   True  → agent explicitly marked success
        #   False → agent explicitly marked failure
        #   None  → agent never reached a done action (browser was closed / crash)
        is_success = history.is_successful()

        if is_success is True:
            final_text = history.final_result()
            logger.info(f"[task:{task_id[-8:]}] Completed in {steps} steps. Result: {final_text!r}")
            return RunResult(success=True, steps_taken=steps, final_result=final_text)

        # Collect the last meaningful error
        err_msg: str
        if is_success is False:
            # Agent ran to completion but declared failure
            all_errors = [e for e in history.errors() if e]
            if all_errors:
                err_msg = all_errors[-1]
            else:
                final_text = history.final_result()
                err_msg = final_text or "Agent reported failure without a specific error"
        else:
            # is_success is None → agent never called done (browser closed / crash / timeout)
            all_errors = [e for e in history.errors() if e]
            if all_errors:
                err_msg = all_errors[-1]
            else:
                err_msg = "Task did not complete — browser may have been closed or timed out"

        logger.error(f"[task:{task_id[-8:]}] Finished with failure in {steps} steps: {err_msg}")
        return RunResult(success=False, error=err_msg, steps_taken=steps)

    except Exception as exc:
        logger.exception(f"[task:{task_id[-8:]}] Automation raised exception: {exc}")
        return RunResult(success=False, error=str(exc))
    finally:
        # Always release browser resources
        if browser is not None:
            try:
                await browser.close()
            except Exception:
                pass
