import logging
from robocorp.tasks import task
from api.utils import export_dataframe
from api.web_scraping import WebScraping
from api.text_processing import TextProcessing

from api.constants import LOGGING_INFO, SEARCH_KEYWORD

@task
def extract_news_data():
    # Set logging level
    logging.basicConfig(level=LOGGING_INFO)

    # Perform the scraping
    scraper = WebScraping()
    df = scraper.scrape_page(search_string=SEARCH_KEYWORD)
    if not df.empty:
        text_processing = TextProcessing()
        df = text_processing.post_process_texts(df)
        export_dataframe(df)
