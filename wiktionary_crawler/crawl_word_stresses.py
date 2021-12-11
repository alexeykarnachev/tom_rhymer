import argparse
import asyncio
import logging
import re
from itertools import chain
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from common import Requester

_logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
_COUNTER = 0


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--word-urls-file-path', '-u', type=str, required=True)
    parser.add_argument('--out-file-path', '-o', type=str, required=True)
    return parser.parse_args()


def main(word_urls_file_path, out_file_path):
    requester = Requester(
        concurrency=10,
        timeout=5,
        n_retries=5,
    )
    loop = asyncio.get_event_loop()
    cor = _run(
        requester=requester,
        word_urls_file_path=word_urls_file_path,
        out_file_path=out_file_path,
    )
    loop.run_until_complete(cor)


async def _run(requester: Requester, word_urls_file_path, out_file_path):
    out_file_path = Path(out_file_path)
    with open(word_urls_file_path) as inp_file:
        word_urls = set(url.strip() for url in inp_file.readlines())
    cors = [_crawl_word(requester, url, out_file_path) for url in word_urls]
    if out_file_path.exists():
        out_file_path.unlink()
    await asyncio.gather(*cors)


async def _crawl_word(requester: Requester, url, out_file_path):
    page_text = await requester.get(url)
    soup = BeautifulSoup(page_text)
    word = soup.find('h1', {'id': 'firstHeading'}).text.lower().strip()
    global _COUNTER
    _COUNTER += 1
    _logger.info(f'[{_COUNTER}] Crawling "{word}" at {url}')
    if re.search(r'\s+', word):
        return {}
    table = soup.find('table', {'class': 'morfotable ru'})
    if not table:
        return {word} if _is_stressed(word) else {}
    cells = table.find_all('td')
    cells = [c for c in cells if c.get('bgcolor', '#ffffff') == '#ffffff']
    words = [cell.get_text(separator='\n').strip().lower() for cell in cells]
    words = list(chain(*[re.split('\n| |/', word) for word in words]))
    words = [re.sub(r'\(.*?\)', '', word).strip() for word in words]
    words = [word for word in words if _is_stressed(word)]
    words = set(words)
    if words:
        with open(out_file_path, "a") as out_file:
            words = '\n'.join(words) + '\n'
            out_file.write(words)


def _is_stressed(word):
    word = word.lower()
    if 'ё' in word:
        return True
    if len(re.findall('[уеыаоэяию]', word)) == 1:
        return True
    if b'\u0301' in word.encode('unicode_escape'):
        return True
    return False


if __name__ == '__main__':
    args = _parse_args()
    main(
        word_urls_file_path=args.word_urls_file_path,
        out_file_path=args.out_file_path,
    )
    # word_urls_file_path = '/ssd_1/data/wiktionary/word_urls.txt'
    # out_file_path = '/ssd_1/data/wiktionary/word_stresses.txt'
    # main(
    #     word_urls_file_path=word_urls_file_path,
    #     out_file_path=out_file_path,
    # )
