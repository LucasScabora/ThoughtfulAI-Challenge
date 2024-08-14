import re
import os
import logging
import requests
import pandas as pd
from datetime import datetime, timedelta

from api.constants import OUTPUT_FOLDER, MONTHS_PERIOD


def parse_date(timestamp:str) -> str:
    # Remove spaces from the start/end of string
    timestamp = timestamp.strip()

    # get base datetime = Today
    today_datetime = datetime.now()

    # If news published some minutes ago
    if 'min ago' in timestamp.lower() or 'mins ago' in timestamp.lower():
        return (today_datetime - timedelta(
            minutes=int(timestamp.split(' ')[0]))).isoformat(
                timespec='minutes')

    # If news published some hours ago
    if 'hours ago' in timestamp.lower() or 'hour ago' in timestamp.lower():
        return (today_datetime - timedelta(
            hours=int(timestamp.split(' ')[0]))).isoformat(
                timespec='minutes')

    # If news published yesterday
    if 'yesterday' in timestamp.lower():
        return (today_datetime - timedelta(days=1)).isoformat(
            timespec='minutes')

    # For other dates, include Year if it is not present
    if timestamp and not re.search('[0-9]{4}^', timestamp):
        timestamp = f'{timestamp.lstrip()}, {today_datetime.strftime("%Y")}'

    # Returned parsed date, or error message
    try:
        return datetime.strptime(timestamp, '%B %d, %Y').isoformat(
            timespec='minutes')
    except Exception:
        logging.warning(f'Error processing date: {timestamp}')
        return 'Error processing date'


def download_image(news_url:str, img_src:str) -> str:
    img_folder = os.path.join(OUTPUT_FOLDER, 'IMGS')
    if not os.path.exists(img_folder):
        os.makedirs(img_folder)

    img_filename = f'{news_url.split("/")[-1]}.png'
    with open(os.path.join(img_folder, img_filename),
              'wb') as handler:
        handler.write(requests.get(img_src).content)
    return img_filename


def continue_by_time_period(df:str) -> bool:
    # Get earliest datetime row with valid date
    df_filtered = df[(df['DateTime'] != 'DateTime Not Found') &
                     (~df['DateTime'].str.contains('Error'))]
    if df_filtered.empty:
        return True  # should continue (none valid date found on page)
    earliest_datetime = df_filtered.iloc[-1]['DateTime']
    logging.debug('DateTime from Latest News in page: ' \
                  f'{earliest_datetime}')
    
    # Compute difference in Months
    current_date = datetime.now()
    earliest_date = datetime.fromisoformat(earliest_datetime)
    diff_in_months = int(
        (current_date.year - earliest_date.year) * 12 +
         current_date.month - earliest_date.month)

    # should finish if period = 0, and 1 on more Month of diff
    if MONTHS_PERIOD == 0 and diff_in_months > 0:
        return False
    # should finish if period > 0, and Months computed diff >= period
    if MONTHS_PERIOD > 0 and diff_in_months >= MONTHS_PERIOD:
        return False
    # otherwise, continue
    return True


def export_dataframe(df:pd.DataFrame) -> None:
    df.to_excel(
        os.path.join(
            OUTPUT_FOLDER,
            f'Execution_{datetime.now().strftime("%Y%m%d-%H%M%S")}.xlsx'),
        index=False)