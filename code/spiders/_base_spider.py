import re
import time
import html
import requests
from bs4 import BeautifulSoup as bs
from exeptions.expeptions import (
    Http403AccessDeniedError,
    Http404NotFoundError,
    Http410GoneError,
    Http301MovedPermanentlyException,
    Http302FoundException,
)
from selenium import webdriver
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

logger = logging.getLogger(__name__)


class BaseSpider:
    def __init__(self, urls):
        self.urls = urls
        self.request_count = 0
        self.session: requests.Session | None = None
        self.last_access_success = False

    @staticmethod
    def _load_headers() -> dict[str, str]:
        """
        ヘッダーを読み込む
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "ja,en-US;q=0.7,en;q=0.3",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
            "Content-Language": "ja-JP",
            "X-Forwarded-For": "126.0.0.1",  # 日本のIPを模倣
        }
        return headers

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=15),
        reraise=True,
    )
    def _get_html(
        self,
        url: str,
        access_delay: float = 1.5,
        allow_redirects: bool = True,
        headers: dict = None,
    ) -> bs:
        """
        HTTPリクエストしてBeautifulSoupオブジェクトに変換する
        """
        if self.request_count == 0 or not self.last_access_success:
            bs = self._session_sp_request(url)
            self.last_access_success = True
            return bs

        self.request_count += 1
        if headers is None:
            headers = self._load_headers()

        time.sleep(access_delay)

        res = self.session.get(
            url,
            headers=headers,
            allow_redirects=allow_redirects,
        )

        if res.status_code == 429:
            retry_after = res.headers.get("Retry-After")
            if retry_after:
                logger.info(f"Retrying after {retry_after} seconds...")
                time.sleep(int(retry_after))
            else:
                logger.info("Retry-After header not found.")

        if res.status_code == 403:
            raise Http403AccessDeniedError(url)

        if res.status_code == 404:
            raise Http404NotFoundError(url)

        if res.status_code == 410:
            raise Http410GoneError(url)

        if res.status_code == 301:
            raise Http301MovedPermanentlyException(url)

        if res.status_code == 302:
            raise Http302FoundException(url)

        if 300 <= res.status_code <= 599:
            raise Exception(
                f"HTTP Error response {res.status_code} content: {res.content}"
            )

        soup = bs(res.content, "html.parser")
        return soup

    def _session_sp_request(self, url: str) -> bs:
        """
        sessionを使ってスクレイピングする
        """
        # セッションを作成してCookieを維持
        session = requests.Session()

        # 日本のブラウザを模倣するヘッダー
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
            "Content-Language": "ja-JP",
            "X-Forwarded-For": "126.0.0.1",  # 日本のIPを模倣
            "Referer": "https://auctions.yahoo.co.jp/",
            "Origin": "https://auctions.yahoo.co.jp",
        }

        # 日本の地域設定を示すCookie
        cookies = {
            "JP_LOCATION": "JP",
            "locale": "ja_JP",
            "country": "jp",
            "language": "ja",
            "region": "JP",
        }

        # Cookieをセッションに追加
        self.cookies = cookies
        session.cookies.update(cookies)

        # 最初にメインページにアクセスして必要なCookieを取得
        main_page_url = "https://auctions.yahoo.co.jp/"
        session.get(main_page_url, headers=headers)

        # 目的のURLにアクセス
        response = session.get(url, headers=headers)
        res_bs = bs(response.content, "html.parser")
        self.session = session

        return res_bs

    def _load_selenium(self) -> webdriver.Chrome:
        """
        Seleniumを使ってページをロードする
        """
        driver = webdriver.Chrome()
        return driver

    @staticmethod
    def clean_html_text(text: str) -> str:
        # HTMLエンティティを通常の文字に変換
        text = html.unescape(text)

        # HTMLタグを削除
        text = re.sub(r"<.*?>", "", text)

        # 不要な空白や改行を整理
        text = re.sub(r"\s+", " ", text)
        return text.strip()
