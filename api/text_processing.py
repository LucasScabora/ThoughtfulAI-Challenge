import re
import logging
import pandas as pd
from api.constants import SEARCH_KEYWORD

class TextProcessing:

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def count_search_phrases(self, df:pd.DataFrame) -> pd.DataFrame:
        df['#Search Phrase Matches'] = df.apply(
            lambda row: len(
                re.findall(rf'\b{SEARCH_KEYWORD}\b',
                           row['Title'] + ' ' + row['Description'],
                           re.IGNORECASE)),
                           axis=1)
        return df

    def check_money_text(self, df:pd.DataFrame) -> pd.DataFrame:
        # pattern for $11.1 or $111,111.11
        money_pattern = r'(\$[0-9]+\,?[0-9]*\.?[0-9]*)' 
        # pattern for 11 dollars
        money_pattern = fr'{money_pattern}|([0-9]+ dollars)'
        # pattern for 11 USD
        money_pattern = fr'{money_pattern}|([0-9]+ USD)'

        df['Contains Money'] = df.apply(
            lambda row: bool(
                re.search(money_pattern,
                          row['Title'] + ' ' + row['Description'])),
                          axis=1)
        return df

    def post_process_texts(self, df:pd.DataFrame) -> pd.DataFrame:
        self.logger.info('Adding column "#Search Phrase Matches"')
        df = self.count_search_phrases(df)

        self.logger.info('Adding column "Contains Money"')
        df = self.check_money_text(df)
        return df