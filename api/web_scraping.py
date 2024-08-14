import logging
import pandas as pd
from selenium import webdriver
from RPA.Browser.Selenium import Selenium
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tenacity import (retry, retry_if_exception_type,
                      stop_after_attempt, wait_random)

from api.utils import parse_date, download_image, continue_by_time_period
from api.constants import BASE_URL, TIMEOUT_SECONDS, CATEGORY_FILTER


class WebScrapingError(Exception):
    # to do: improve error handling
    pass


class WebScraping:

    def __init__(self):
        self.driver = None
        self.logger = logging.getLogger(__name__)
        self.continue_scraping = True


    def set_chrome_options(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-web-security')
        options.add_argument('--start-maximized')        
        options.add_argument('--remote-debugging-port=9222')
        options.add_experimental_option('excludeSwitches',
                                        ['enable-logging'])
        return options


    @retry(reraise=True, retry=retry_if_exception_type(WebScrapingError),
           stop=stop_after_attempt(3), wait=wait_random(min=1, max=3))
    def open_webdriver(self):
        try:
            self.browser = Selenium()
            self.browser.set_selenium_timeout(TIMEOUT_SECONDS)
            self.logger.debug('Opening Browser Chrome and loading Page')
            self.browser.open_available_browser(
                browser_selection='Chrome',
                url=BASE_URL,
                options=self.set_chrome_options())
            self.logger.debug('Finished opening Web Page')
        except Exception as error:
            logging.exception(error)
            raise WebScrapingError


    def disable_popup_overlay(self):
        try:
            WebDriverWait(self.browser.driver, TIMEOUT_SECONDS).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR,
                     '#onetrust-accept-btn-handler')))
        except:
            logging.info('Skipping closing Advertisement Popup')

        try:
            self.browser.click_element_when_clickable(
                'class=fancybox-item.fancybox-close')
        except:
            logging.info('Skipping closing Fancybox Popup')


    @retry(reraise=True, retry=retry_if_exception_type(WebScrapingError),
           stop=stop_after_attempt(3), wait=wait_random(min=1, max=3))
    def add_category_filter(self) -> None:
        try:
            logging.info(f'Applying Category filter: {CATEGORY_FILTER}')

            # Refresh page after latest operations
            self.browser.driver.refresh()

            # Disable Popup overlay, if it exists
            self.disable_popup_overlay()

            # Open Filters
            self.browser.click_element_when_visible(
                'class=SearchResultsModule-filters-open')

            # Expand Categories
            self.browser.click_element_when_visible(
                'class=SearchFilter-content')

            # Iterate over categories
            categories_result = self.browser.find_elements(
                'class=CheckboxInput-label')

            # Click on the expected one
            for category in categories_result:
                if CATEGORY_FILTER in str(category.text).lower():
                    category.click()
                    logging.info(f'Checked filter: {category.text}')

            # Apply filter (works even when no checkbox was selected)
            self.browser.click_element_when_visible(
                'class=SearchResultsModule-filters-applyButton')

            logging.info(f'Applied Category filter: {CATEGORY_FILTER}')
        except Exception as error:
            logging.exception(error)
            raise WebScrapingError


    @retry(reraise=True, retry=retry_if_exception_type(WebScrapingError),
           stop=stop_after_attempt(3), wait=wait_random(min=1, max=3))
    def go_to_next_page(self) -> None:
        logging.info('Not achieved Month threshold, go to next page')
        try:
            self.browser.click_element_when_visible(
                'class=Pagination-nextPage')
        except Exception as error:
            logging.exception(error)
            self.browser.driver.refresh()
            raise WebScrapingError


    @retry(reraise=True, retry=retry_if_exception_type(WebScrapingError),
           stop=stop_after_attempt(3), wait=wait_random(min=1, max=3))
    def perform_search(self, search_string:str) -> None:
        try:
            logging.info('Performing Search')

            # Disable Popup overlay, if it exists
            self.disable_popup_overlay()

            # Click on magnifying glass
            self.browser.click_element_when_visible(
                'class=SearchOverlay-search-button')

            # Input search string and submit
            self.browser.input_text_when_element_is_visible(
                'class=SearchOverlay-search-input', search_string)
            self.browser.click_element_when_visible(
                'class=SearchOverlay-search-submit')

            # Sort by Newest
            logging.info('Applying Newest sorting')
            sort_by_droplist = self.browser.find_element(
                'class=Select-input')
            select = Select(sort_by_droplist)
            select.select_by_visible_text('Newest')
            logging.info('Applied Newest sorting')
        except Exception as error:
            logging.exception(error)
            self.browser.go_to(BASE_URL)
            raise WebScrapingError


    @retry(reraise=True, retry=retry_if_exception_type(WebScrapingError),
           stop=stop_after_attempt(3), wait=wait_random(min=1, max=3))
    def process_results(self) -> pd.DataFrame:
        try:
            # Refresh page so the Timestamps appears
            self.browser.driver.refresh()

            # Disable Popup overlay, if it exists
            self.disable_popup_overlay()

            # Wait for the search results to appear
            WebDriverWait(self.browser.driver, TIMEOUT_SECONDS).until(
                EC.visibility_of_element_located(
                    (By.CLASS_NAME, 'SearchResultsModule-results')))

            # Get Query Results
            search_result = self.browser.find_element(
                'class=SearchResultsModule-results')
            retrieved_news = search_result.find_elements(
                by=By.CLASS_NAME, value='PagePromo')
            logging.info(f'Retrieved {len(retrieved_news)} news from search')

            # Parse Results
            parsed_news = list()
            for news in retrieved_news:
                parsed_new_row = dict()

                parsed_new_row['URL'] = str(
                    news.find_element(by=By.CLASS_NAME,
                                    value='Link').get_attribute('href')
                    )

                parsed_new_row['Title'] = str(news.get_attribute('data-gtm-region'))
                
                # News Description (sometimes do no exists)
                try:
                    parsed_new_row['Description'] = str(news.find_element(
                        by=By.CLASS_NAME, value='PagePromo-description').text)
                except Exception as error:
                    parsed_new_row['Description'] = ''

                # Download and save image (sometimes do no exists)
                try:
                    parsed_new_row['Image'] = download_image(
                        parsed_new_row['URL'],
                        news.find_element(by=By.CLASS_NAME,
                                          value='Image').get_attribute('src'))
                except Exception:
                    parsed_new_row['Image'] = 'Image Not Found'

                # Parse News DateTime (default not found)
                try:
                    parsed_new_row['DateTime'] = parse_date(news.find_element(
                        by=By.CLASS_NAME, value='Timestamp-template-now').text)
                except Exception:
                    try:
                        # Retry with older timestamp template
                        parsed_new_row['DateTime'] = parse_date(news.find_element(
                            by=By.CLASS_NAME, value='Timestamp-template').text)
                    except Exception:
                        parsed_new_row['DateTime'] = 'DateTime Not Found'
        
                # Append parsed row to DataFrame
                parsed_news.append(parsed_new_row)

            logging.info(f'Finished Parsing Web Page')
            return pd.DataFrame(parsed_news)
        except Exception as error:
            logging.exception(error)
            raise WebScrapingError


    def scrape_pages(self, search_string:str):
        logging.info('Starting Scraping the Page')
        self.open_webdriver()

        logging.info('Performing Search on Page')
        self.perform_search(search_string)

        logging.info('Add Categories filter')
        try:
            self.add_category_filter()
        except Exception as error:
            logging.exception(error)
            logging.info('Error when applying filters. '\
                         'Running without filters applied.')

        page_number = 1
        df = pd.DataFrame()
        while self.continue_scraping:
            logging.info(f'Processing Search Result page {page_number}')
            try:
                # Process Page
                df_page = self.process_results()
                # Combine Page results with current results
                df = pd.concat([df, df_page], ignore_index=True)

                # Check months limit
                self.continue_scraping = continue_by_time_period(df_page)
                if self.continue_scraping:
                    self.go_to_next_page()
                    page_number += 1
            except Exception as error:
                # if error or last page, stop appending DataFrames
                logging.exception(error)
        return df
