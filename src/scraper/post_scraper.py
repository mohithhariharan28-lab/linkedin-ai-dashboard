import asyncio
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Error as PlaywrightError
from src.database.models import PostSnapshot
from src.utils.logger import setup_logger

logger = setup_logger("scraper.post_scraper")

class LinkedInPostScraperService:
    """Service class for scraping LinkedIn posts and activity data."""

    def __init__(
        self,
        session_path: Optional[str] = None,
        headless: bool = True,
        timeout_ms: int = 30000
    ) -> None:
        """Initializes the post scraper service.

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

    def _parse_relative_date(self, relative_str: str) -> datetime:
        """Parses relative LinkedIn time descriptions into UTC datetimes.

        Handles strings like "5h", "2d", "1w", "3mo", "1yr", "Edited".

        Args:
            relative_str: Relative date string.

        Returns:
            datetime: Calculated approximate UTC datetime.
        """
        now = datetime.utcnow()
        # Clean the string (remove bullets, dots, spaces, "Edited" text, other unicode relics)
        clean = relative_str.lower().replace("edited", "")
        clean = re.sub(r"[^a-z0-9]", "", clean)
        
        # Search for digits followed by unit (check multi-character units first to prevent partial matches)
        match = re.match(r"(\d+)(mo|yr|m|h|d|w)", clean)
        if not match:
            # Fallback if text contains "yesterday" or similar
            if "yesterday" in clean:
                return now - timedelta(days=1)
            return now
            
        value = int(match.group(1))
        unit = match.group(2)
        
        if unit == "m":
            return now - timedelta(minutes=value)
        elif unit == "h":
            return now - timedelta(hours=value)
        elif unit == "d":
            return now - timedelta(days=value)
        elif unit == "w":
            return now - timedelta(weeks=value)
        elif unit == "mo":
            return now - timedelta(days=value * 30)  # Approximate month
        elif unit == "yr":
            return now - timedelta(days=value * 365)  # Approximate year
            
        return now


    async def _scroll_page(self, page: Page, max_scrolls: int = 40) -> None:
        """Scrolls down the page repeatedly to trigger loading of older posts."""
        logger.info("Scrolling posts page to load older activity...")
        last_height = await page.evaluate("document.body.scrollHeight")
        no_change_count = 0
        
        for i in range(max_scrolls):
            # Scroll down incrementally in steps to trigger lazy loader
            for step in range(4):
                await page.evaluate("window.scrollBy(0, 800);")
                await asyncio.sleep(0.4)
                
            # Scroll to the absolute bottom of the body
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(2.5)  # Wait for new posts to load
            
            # Click any 'Show more' button if present
            try:
                show_more_button = page.locator("button.scaffold-finite-scroll__load-button, button:has-text('Show more results'), button:has-text('Load more')")
                if await show_more_button.count() > 0 and await show_more_button.is_visible():
                    logger.info("Found 'Show more results' button. Clicking it to load more posts...")
                    await show_more_button.click()
                    await asyncio.sleep(3.0)
            except Exception as btn_err:
                logger.debug(f"Show more button check skipped: {btn_err}")
                
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                # Scroll up slightly, wait, and scroll down again to shake the lazy load listeners
                await page.evaluate("window.scrollBy(0, -300);")
                await asyncio.sleep(0.5)
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                await asyncio.sleep(2.0)
                
                new_height = await page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    no_change_count += 1
                    if no_change_count >= 4:
                        logger.info(f"Reached bottom of the posts page after {i+1} scroll cycles (height: {new_height}px).")
                        break
                else:
                    no_change_count = 0
                    last_height = new_height
            else:
                no_change_count = 0
                last_height = new_height

    async def scrape_posts(self, profile_url: str) -> List[PostSnapshot]:
        """Scrapes all posts from the user's recent activity shares page.

        Args:
            profile_url: Discovered LinkedIn profile URL of the user.

        Returns:
            List[PostSnapshot]: Scraped post snapshots.
        """
        if not self.session_path.exists():
            raise FileNotFoundError(f"Session file not found at {self.session_path}. Run authentication first.")

        # Clean trailing slash and construct the posts Shares page URL
        base_profile = profile_url.rstrip("/")
        shares_url = f"{base_profile}/recent-activity/shares/"
        
        logger.info(f"Navigating directly to posts page: {shares_url}")
        
        async with async_playwright() as p:
            browser: Browser = await p.chromium.launch(headless=self.headless)
            context: BrowserContext = await browser.new_context(storage_state=str(self.session_path))
            page: Page = await context.new_page()
            
            try:
                await page.goto(shares_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                await asyncio.sleep(4)  # Let content load
                
                # Check if we were redirected to login (session expired)
                current_url = page.url
                if "login" in current_url or "checkpoint" in current_url:
                    logger.error("Session expired or invalid during post scraping navigation.")
                    raise PermissionError("Session expired. Please re-authenticate.")

                # Scroll to load all posts
                await self._scroll_page(page, max_scrolls=60)
                
                # Locate post card containers
                # Standard LinkedIn update elements are represented by article tags or divs with class feed-shared-update-v2
                post_locators = page.locator("div[data-urn*='urn:li:activity:'], div.feed-shared-update-v2, article")
                raw_count = await post_locators.count()
                logger.info(f"Found {raw_count} raw post containers on page.")
                
                scraped_posts: List[PostSnapshot] = []
                seen_urns = set()

                for i in range(raw_count):
                    post_el = post_locators.nth(i)
                    
                    # Get URN to check for ID
                    urn = await post_el.get_attribute("data-urn")
                    if not urn or "urn:li:activity:" not in urn:
                        # Fallback: check if we can locate urn in sub links or child attributes
                        urn_attr = await post_el.get_attribute("data-activity-id")
                        if urn_attr:
                            urn = f"urn:li:activity:{urn_attr}"
                        else:
                            continue
                    
                    if urn in seen_urns:
                        continue
                    seen_urns.add(urn)
                    
                    # Extract ID
                    linkedin_post_id = urn.split(":")[-1]
                    post_url = f"https://www.linkedin.com/feed/update/{urn}"

                    # Extract Post Text
                    # Commentary element contains the post content
                    text_loc = post_el.locator(".feed-shared-update-v2__commentary, .feed-shared-text, .update-components-text, span.break-words").first
                    post_text = (await text_loc.inner_text()).strip() if await text_loc.count() > 0 else ""

                    # Extract Post Date (Relative)
                    # Located inside the sub-description of the actor header
                    actor_sub_loc = post_el.locator(".feed-shared-actor__sub-description, .update-components-actor__sub-description, .feed-shared-actor__meta").first
                    relative_date_text = "5h"
                    if await actor_sub_loc.count() > 0:
                        raw_sub = await actor_sub_loc.inner_text()
                        # Clean to isolate the time portion (usually the line with "h", "d", "w", "mo", "yr")
                        lines = [l.strip() for l in raw_sub.split("\n") if l.strip()]
                        for line in lines:
                            cleaned_line = re.sub(r"[•·\s]", "", line).lower()
                            # Match if starts with digit followed by unit, or contains yesterday/edited/bullet
                            if re.match(r"^\d+(mo|yr|m|h|d|w)", cleaned_line) or "yesterday" in cleaned_line or "edited" in cleaned_line or "•" in line or "·" in line:
                                # Ensure it doesn't look like a long headline or name
                                if len(cleaned_line) < 15 and not any(x in cleaned_line for x in ["student", "engineer", "manager", "developer", "founder", "analyst", "specialist"]):
                                    relative_date_text = line
                                    break

                    
                    post_datetime = self._parse_relative_date(relative_date_text)
                    post_date_str = post_datetime.isoformat()
                    
                    # Calculate date categories
                    weekday = post_datetime.strftime("%A")
                    month = post_datetime.strftime("%B")
                    year = post_datetime.year

                    # Extract Social Reactions (Likes, Comments, Reposts)
                    social_counts_loc = post_el.locator(".social-details-social-counts").first
                    likes = 0
                    comments = 0
                    reposts = 0
                    
                    if await social_counts_loc.count() > 0:
                        counts_text = await social_counts_loc.inner_text()
                        
                        # Parse reactions (likes)
                        likes_match = re.search(r"([\d,.]+)\s*(reaction|like|others)", counts_text, re.IGNORECASE)
                        if likes_match:
                            likes = int(likes_match.group(1).replace(",", ""))
                        else:
                            # Check for "and X others"
                            others_match = re.search(r"and\s+([\d,.]+)\s+others", counts_text, re.IGNORECASE)
                            if others_match:
                                likes = int(others_match.group(1).replace(",", "")) + 1
                            elif len(counts_text.strip()) > 0:
                                # Try parsing first numbers
                                digits = re.findall(r"\d+", counts_text)
                                if digits:
                                    likes = int(digits[0])
                        
                        # Comments
                        comments_match = re.search(r"([\d,.]+)\s*comment", counts_text, re.IGNORECASE)
                        if comments_match:
                            comments = int(comments_match.group(1).replace(",", ""))
                            
                        # Reposts
                        reposts_match = re.search(r"([\d,.]+)\s*repost", counts_text, re.IGNORECASE)
                        if reposts_match:
                            reposts = int(reposts_match.group(1).replace(",", ""))

                    # Media Type Classification
                    media_type = "Text"
                    if await post_el.locator(".update-components-carousel, .feed-shared-carousel").count() > 0:
                        media_type = "Carousel"
                    elif await post_el.locator(".update-components-document, .feed-shared-document, iframe[title*='document']").count() > 0:
                        media_type = "Document"
                    elif await post_el.locator(".update-components-video, .feed-shared-video, video").count() > 0:
                        media_type = "Video"
                    elif await post_el.locator(".update-components-image, .feed-shared-image").count() > 0:
                        media_type = "Image"
                    else:
                        # Fallback checks
                        if await post_el.locator("img").count() > 0:
                            imgs = post_el.locator("img")
                            for img_idx in range(await imgs.count()):
                                w = await imgs.nth(img_idx).get_attribute("width")
                                if w and w.isdigit() and int(w) > 100:
                                    media_type = "Image"
                                    break
                                    
                    snapshot = PostSnapshot(
                        linkedin_post_id=linkedin_post_id,
                        post_date=post_date_str,
                        weekday=weekday,
                        month=month,
                        year=year,
                        post_text=post_text,
                        media_type=media_type,
                        likes=likes,
                        comments=comments,
                        reposts=reposts,
                        impressions=None,
                        views=None,
                        engagement_rate=0.0,  # Calculated in main/analytics layer
                        post_url=post_url,
                        scraped_at=datetime.utcnow().isoformat()
                    )
                    scraped_posts.append(snapshot)

                logger.info(f"Successfully scraped {len(scraped_posts)} unique posts.")
                return scraped_posts

            except PlaywrightError as e:
                logger.error(f"Playwright error during post scraping: {e}", exc_info=True)
                raise
            except Exception as e:
                logger.error(f"Unexpected error during post scraping: {e}", exc_info=True)
                raise
            finally:
                await context.close()
                await browser.close()
