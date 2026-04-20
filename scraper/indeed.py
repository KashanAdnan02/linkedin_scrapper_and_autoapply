from . import BaseScraper
from config import Config
from bs4 import BeautifulSoup

class IndeedScraper(BaseScraper):
    async def scrape_jobs(self, keywords: list, location: str, max_pages: int = 5):
        if not self.browser:
            await self.init_browser(headless=Config.HEADLESS)

        page = await self.context.new_page()
        all_jobs = []

        for keyword in keywords:
            for page_num in range(max_pages):
                url = f"https://www.indeed.com/jobs?q={keyword.replace(' ', '+')}&l={location.replace(' ', '+')}&radius=25&start={page_num * 10}"
                
                await page.goto(url, wait_until="domcontentloaded")
                await self.random_delay(4, 8)

                content = await page.content()
                soup = BeautifulSoup(content, 'lxml')
                job_cards = soup.select("div.job_seen_beacon")
                for card in job_cards:
                    try:
                        title_tag = card.select_one("h2.jobTitle a")
                        link = title_tag["href"] if title_tag else None
                        company_tag = card.select_one('span[data-testid="company-name"]')
                        location_tag = card.select_one('div[data-testid="text-location"]')
                        if not company_tag:
                            company_tag = card.select_one("span.companyName")
                        if not location_tag:
                            location_tag = card.select_one("div.companyLocation")

                        job_data = {
                            "job_id": link.split("jk=")[1].split("&")[0] if link else None,
                            "title": title_tag.get_text(strip=True) if title_tag else None,
                            "company": company_tag.get_text(strip=True) if company_tag else None,
                            "location": location_tag.get_text(strip=True) if location_tag else None,
                            "url": "https://www.indeed.com" + link if link else None,
                        }
                        if job_data["title"] and job_data["url"]:
                            all_jobs.append(job_data)
                            self.save_job(job_data)
                    except Exception:
                        continue

                print(f"Indeed: Scrapping'")

        await page.close()
        return all_jobs