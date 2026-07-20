"""Playwrightを使い、quotes.toscrape.com/js から名言テキスト・著者名を収集する。

結果はMarkdown(quotes_YYYYMMDD.md)とページのスクリーンショット
(quotes_YYYYMMDD.png)として保存する。ブラウザは画面表示(headed)で起動する。
"""

import logging
import random
import sys
import time
import urllib.robotparser
from datetime import date
from urllib.parse import urljoin

import requests
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

BASE_URL = "https://quotes.toscrape.com/"
TARGET_URL = urljoin(BASE_URL, "js")
USER_AGENT = "quotes-scraper/1.0"
REQUEST_TIMEOUT = 10
NAV_TIMEOUT_MS = 15000
MIN_DELAY_SEC = 1
MAX_DELAY_SEC = 3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def load_robot_parser() -> urllib.robotparser.RobotFileParser:
    robots_url = urljoin(BASE_URL, "robots.txt")
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        response = requests.get(
            robots_url,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        )
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


def parse_quotes(page) -> list[dict[str, str]]:
    quotes = []
    for quote_el in page.locator(".quote").all():
        text = quote_el.locator(".text").inner_text().strip()
        author = quote_el.locator(".author").inner_text().strip()
        quotes.append({"text": text, "author": author})
    return quotes


def write_markdown(quotes: list[dict[str, str]], output_path: str, source_url: str) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# quotes.toscrape.com/js 名言一覧\n\n")
        f.write(f"取得元: {source_url}\n\n")
        f.write(f"取得日: {date.today().isoformat()}\n\n")
        f.write(f"件数: {len(quotes)}\n\n")
        for quote in quotes:
            text = quote["text"].replace("\n", " ")
            f.write(f"> {text}\n")
            f.write(f"> — {quote['author']}\n\n")


def main() -> None:
    rp = load_robot_parser()
    ensure_allowed(rp, TARGET_URL)

    today_str = date.today().strftime("%Y%m%d")
    md_path = f"quotes_{today_str}.md"
    png_path = f"quotes_{today_str}.png"

    time.sleep(random.uniform(MIN_DELAY_SEC, MAX_DELAY_SEC))

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            try:
                page = browser.new_page(user_agent=USER_AGENT)
                page.set_default_navigation_timeout(NAV_TIMEOUT_MS)
                logger.info("取得中: %s", TARGET_URL)
                page.goto(TARGET_URL, wait_until="networkidle")
                page.wait_for_selector(".quote", timeout=NAV_TIMEOUT_MS)

                quotes = parse_quotes(page)
                page.screenshot(path=png_path, full_page=True)
            finally:
                browser.close()
    except PlaywrightError as exc:
        logger.error("接続エラーが発生しました: %s (%s)", TARGET_URL, exc)
        sys.exit(1)

    write_markdown(quotes, md_path, TARGET_URL)
    logger.info("完了しました: %s / %s (%d件)", md_path, png_path, len(quotes))


if __name__ == "__main__":
    main()
