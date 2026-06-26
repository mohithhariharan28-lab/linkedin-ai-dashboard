import asyncio
import os
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Error as PlaywrightError
from src.utils.logger import setup_logger

logger = setup_logger("auth.login")

class LinkedInAuthenticator:
    """Handles manual and automated authentication for LinkedIn using Playwright."""

    def __init__(
        self,
        session_path: Optional[str] = None,
        headless: bool = False,
        login_timeout_ms: int = 120000
    ) -> None:
        """Initializes the authenticator.

        Args:
            session_path: Path to the browser storage state JSON file.
            headless: Whether to run the browser in headless mode.
            login_timeout_ms: Time limit for manual login in milliseconds.
        """
        project_root = Path(__file__).resolve().parent.parent.parent
        default_session_path = os.path.join(project_root, "data", "session.json")
        
        self.session_path = Path(session_path or os.getenv("LINKEDIN_SESSION_PATH", default_session_path))
        
        # Load other configurations with sensible defaults
        env_headless = os.getenv("BROWSER_HEADLESS", "False").lower() in ("true", "1", "yes")
        self.headless = headless or env_headless
        
        try:
            self.login_timeout_ms = int(os.getenv("LOGIN_TIMEOUT_MS", str(login_timeout_ms)))
        except ValueError:
            self.login_timeout_ms = login_timeout_ms

    def _is_logged_in_url(self, url: str) -> bool:
        """Determines if the given URL represents a successful login state.

        Args:
            url: The page URL to check.

        Returns:
            bool: True if we are on the feed or another post-login landing page, and not on login/checkpoint.
        """
        url_lower = url.lower()
        # Logged-in page patterns
        is_feed_or_home = "linkedin.com/feed" in url_lower or "linkedin.com/de/feed" in url_lower
        has_feed_substring = "feed" in url_lower or "mynetwork" in url_lower or "messaging" in url_lower or "notifications" in url_lower
        
        # Keywords indicating we are still in authentication phases
        excluded_keywords = ["login", "checkpoint", "challenge", "signup", "auth", "logout"]
        is_excluded = any(kw in url_lower for kw in excluded_keywords)
        
        return (is_feed_or_home or has_feed_substring) and not is_excluded

    async def verify_session(self) -> bool:
        """Verifies if the saved session is valid by navigating to the feed.

        Returns:
            bool: True if session is valid, False otherwise.
        """
        if not self.session_path.exists():
            logger.warning(f"Session state file does not exist at {self.session_path}")
            return False
            
        async with async_playwright() as p:
            # We verify headlessly to keep it quiet
            browser: Browser = await p.chromium.launch(headless=True)
            context: Optional[BrowserContext] = None
            try:
                logger.info("Initializing verification browser context with saved session state...")
                context = await browser.new_context(storage_state=str(self.session_path))
                page: Page = await context.new_page()
                
                # Navigate to the feed directly
                logger.info("Navigating to LinkedIn feed page...")
                await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
                
                # Wait briefly to let redirects settle
                await asyncio.sleep(4)
                
                current_url = page.url
                logger.info(f"Verification landed on URL: {current_url}")
                
                if self._is_logged_in_url(current_url):
                    # Check the page title or text content to verify we aren't showing a blank or generic login page
                    page_title = await page.title()
                    body_text = await page.inner_text("body")
                    
                    # Check if "Feed" is in the title, or if we can see navigation words like "My Network", "Messaging", or "Notifications"
                    has_logged_in_keywords = any(
                        kw in page_title or kw in body_text 
                        for kw in ["Feed", "My Network", "Messaging", "Notifications", "Sign Out", "Log Out"]
                    )
                    
                    if has_logged_in_keywords:
                        logger.info("Successfully validated logged-in state via URL and content keywords.")
                        return True
                        
                    logger.warning("Landed on feed URL, but page content keywords were not found.")
                
                return False
            except PlaywrightError as e:
                logger.error(f"Playwright error during session verification: {e}")
                return False
            except Exception as e:
                logger.error(f"Unexpected error during session verification: {e}", exc_info=True)
                return False
            finally:
                if context:
                    await context.close()
                await browser.close()

    async def authenticate(self) -> bool:
        """Main authentication flow.

        First attempts to validate the existing session. If no session is found or
        the session is expired/invalid, it triggers a manual login flow.

        Returns:
            bool: True if authenticated successfully, False otherwise.
        """
        logger.info("Starting LinkedIn authentication flow...")
        
        # Ensure session directory exists
        self.session_path.parent.mkdir(parents=True, exist_ok=True)

        if self.session_path.exists():
            logger.info(f"Found session file at {self.session_path}. Verifying validity...")
            is_valid = await self.verify_session()
            if is_valid:
                logger.info("Saved session is still valid. No login required.")
                return True
            logger.warning("Saved session is invalid or expired. Manual login required.")
        else:
            logger.info("No saved session file found. Manual login required.")

        return await self._manual_login_flow()

    async def _manual_login_flow(self) -> bool:
        """Launches a headed browser instance for the user to manually log in.

        Returns:
            bool: True if manual login was successful and session saved, False otherwise.
        """
        async with async_playwright() as p:
            logger.info("Launching headed Chromium browser for manual login...")
            # For manual login, headless MUST be False
            browser: Browser = await p.chromium.launch(headless=False)
            context: BrowserContext = await browser.new_context()
            page: Page = await context.new_page()
            
            try:
                # Open login page
                logger.info("Navigating to LinkedIn login page...")
                await page.goto("https://www.linkedin.com/login")
                
                print("\n" + "="*80)
                print("ACTION REQUIRED:")
                print("1. A browser window has opened. Please log in manually.")
                print("2. Complete any verification prompts, MFA codes, or CAPTCHAs if prompted.")
                print(f"3. Keep the browser open until you reach your home feed. (Timeout: {self.login_timeout_ms / 1000:.0f}s)")
                print("="*80 + "\n")
                
                start_time = asyncio.get_event_loop().time()
                success = False
                
                # Poll the page URL to detect when the user is logged in
                while asyncio.get_event_loop().time() - start_time < self.login_timeout_ms / 1000:
                    current_url = page.url
                    if self._is_logged_in_url(current_url):
                        logger.info(f"Login success detected. Current URL: {current_url}")
                        success = True
                        break
                    await asyncio.sleep(1)
                
                if not success:
                    logger.error("Authentication timed out or user closed/cancelled the login page.")
                    print("\n" + "="*80)
                    print("TIMEOUT/FAILURE: Did not detect login redirection within the timeout.")
                    print("="*80 + "\n")
                    return False
                
                # Wait for session and cookies to fully settle
                logger.info("Login detected. Settle period (5s) starting...")
                await asyncio.sleep(5)
                
                # Double check that we are still logged in after settling
                final_url = page.url
                if not self._is_logged_in_url(final_url):
                    logger.error(f"Settle period finished but URL is no longer valid: {final_url}")
                    return False
                
                # Write state to disk
                logger.info(f"Writing browser storage state to disk: {self.session_path}")
                await context.storage_state(path=str(self.session_path))
                
                # Verify file was written and is not empty
                if self.session_path.exists() and self.session_path.stat().st_size > 0:
                    logger.info(f"Session file successfully written. Size: {self.session_path.stat().st_size} bytes.")
                    print("\n" + "="*80)
                    print(f"SUCCESS: Authentication cookies saved to {self.session_path}")
                    print("="*80 + "\n")
                    return True
                else:
                    logger.error("Session file was not written, or size is 0 bytes.")
                    return False
                    
            except PlaywrightError as e:
                logger.error(f"Playwright error during manual login: {e}", exc_info=True)
                return False
            except Exception as e:
                logger.error(f"Unexpected error during manual login: {e}", exc_info=True)
                return False
            finally:
                await context.close()
                await browser.close()
