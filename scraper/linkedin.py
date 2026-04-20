from . import BaseScraper
from config import Config
from urllib.parse import quote
from bs4 import BeautifulSoup
import asyncio


class LinkedInScraper(BaseScraper):

    async def scrape_jobs(self, keywords: list[str], location: str, max_pages: int = 3):
        if not self.browser:
            await self.init_browser(headless=Config.HEADLESS)
        all_jobs = []
        page = await self.context.new_page()
        try:
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
            })
            for keyword in keywords:
                for page_num in range(max_pages):
                    encoded_keyword = quote(keyword.strip())
                    encoded_location = quote(location.strip())
                    url = (f"https://www.linkedin.com/jobs/search/"
                           f"?keywords={encoded_keyword}"
                           f"&location={encoded_location}"
                           f"&start={page_num * 25}")
                    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    await self.random_delay(4, 8)
                    await self._scroll_page(page)
                    content = await page.content()
                    soup = BeautifulSoup(content, "lxml")
                    job_cards = soup.select("div.base-card, div.jobs-search__results-list > li")
                    for card in job_cards:
                        job_data = self._parse_job_card(card)
                        if job_data and job_data.get("title") and job_data.get("url"):
                            if not any(j["url"] == job_data["url"] for j in all_jobs):
                                all_jobs.append(job_data)
                                self.save_job(job_data)
        finally:
            await page.close()
        return all_jobs

    async def _scroll_page(self, page):
        await page.evaluate("""
            async () => {
                let currentScroll = 0;
                const scrollHeight = document.body.scrollHeight;
                while (currentScroll < scrollHeight * 0.85) {
                    window.scrollBy(0, 800);
                    currentScroll += 800;
                    await new Promise(r => setTimeout(r, 400));
                }
            }
        """)
        await asyncio.sleep(2)

    def _parse_job_card(self, card):
        try:
            title_tag = card.select_one("h3.base-search-card__title, h3.job-card-list__title")
            company_tag = card.select_one("h4.base-search-card__subtitle, h4.job-card-container__company-name")
            location_tag = card.select_one("span.job-search-card__location, span.job-card-container__metadata-item")
            link_tag = card.select_one("a.base-card__full-link")
            list_date_tag = card.select_one("time.job-search-card__listdate, span.job-card-container__listed-time")
            url = link_tag.get("href") if link_tag else None
            if url and not url.startswith("http"):
                url = "https://www.linkedin.com" + url
            
            return {
                "job_id": link_tag["href"].split("?")[0].split("-")[-1] if link_tag else None,
                "title": title_tag.get_text(strip=True) if title_tag else None,
                "company": company_tag.get_text(strip=True) if company_tag else None,
                "location": location_tag.get_text(strip=True) if location_tag else None,
                "url": url,
                "list_date": list_date_tag.get_text(strip=True) if list_date_tag else None,
            }
        except Exception:
            return None