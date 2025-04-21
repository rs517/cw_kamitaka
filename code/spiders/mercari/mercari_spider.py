from spiders._base_spider import BaseSpider
from selenium.webdriver.common.by import By
import time
import logging
from selenium.webdriver.support.ui import WebDriverWait

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException
import re
from tenacity import retry, stop_after_attempt, wait_exponential

# ロギングの基本設定を追加
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


class MercariSpider(BaseSpider):
    def __init__(self, urls):
        super().__init__(urls)

    def run(self):
        self.driver = self._load_selenium()
        scraped_data = self.crawl_urls()
        return scraped_data

    def crawl_urls(self):
        scraped_data = []
        total_urls = len(self.urls)
        for i, url in enumerate(self.urls, 1):
            try:
                logger.info(
                    f"Scraping URL {i}/{total_urls} ({i/total_urls*100:.1f}%): {url}"
                )
                scraped_data.append(self._scrape(url))
                logger.info(
                    f"Successfully scraped URL {i}/{total_urls} ({i/total_urls*100:.1f}%)"
                )
            except Exception as e:
                scraped_data.append(
                    {
                        "original_url": url,
                    }
                )
                logger.error(
                    f"Error scraping URL {i}/{total_urls} ({i/total_urls*100:.1f}%): {url} - {e}"
                )
                continue
        if total_urls > 0:
            success_rate = len(scraped_data) / total_urls * 100
            logger.info(
                f"Completed scraping {len(scraped_data)}/{total_urls} URLs ({success_rate:.1f}% success rate)"
            )
        else:
            logger.info(
                f"No URLs to scrape. Completed with {len(scraped_data)} results."
            )
        return scraped_data

    def determine_page_type(self, url: str) -> str:
        """
        商品のURLに基づいてページタイプを決定します。
        """
        url_to_page_type = {
            "/item/": "customer_posting",
            "/products/": "mercari_shops_posting",
            "/shops/product/": "mercari_shops_posting",
            "https://jp.mercari.com/search": "listing_page",
        }

        for fragment, page_type in url_to_page_type.items():
            if fragment in url:
                return page_type

        # 既知のパターンに合致しない場合はデフォルトのページタイプを返すが、アラートも鳴らす
        logger.error(f"Unknown page type for URL: {url}")
        return "customer_posting"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=15),
        reraise=True,
    )
    def _scrape(self, url: str):
        self.driver.get(url)
        self.driver.implicitly_wait(5)

        wait = WebDriverWait(self.driver, 10)
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "[data-testid='price'],[data-testid='product-price']")
            )
        )

        page_type = self.determine_page_type(url)

        # A列.商品画像
        image_urls = self._extract_img_urls(page_type)

        # B列.URLはそのままurlを使う

        # C列.商品価格
        price = int(
            re.sub(
                r"\D",
                "",
                self.driver.find_element(
                    By.CSS_SELECTOR,
                    "[data-testid='price'],[data-testid='product-price']",
                )
                .get_attribute("textContent")
                .strip(),
            )
        )

        # D列.商品タイトル
        title = (
            self.driver.find_element(By.CSS_SELECTOR, "h1[class*=heading__]")
            .get_attribute("textContent")
            .strip()
        )

        # 発送元の地域
        shipping_region = self._extract_shipping_region()

        # E列.商品説明文
        description = self._extract_description(page_type)

        # F列.商品状態説明文
        condition = self._extract_condition(page_type)

        # G列？
        shipping = self._extract_shipping()

        # D列目~F列目を改行で区切ってドッキングしたもの
        merged_info = "\n".join(
            [
                title,
                description,
                condition,
            ]
        )

        # TODO 取得日とかをデータに埋め込んでも良いかも

        scraped_data = {
            "image_urls": image_urls,  # A列.商品画像
            "original_url": url,  # B列.URL
            "price": price,  # C列.商品価格
            "shipping_fee": shipping,  # 追加する？送料
            "total_price": price + shipping,  # 追加する？送料込みの価格
            "shipping_region": shipping_region,  # 追加する？発送元の地域
            "title": title,  # D列.商品タイトル
            "description": description,  # E列.商品説明文
            "condition": condition,  # F列.商品状態説明文
            "merged_info": merged_info,  # H列 D列目~F列目を改行で区切ってドッキングしたもの
        }
        return scraped_data

    def _extract_condition(self, page_type):
        """
        商品のconditionを抽出(詳細ページ)
        """
        condition = (
            self._extract_detail_table()
            .find_element(
                By.XPATH,
                './/*[contains(text(),"商品の状態")]/ancestor::node()/following-sibling::node()',
            )
            .get_attribute("textContent")
            .strip()
        )

        return condition

    def _extract_shipping(self):
        """
        Extracts shipping information.
        """

        def determine_shipping_from_text(text: str) -> str:
            """
            送料込みなら0、送料別なら2000(福岡想定)で固定
            """
            is_shipping_fee = 0 if "送料込み" in text else 2000
            return is_shipping_fee

        shipping = None

        try:
            shipping_text_xpath = './/*[contains(text(),"配送料の負担")]/ancestor::node()/following-sibling::node()'
            shipping_text = (
                self._extract_detail_table()
                .find_element(By.XPATH, shipping_text_xpath)
                .get_attribute("textContent")
                .strip()
            )
            shipping = determine_shipping_from_text(shipping_text)
        except NoSuchElementException:
            return None

        return shipping

    def _extract_shipping_region(self):
        """
        Extracts shipping information.
        """

        try:
            shipping_region_xpath = './/*[contains(text(),"発送元の地域")]/ancestor::node()/following-sibling::node()'
            shipping_region = (
                self._extract_detail_table()
                .find_element(By.XPATH, shipping_region_xpath)
                .get_attribute("textContent")
                .strip()
            )
        except NoSuchElementException:
            return None

        return shipping_region

    def _extract_img_urls(self, page_type):
        """
        商品の画像URLを抽出(詳細ページ)
        """
        img_urls = []

        if page_type == "customer_posting":
            # NOTE: 安定性向上のためリトライ機構を追加
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    # NOTE: ページが完全に読み込まれるまで待機
                    time.sleep(2)

                    # NOTE: JavaScriptを直接実行して画像URLを抽出（より安定した方法）
                    img_urls = self.driver.execute_script(
                        """
                            const images = document.querySelectorAll('.slick-list img');
                            return Array.from(images).map(img => img.getAttribute('src'));
                        """
                    )

                    if img_urls and len(img_urls) > 0:
                        break
                except Exception as e:
                    if attempt == max_attempts - 1:
                        logger.warning(f"Failed to extract image URLs: {e}")
                    else:
                        time.sleep(1)  # 再試行前に少し待機

                # NOTE: 最終手段（前の試行が失敗した場合）
                if not img_urls:
                    try:
                        # 直接XPATHでの取得を試みる
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_all_elements_located(
                                (By.XPATH, '//div[@class="slick-list"]//img')
                            )
                        )
                        img_elements = self.driver.find_elements(
                            By.XPATH, '//div[@class="slick-list"]//img'
                        )
                        img_urls = [
                            element.get_attribute("src") for element in img_elements
                        ]
                    except:
                        pass

        elif page_type == "mercari_shops_posting":
            try:
                # NOTE: JavaScriptを使用して直接画像URLを抽出
                img_urls = self.driver.execute_script(
                    """
                        const slides = document.querySelectorAll('[role="region"] .slick-list .slick-track .slick-slide');
                        return Array.from(slides)
                            .map(slide => slide.querySelector('img'))
                            .filter(img => img !== null)
                            .map(img => img.getAttribute('src'));
                    """
                )
            except Exception as e:
                logger.warning(f"Failed to extract Mercari Shops image URLs: {e}")
                img_urls = []

        # img_urlsを|で区切る
        img_urls = "|".join(img_urls)
        return img_urls

    def _extract_detail_table(self) -> WebElement:
        """
        商品詳細ページの「商品の詳細」テーブルのelementを取得して返す。

        Returns:
            WebElement: テーブルリストの WebElement。
        """
        return self.driver.find_element(
            By.XPATH,
            './/h2[contains(text(),"商品の情報")]/ancestor::node()/ancestor::node()/following-sibling::node()',
        )

    def _extract_description(self, page_type):
        """
        商品詳細情報を抽出(詳細ページ)
        """
        description = None
        other_info = self._extract_detail_table().text

        if page_type == "customer_posting":
            description = self.driver.find_element(
                By.XPATH, "//*[@data-testid='description']"
            ).text

        elif page_type == "mercari_shops_posting":
            description_xpath = '//*[contains(@class,"heading__") and contains(text(),"商品の説明")]/ancestor::*/following-sibling::*'
            description_element = self.driver.find_element(By.XPATH, description_xpath)
            description = description_element.get_attribute("textContent").strip()

        return f"{description}|{other_info}"
