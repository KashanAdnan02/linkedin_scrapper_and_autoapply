# scraper/__init__.py

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import Config
from database.mongodb import JobDatabase
from playwright.async_api import async_playwright
import asyncio
from fake_useragent import UserAgent
import random
from bs4 import BeautifulSoup
from datetime import datetime
import logging

logging.basicConfig(level=getattr(logging, Config.LOG_LEVEL, logging.INFO))
logger = logging.getLogger(__name__)

ua = UserAgent()

class BaseScraper:
    def __init__(self):
        self.db = JobDatabase()
        self.browser = None
        self.context = None
        self.playwright = None

    async def init_browser(self, headless: bool = None):
        if headless is None:
            headless = Config.HEADLESS

        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ]
        )
        self.context = await self.browser.new_context(
            user_agent=ua.random,
            viewport={'width': 1920, 'height': 1080},
            locale='en-US'
        )
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        """)
        logger.info(f"Browser initialized (headless={headless})")

    async def close(self):
        """Graceful shutdown to reduce event loop warnings."""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.warning(f"Error during browser close: {e}")
        finally:
            self.context = None
            self.browser = None
            self.playwright = None
        logger.info("Browser resources released.")

    async def random_delay(self, min_sec: float = None, max_sec: float = None):
        if min_sec is None:
            min_sec = Config.RANDOM_DELAY_MIN
        if max_sec is None:
            max_sec = Config.RANDOM_DELAY_MAX
        delay = random.uniform(min_sec, max_sec)
        logger.debug(f"Random human-like delay: {delay:.2f}s")
        await asyncio.sleep(delay)

    def save_job(self, job_data: dict):
        """
        Save a job to the database while preventing duplicates based on job_id.
        """
        try:
            if not job_data.get("job_id"):
                logger.warning("Job data missing job_id. Skipping save.")
                return

            # Check if job already exists
            existing_job = self.db.get_job_by_id(job_data["job_id"])
            
            if existing_job:
                logger.info(f"Duplicate job skipped: {job_data['job_id']} - {job_data.get('title', '')}")
                return  # Do not save duplicate

            # Set default fields only for new jobs
            job_data.setdefault("status", "pending")
            job_data.setdefault("applied_date", None)
            job_data.setdefault("source", self.__class__.__name__.replace("Scraper", "").lower())
            job_data.setdefault("timestamp", datetime.utcnow())

            self.db.save_job(job_data)
            logger.info(f"Job saved successfully: {job_data['job_id']} - {job_data.get('title', '')}")

        except Exception as e:
            logger.error(f"Failed to save job {job_data.get('job_id')}: {e}")