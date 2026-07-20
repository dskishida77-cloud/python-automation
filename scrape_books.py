"""books.toscrape.com から書籍タイトル・価格・在庫状況を収集し、Markdownに出力する。"""

import logging
import random
import sys
import time
import urllib.robotparser
from datetime import date
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/"
CATALOGUE_URL_TEMPLATE = urljoin(BASE_URL, "catalogue/page-{}.html")
USER_AGENT = "books-scraper/1.0"
REQUEST_TIMEOUT = 10
MIN_DELAY_SEC = 1
MAX_DELAY_SEC = 3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def load_robot_parser(session: requests.Session) -> urllib.robotparser.RobotFileParser:
    robots_url = urljoin(BASE_URL, "robots.txt")
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        response = session.get(robots_url, timeout=REQUEST_TIMEOUT)
        if response.status_code == 404:
            logger.info("robots.txtが存在しないため、全ページアクセス可能として扱います。")
            rp.parse([])
        else:
            response.raise_for_status()
            rp.parse(response.text.splitlines())
    except requests.exceptions.RequestException as exc:
        logger.warning("robots.txtの取得に失敗しました。全ページ許可として扱います: %s", exc)
        rp.parse([])
    return rp


def ensure_allowed(rp: urllib.robotparser.RobotFileParser, url: str) -> None:
    if not rp.can_fetch(USER_AGENT, url):
        logger.error("robots.txtにより許可されていないためアクセスを中止します: %s", url)
        sys.exit(1)


def fetch_page(session: requests.Session, url: str) -> str:
    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        logger.error("接続エラーが発生しました: %s (%s)", url, exc)
        sys.exit(1)
    response.encoding = response.apparent_encoding
    return response.text


def parse_books(html: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    books = []
    for article in soup.select("article.product_pod"):
        title = article.h3.a["title"].strip()
        price = article.select_one("p.price_color").get_text(strip=True)
        availability = article.select_one("p.instock.availability").get_text(strip=True)
        books.append({"title": title, "price": price, "availability": availability})
    return books


def has_next_page(html: str) -> bool:
    soup = BeautifulSoup(html, "html.parser")
    return soup.select_one("li.next a") is not None


def write_markdown(books: list[dict[str, str]], output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# books.toscrape.com 書籍一覧\n\n")
        f.write(f"取得日: {date.today().isoformat()}\n\n")
        f.write(f"件数: {len(books)}\n\n")
        f.write("| タイトル | 価格 | 在庫状況 |\n")
        f.write("|---|---|---|\n")
        for book in books:
            title = book["title"].replace("|", "\\|")
            f.write(f"| {title} | {book['price']} | {book['availability']} |\n")


def main() -> None:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    rp = load_robot_parser(session)

    all_books: list[dict[str, str]] = []
    page = 1
    while True:
        url = CATALOGUE_URL_TEMPLATE.format(page)
        ensure_allowed(rp, url)

        logger.info("取得中: %s", url)
        html = fetch_page(session, url)
        all_books.extend(parse_books(html))

        if not has_next_page(html):
            break

        page += 1
        time.sleep(random.uniform(MIN_DELAY_SEC, MAX_DELAY_SEC))

    output_path = f"books_{date.today().strftime('%Y%m%d')}.md"
    write_markdown(all_books, output_path)
    logger.info("完了しました: %s (%d件)", output_path, len(all_books))


if __name__ == "__main__":
    main()
