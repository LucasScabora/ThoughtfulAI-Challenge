from robocorp.tasks import task
from api.web_scraping import WebScraping
from api.utils import export_dataframe

@task
def extract_news_data():
    scraper = WebScraping()
    df = scraper.scrape_page(search_string='finance')
    if not df.empty:
        export_dataframe(df)
