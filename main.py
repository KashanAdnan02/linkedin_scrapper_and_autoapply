import asyncio
import logging
from config import Config
from scraper.linkedin import LinkedInScraper
from scraper.indeed import IndeedScraper

logger = logging.getLogger(__name__)

async def run_scrapers():
    Config.ensure_directories()
    
    keywords = Config.SEARCH_KEYWORDS
    location = Config.LOCATION
    max_pages = 1

    scrapers = [
        LinkedInScraper(),
        IndeedScraper(),
    ]

    all_jobs = []
    for scraper in scrapers:
        try:
            logger.info(f"Starting scraper: {scraper.__class__.__name__}")
            jobs = await scraper.scrape_jobs(keywords, location, max_pages=max_pages)
            all_jobs.extend(jobs)
            logger.info(f"{scraper.__class__.__name__} completed: {len(jobs)} jobs found")
        except Exception as e:
            logger.error(f"Error in {scraper.__class__.__name__}: {e}")
        finally:
            await scraper.close()

    logger.info(f"\n=== Scraping Summary ===\nTotal jobs saved: {len(all_jobs)}")
    return all_jobs

if __name__ == "__main__":
    try:
        asyncio.run(run_scrapers())
    except KeyboardInterrupt:
        logger.info("Scraping stopped by user.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")