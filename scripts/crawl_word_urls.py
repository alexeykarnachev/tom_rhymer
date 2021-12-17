import argparse
import asyncio
import logging
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from common import Requester

_logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

_BASE_URL = 'https://ru.wiktionary.org/'
_START_URL = 'https://ru.wiktionary.org/w/index.php?title=%D0%9A%D0%B0%D1%82%D0%B5%D0%B3%D0%BE%D1%80%D0%B8%D1%8F:%D0%A0%D1%83%D1%81%D1%81%D0%BA%D0%B8%D0%B9_%D1%8F%D0%B7%D1%8B%D0%BA&from=%D0%B0'


def _parse_args():
    parser = argparse.ArgumentParser(description='Crawls russian word urls from wiktionary.')
    parser.add_argument('--out-file-path', '-o', type=str, required=True, help='Output path to save word urls.')
    return parser.parse_args()


def main(out_file_path):
    requester = Requester(
        concurrency=1,
        timeout=1,
        n_retries=10,
    )
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_run(requester, out_file_path))


async def _run(requester: Requester, out_file_path):
    url = _START_URL
    n_urls = 0
    with open(out_file_path, 'w') as out_file:
        while True:
            page_text = await requester.get(url)
            soup = BeautifulSoup(page_text, 'html.parser')
            word_urls = [e.find('a').get('href') for e in soup.find_all('div', {'id': 'mw-pages'})[-1].find_all('li')]
            word_urls = [urljoin(_BASE_URL, url) for url in word_urls]
            for word_url in word_urls:
                out_file.write(word_url)
                out_file.write('\n')
            n_urls += len(word_urls)
            _logger.info(f'Word urls: {n_urls}')
            next_page_elems = soup.find_all('a', string='Следующая страница')
            if not (next_page_elems):
                break
            url = urljoin(_BASE_URL, next_page_elems[-1].get('href'))


if __name__ == '__main__':
    args = _parse_args()
    main(out_file_path=args.out_file_path)
