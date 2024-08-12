import re
import os
import requests
import pandas as pd
from datetime import datetime, timedelta

from api.constants import OUTPUT_FOLDER

def parse_date(timestamp:str) -> str:
    # get base datetime = Today
    today_datetime = datetime.now()

    # If news published some minutes ago
    if 'min ago' in timestamp.lower() or 'mins ago' in timestamp.lower():
        return (today_datetime - timedelta(
            minutes=int(timestamp.split(' ')[0]))).isoformat()

    # If news published some hours ago
    if 'hours ago' in timestamp.lower() or 'hour ago' in timestamp.lower():
        return (today_datetime - timedelta(
            hours=int(timestamp.split(' ')[0]))).isoformat()

    # If news published yesterday
    if 'yesterday' in timestamp.lower():
        return (today_datetime - timedelta(days=1)).isoformat()

    # For other dates, include Year if it is not present
    if not re.search('[0-9]{4}^', timestamp):
        timestamp = f'{timestamp.lstrip()}, {today_datetime.strftime("%Y")}'

    # Returned parsed date, or error message
    try:
        return datetime.strptime(timestamp, '%B %d, %Y').isoformat()
    except:
        return f'Error processing date: {timestamp}'


def download_image(news_url:str, img_src:str) -> str:
    img_folder = os.path.join(OUTPUT_FOLDER, 'IMGS')
    if not os.path.exists(img_folder):
        os.makedirs(img_folder)

    img_filename = f'{news_url.split("/")[-1]}.png'
    with open(os.path.join(img_folder, img_filename),
              'wb') as handler:
        handler.write(requests.get(img_src).content)
    return img_filename


def export_dataframe(df:pd.DataFrame) -> None:
    df.to_excel(
        os.path.join(
            OUTPUT_FOLDER,
            f'Execution_{datetime.now().strftime("%Y%m%d-%H%M%S")}.xlsx'),
        index=False)