import asyncio
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Error as PlaywrightError
from src.database.models import ProfileSnapshot
from src.utils.logger import setup_logger

logger = setup_logger("scraper.profile_service")

class LinkedInProfileScraperService:
    """Service class for scraping LinkedIn profile data."""

    def __init__(
        self,
        session_path: Optional[str] = None,
        headless: bool = True,
        timeout_ms: int = 30000
    ) -> None:
        """Initializes the profile scraper service.

        Args:
            session_path: Path to session.json state file.
            headless: Whether to run headlessly. Defaults to True.
            timeout_ms: General navigation timeout in milliseconds.
        """
        project_root = Path(__file__).resolve().parent.parent.parent
        default_session_path = os.path.join(project_root, "data", "session.json")
        
        self.session_path = Path(session_path or os.getenv("LINKEDIN_SESSION_PATH", default_session_path))
        self.headless = headless
        self.timeout_ms = timeout_ms

    async def _discover_profile_url(self, page: Page) -> str:
        """Discovers the current user's profile URL from the Feed page.

        Args:
            page: Active page object.

        Returns:
            str: Resolved profile URL.
        """
        logger.info("Auto-discovering profile URL from home feed...")
        await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=self.timeout_ms)
        await asyncio.sleep(4)  # Allow page to settle

        # Check all <a> elements containing "/in/" in the URL
        hrefs = await page.evaluate('''() => {
            const links = Array.from(document.querySelectorAll('a'));
            return links.map(link => link.href).filter(href => href.includes('/in/'));
        }''')
        
        valid_urls = []
        for href in hrefs:
            if "linkedin.com/in/" in href and not any(x in href.lower() for x in ["/edit/", "/create/"]):
                valid_urls.append(href)
                
        if valid_urls:
            discovered_url = valid_urls[0]
            logger.info(f"Discovered profile URL: {discovered_url}")
            return discovered_url

        sidebar_link = await page.query_selector("a.global-nav__primary-link[href*='/in/'], .feed-identity-module__actor-meta a")
        if sidebar_link:
            href = await sidebar_link.get_attribute("href")
            if href:
                url = href if href.startswith("http") else f"https://www.linkedin.com{href}"
                logger.info(f"Discovered profile URL via selector: {url}")
                return url

        raise Exception("Could not automatically discover LinkedIn profile URL. Ensure you are fully logged in.")

    async def _scroll_page(self, page: Page) -> None:
        """Scrolls down the page slowly to trigger lazy loading of profile sections."""
        logger.info("Scrolling page to load dynamic sections...")
        for i in range(1, 11):
            scroll_y = f"window.scrollTo(0, document.body.scrollHeight * {i / 10});"
            await page.evaluate(scroll_y)
            await asyncio.sleep(1.0)
        
        await page.evaluate("window.scrollTo(0, 0);")
        await asyncio.sleep(1.0)

    def _parse_number(self, pattern: str, text: str) -> Optional[int]:
        """Helper to extract integer count from a regex match group.

        Args:
            pattern: The regex pattern to execute.
            text: Input string.

        Returns:
            Optional[int]: Parsed integer or None if not found/invalid.
        """
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            clean_str = match.group(1).replace(",", "").replace(".", "").strip()
            try:
                return int(clean_str)
            except ValueError:
                return None
        return None

    async def scrape_profile(self, target_url: Optional[str] = None) -> ProfileSnapshot:
        """Performs profile scraping flow.

        Reuses session state, discovers target profile (if not provided),
        navigates, scrolls, and extracts data fields.

        Args:
            target_url: URL of the profile to scrape. If None, auto-discovers.

        Returns:
            ProfileSnapshot: Extracted profile data snapshot.
        """
        if not self.session_path.exists():
            raise FileNotFoundError(f"Session file not found at {self.session_path}. Run authentication first.")

        logger.info("Launching browser for profile scraping...")
        async with async_playwright() as p:
            browser: Browser = await p.chromium.launch(headless=self.headless)
            context: BrowserContext = await browser.new_context(storage_state=str(self.session_path))
            page: Page = await context.new_page()
            
            try:
                # 1. Discover URL if not specified
                url_to_scrape = target_url
                if not url_to_scrape:
                    url_to_scrape = await self._discover_profile_url(page)

                logger.info(f"Navigating to target profile: {url_to_scrape}")
                await page.goto(url_to_scrape, wait_until="domcontentloaded", timeout=self.timeout_ms)
                await asyncio.sleep(5)  # Let content settle

                # 2. Trigger lazy loading of lower sections
                await self._scroll_page(page)

                # 3. Extract text content from sections (resilient to CSS class changes)
                sections = page.locator("section")
                section_count = await sections.count()
                logger.info(f"Detected {section_count} section elements on profile page.")

                top_card_text = ""
                activity_text = ""
                experience_text = ""
                education_text = ""
                skills_text = ""
                about_text = ""

                for i in range(section_count):
                    sec = sections.nth(i)
                    sec_text = await sec.inner_text()
                    lines = [l.strip() for l in sec_text.split("\n") if l.strip()]
                    if not lines:
                        continue
                    
                    first_line = lines[0].lower()
                    
                    if "contact info" in sec_text.lower():
                        top_card_text = sec_text
                    elif first_line == "activity" or (any("followers" in l.lower() for l in lines) and "activity" in sec_text.lower()):
                        activity_text = sec_text
                    elif "experience" in first_line:
                        experience_text = sec_text
                    elif "education" in first_line:
                        education_text = sec_text
                    elif "skills" in first_line:
                        skills_text = sec_text
                    elif first_line == "about":
                        about_text = sec_text

                # Fallback for top card if "contact info" is not found in language/markup
                if not top_card_text and section_count > 1:
                    logger.debug("Falling back to Section 1 for top card...")
                    top_card_text = await sections.nth(1).inner_text()

                logger.debug(f"Top card text length: {len(top_card_text)}")
                logger.debug(f"Activity text length: {len(activity_text)}")
                logger.debug(f"About text length: {len(about_text)}")

                # 4. Parse fields from extracted section texts
                
                # Full Name (from title first, fallback to top card)
                full_name = "Unknown Name"
                try:
                    title = await page.title()
                    if "|" in title:
                        full_name = title.split("|")[0].strip()
                except Exception:
                    pass

                top_lines = [l.strip() for l in top_card_text.split("\n") if l.strip()] if top_card_text else []
                if (full_name == "Unknown Name" or not full_name) and top_lines:
                    full_name = top_lines[0]

                # Headline
                headline = ""
                if len(top_lines) > 1:
                    headline = top_lines[1]

                # Location
                location = ""
                if top_lines:
                    for idx, line in enumerate(top_lines):
                        if "contact info" in line.lower() and idx > 0:
                            prev_line = top_lines[idx - 1]
                            location = top_lines[idx - 2] if prev_line == "•" and idx > 1 else prev_line
                            break
                    if not location:
                        # Fallback regex search
                        for line in top_lines:
                            if any(kw in line for kw in [", India", "Area", "County", "City", "Province", "State"]):
                                location = line
                                break

                # About
                about = ""
                if about_text:
                    about_lines = [l.strip() for l in about_text.split("\n") if l.strip()]
                    about = "\n".join(about_lines[1:]) if len(about_lines) > 1 else about_text

                # Followers & Connections
                followers = None
                if activity_text:
                    for line in activity_text.split("\n"):
                        if "followers" in line.lower():
                            followers = self._parse_number(r"([\d,.]+)\s*followers", line)
                            if followers is not None:
                                break
                if followers is None:
                    # Fallback to scanning body text
                    body_text = await page.inner_text("body")
                    followers = self._parse_number(r"([\d,.]+)\s*followers", body_text)

                connections = None
                if top_card_text:
                    for line in top_card_text.split("\n"):
                        if "connections" in line.lower():
                            connections = self._parse_number(r"([\d,.]+)(\+)?\s*connections", line)
                            if connections is not None:
                                break

                # 5. Extract structured lists using elements and fallbacks
                
                # Experience
                experience_items: List[Dict[str, Any]] = []
                if experience_text:
                    exp_sec_loc = page.locator("section").filter(has_text=re.compile(r"^Experience", re.IGNORECASE))
                    if await exp_sec_loc.count() > 0:
                        lis = exp_sec_loc.first.locator("li")
                        li_count = await lis.count()
                        for i in range(li_count):
                            item_text = await lis.nth(i).inner_text()
                            lines = [l.strip() for l in item_text.split("\n") if l.strip()]
                            if lines:
                                experience_items.append({
                                    "item_index": i,
                                    "raw_text": " | ".join(lines),
                                    "lines": lines
                                })
                    if not experience_items:
                        exp_lines = [l.strip() for l in experience_text.split("\n") if l.strip()]
                        experience_items = [{"raw_text": " | ".join(exp_lines[1:]), "lines": exp_lines[1:]}]

                # Current Company (from the first experience item)
                current_company = ""
                if experience_items:
                    first_job_lines = experience_items[0].get("lines", [])
                    if len(first_job_lines) > 1:
                        # Extract company name by splitting common delimiters
                        comp = first_job_lines[1]
                        current_company = comp.split(" · ")[0].split(" - ")[0].split(" | ")[0].strip()
                if not current_company and len(top_lines) > 2:
                    current_company = top_lines[2]

                # Education
                education_items: List[Dict[str, Any]] = []
                if education_text:
                    edu_sec_loc = page.locator("section").filter(has_text=re.compile(r"^Education", re.IGNORECASE))
                    if await edu_sec_loc.count() > 0:
                        lis = edu_sec_loc.first.locator("li")
                        li_count = await lis.count()
                        for i in range(li_count):
                            item_text = await lis.nth(i).inner_text()
                            lines = [l.strip() for l in item_text.split("\n") if l.strip()]
                            if lines:
                                education_items.append({
                                    "item_index": i,
                                    "raw_text": " | ".join(lines),
                                    "lines": lines
                                })
                    if not education_items:
                        edu_lines = [l.strip() for l in education_text.split("\n") if l.strip()]
                        education_items = [{"raw_text": " | ".join(edu_lines[1:]), "lines": edu_lines[1:]}]

                # Skills
                skills_items: List[str] = []
                if skills_text:
                    skills_sec_loc = page.locator("section").filter(has_text=re.compile(r"^Skills", re.IGNORECASE))
                    if await skills_sec_loc.count() > 0:
                        lis = skills_sec_loc.first.locator("li")
                        li_count = await lis.count()
                        for i in range(li_count):
                            item_text = await lis.nth(i).inner_text()
                            lines = [l.strip() for l in item_text.split("\n") if l.strip()]
                            if lines:
                                skill_name = lines[0]
                                if skill_name.lower() not in ["skills", "endorse", "see details"]:
                                    skills_items.append(skill_name)
                    if not skills_items:
                        sk_lines = [l.strip() for l in skills_text.split("\n") if l.strip()]
                        for item in sk_lines[1:]:
                            if item.lower() not in ["endorse", "see details"] and len(item) < 60:
                                skills_items.append(item)

                # Assemble Snapshot
                snapshot = ProfileSnapshot(
                    full_name=full_name,
                    headline=headline,
                    profile_url=url_to_scrape,
                    followers=followers,
                    connections=connections,
                    location=location,
                    about=about,
                    current_company=current_company,
                    experience=experience_items,
                    education=education_items,
                    skills=skills_items,
                    scraped_at=datetime.utcnow().isoformat()
                )
                
                logger.info(f"Successfully scraped profile: {full_name} ({followers} followers, {connections} connections)")
                return snapshot
                
            except PlaywrightError as e:
                logger.error(f"Playwright error during profile scraping: {e}", exc_info=True)
                raise
            except Exception as e:
                logger.error(f"Unexpected error during profile scraping: {e}", exc_info=True)
                raise
            finally:
                await context.close()
                await browser.close()
