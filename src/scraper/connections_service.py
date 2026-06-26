import os
import csv
import re
import logging
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple
from playwright.async_api import async_playwright
from src.database.repository import LinkedInRepository
from src.database.models import ConnectionRecord
from src.utils.logger import setup_logger

logger = setup_logger("scraper.connections_service")

class LinkedInConnectionsService:
    """Manages importing LinkedIn connections via CSV files or browser scraping."""

    def __init__(self, repository: LinkedInRepository) -> None:
        """Initializes the service with the database repository.

        Args:
            repository: Database repository instance.
        """
        self.repository = repository
        
        project_root = Path(__file__).resolve().parent.parent.parent
        self.session_path = project_root / "data" / "session.json"
        
        # Search paths for Connections.csv
        self.csv_paths = [
            project_root / "Connections.csv",
            project_root / "data" / "Connections.csv",
            Path(os.getcwd()) / "Connections.csv"
        ]

    def _parse_linkedin_date(self, date_str: str) -> str:
        """Helper to parse typical LinkedIn CSV exported dates to YYYY-MM-DD.

        Args:
            date_str: Raw date string.

        Returns:
            str: Date formatted as YYYY-MM-DD, or original string if parsing fails.
        """
        if not date_str:
            return datetime.utcnow().strftime("%Y-%m-%d")
            
        date_str = date_str.strip()
        # Common formats: "25 Jun 2026", "Jun 25, 2026", "2026-06-25"
        formats = [
            "%d %b %Y",     # 25 Jun 2026
            "%b %d, %Y",    # Jun 25, 2026
            "%Y-%m-%d",     # 2026-06-25
            "%d-%b-%y",     # 25-Jun-26
            "%m/%d/%Y"      # 06/25/2026
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
                
        # If parsing fails, clean it up or return as is
        return date_str

    def _parse_relative_time(self, rel_str: str) -> str:
        """Helper to parse relative time strings (e.g. 'Connected 2 hours ago') to YYYY-MM-DD.

        Args:
            rel_str: Relative time string.

        Returns:
            str: Date formatted as YYYY-MM-DD.
        """
        now = datetime.utcnow()
        if not rel_str:
            return now.strftime("%Y-%m-%d")
            
        rel_str = rel_str.lower().strip()
        
        # Extract digits
        digits = re.findall(r"\d+", rel_str)
        val = int(digits[0]) if digits else 1
        
        if "minute" in rel_str or "hour" in rel_str or "day" in rel_str:
            if "day" in rel_str:
                dt = now - timedelta(days=val)
            else:
                dt = now
            return dt.strftime("%Y-%m-%d")
        elif "week" in rel_str:
            dt = now - timedelta(weeks=val)
            return dt.strftime("%Y-%m-%d")
        elif "month" in rel_str:
            dt = now - timedelta(days=val * 30)
            return dt.strftime("%Y-%m-%d")
        elif "year" in rel_str:
            dt = now - timedelta(days=val * 365)
            return dt.strftime("%Y-%m-%d")
            
        return now.strftime("%Y-%m-%d")

    def detect_and_parse_csv(self) -> Optional[List[ConnectionRecord]]:
        """Checks for local Connections.csv backups and imports them if present.

        Returns:
            Optional[List[ConnectionRecord]]: List of connection records, or None if no CSV found.
        """
        target_csv = None
        for path in self.csv_paths:
            if path.exists():
                target_csv = path
                break
                
        if not target_csv:
            logger.info("No local Connections.csv file detected in workspace search paths.")
            return None
            
        logger.info(f"Auto-detected LinkedIn Connections CSV export file at: {target_csv}")
        records: List[ConnectionRecord] = []
        
        try:
            with open(target_csv, "r", encoding="utf-8") as f:
                # LinkedIn CSVs typically have introductory instructions/metadata lines to skip
                lines = f.readlines()
                
            # Locate the actual headers index
            header_idx = -1
            for idx, line in enumerate(lines[:10]):  # Header is usually in the first few lines
                if "First Name" in line and "Last Name" in line:
                    header_idx = idx
                    break
                    
            if header_idx == -1:
                logger.error("Could not find standard headers in Connections.csv. Importing failed.")
                return []
                
            # Parse rows using csv.DictReader on relevant lines
            csv_reader = csv.DictReader(lines[header_idx:])
            
            for row in csv_reader:
                first_name = row.get("First Name", "").strip()
                last_name = row.get("Last Name", "").strip()
                url = row.get("URL", "").strip()
                company = row.get("Company", "").strip()
                position = row.get("Position", "").strip()
                connected_date_raw = row.get("Connected On", "").strip()
                
                if not first_name or not url:
                    continue
                    
                full_name = f"{first_name} {last_name}".strip()
                connected_date = self._parse_linkedin_date(connected_date_raw)
                
                # Combine Position and Company to create a headline representation
                headline = f"{position} at {company}" if (position and company) else (position or company)
                
                records.append(ConnectionRecord(
                    first_name=first_name,
                    last_name=last_name,
                    full_name=full_name,
                    profile_url=url,
                    headline=headline,
                    company=company,
                    location=None,  # Location not provided in LinkedIn CSV exports
                    connected_date=connected_date,
                    import_source="csv"
                ))
                
            logger.info(f"Successfully parsed {len(records)} connection records from local CSV.")
            return records
            
        except Exception as e:
            logger.error(f"Error parsing local Connections CSV: {e}", exc_info=True)
            return []

    async def scrape_connections_page(self, headless: bool = True) -> List[ConnectionRecord]:
        """Launches Playwright and scrapes connection list from My Network -> Connections page.

        Args:
            headless: Headless browser mode flag.

        Returns:
            List[ConnectionRecord]: List of scraped connection records.
        """
        if not self.session_path.exists():
            logger.warning("Session file does not exist. Cannot scrape connections page.")
            return []
            
        logger.info("Initializing Playwright connections scraper session...")
        records: List[ConnectionRecord] = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            # Create context with saved session
            context = await browser.new_context(storage_state=str(self.session_path))
            page = await context.new_page()
            
            url = "https://www.linkedin.com/mynetwork/invite-connect/connections/"
            logger.info(f"Navigating browser to: {url}...")
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                await asyncio.sleep(5)  # Give time to render
                
                # Check if we are redirected to login (session expired)
                if "login" in page.url or "checkpoint" in page.url:
                    logger.warning("LinkedIn session expired or verification checkpoint triggered. Scraping blocked.")
                    return []
                    
                # Scroll to load connections
                logger.info("Scrolling page to load lazy connections...")
                last_height = await page.evaluate("document.body.scrollHeight")
                
                # Scroll 12 times to fetch ~100-200 connections if present
                for scroll_cycle in range(12):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(2.5)
                    new_height = await page.evaluate("document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
                    
                # Parse connection cards
                # Class list cards usually: li.mn-connection-card or .mn-connection-card
                card_locators = await page.locator("li.mn-connection-card, .mn-connection-card").all()
                logger.info(f"Found {len(card_locators)} connection card elements on page.")
                
                for idx, card in enumerate(card_locators):
                    try:
                        # Extract Name
                        name_elem = card.locator(".mn-connection-card__name, [class*='name']").first
                        name_text = (await name_elem.text_content()).strip() if await name_elem.count() > 0 else "Unknown User"
                        
                        # Extract Profile URL
                        link_elem = card.locator("a[href*='/in/']").first
                        profile_link = (await link_elem.get_attribute("href")) if await link_elem.count() > 0 else ""
                        
                        if not profile_link:
                            continue
                            
                        # Complete URL if relative
                        if profile_link.startswith("/"):
                            profile_link = "https://www.linkedin.com" + profile_link
                            
                        # Split full name into first and last
                        name_parts = name_text.split(" ")
                        first_name = name_parts[0] if name_parts else "Unknown"
                        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
                        
                        # Extract Headline / Occupation
                        occ_elem = card.locator(".mn-connection-card__occupation, [class*='occupation']").first
                        occ_text = (await occ_elem.text_content()).strip() if await occ_elem.count() > 0 else ""
                        
                        # Extract Company from Occupation text if keyword present (e.g. "Software Engineer at Google" -> "Google")
                        company = None
                        if " at " in occ_text:
                            company = occ_text.split(" at ")[-1].strip()
                            
                        # Extract Connected Date relative indicator (e.g. "Connected 3 days ago")
                        time_elem = card.locator(".mn-connection-card__connected-time, time").first
                        time_text = (await time_elem.text_content()).strip() if await time_elem.count() > 0 else ""
                        
                        connected_date = self._parse_relative_time(time_text)
                        
                        records.append(ConnectionRecord(
                            first_name=first_name,
                            last_name=last_name,
                            full_name=name_text,
                            profile_url=profile_link,
                            headline=occ_text,
                            company=company,
                            location=None,  # Location not visible on standard My Network cards
                            connected_date=connected_date,
                            import_source="scrape"
                        ))
                    except Exception as card_err:
                        logger.warning(f"Error parsing card at index {idx}: {card_err}")
                        continue
                        
            except Exception as nav_err:
                logger.error(f"Navigation/Scraping error: {nav_err}", exc_info=True)
                
            finally:
                await browser.close()
                
        return records

    async def execute_connections_import(self) -> Tuple[int, int, str]:
        """Orchestrates connections collection, automatically choosing the best method.

        Returns:
            Tuple[int, int, str]: (inserted_count, skipped_count, source_used)
        """
        # Method 1: Check CSV
        records = self.detect_and_parse_csv()
        source = "csv"
        
        # Method 2: Scrape page if CSV is not found
        if records is None:
            logger.info("CSV export not found. Attempting browser scraping of connections page...")
            try:
                # Use headless=True for background runs
                records = await self.scrape_connections_page(headless=True)
                source = "scrape"
            except Exception as scrape_err:
                logger.error(f"Scraping failed: {scrape_err}")
                records = []
                
        if not records:
            # Report failure details and suggest manual CSV downloads
            logger.warning("No connections were retrieved. Check if session cookie is expired, or export a Connections CSV.")
            return 0, 0, "failed"
            
        # Write connections list to SQLite
        inserted, skipped = self.repository.save_connection_records(records)
        return inserted, skipped, source
