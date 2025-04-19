from spiders._base_spider import BaseSpider
import logging
from bs4 import BeautifulSoup as bs
from typing import Optional
import re
import json
import os
from pathlib import Path

# ロギングの基本設定を追加
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# 現在のファイルのディレクトリを取得
current_dir = Path(__file__).parent


class YahaucSpider(BaseSpider):
    name = "yahauc"

    def __init__(self, urls):
        super().__init__(urls)

    def run(self):
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
        logger.info(
            f"Completed scraping {len(scraped_data)}/{total_urls} URLs ({len(scraped_data)/total_urls*100:.1f}% success rate)"
        )
        return scraped_data

    def _scrape(self, url):
        soup = self._get_html(url)
        # 出力ファイルパスを相対パスに変更
        output_file = current_dir / "yahauc.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(soup.prettify())
        # A列.商品画像
        image_urls = self._extract_img_urls(soup)

        # B列.URLはそのままurlを使う

        # C列.商品価格
        price = self._extract_price(soup)

        # 送料
        shipping_fee = self._extract_shipping_fee(soup)

        # 発送元の地域
        shipping_region = self._extract_shipping_region(soup)

        # D列.商品タイトル
        title = soup.select_one("#itemTitle").text

        # E列.商品説明文
        description = self._extract_description(soup)

        # F列.商品状態説明文
        condition = self._extract_condition(soup)

        # G列？

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
            "shipping_fee": shipping_fee,  # 追加する？送料
            "total_price": price + shipping_fee,  # 追加する？送料込みの価格
            "shipping_region": shipping_region,  # 追加する？発送元の地域
            "title": title,  # D列.商品タイトル
            "description": description,  # E列.商品説明文
            "condition": condition,  # F列.商品状態説明文
            "merged_info": merged_info,  # H列 D列目~F列目を改行で区切ってドッキングしたもの
        }
        return scraped_data

    def _extract_shipping_fee(self, soup: bs) -> Optional[int]:
        """
        送料無料なら0、送料有料なら2000（福岡想定）で固定
        """
        if any(
            span
            for span in soup.select("li span")
            if span.string and "送料無料" in span.string
        ):
            return 0
        return 2000

    def _extract_shipping_region(self, soup: bs) -> Optional[str]:
        """
        <div id="itemInfo"> 内の dt タグで「発送元の地域」と記載されている要素の
        兄弟 dd タグの値を select を使って抽出する。
        """
        # itemInfo 配下の dt 要素すべてを選択
        dts = soup.select("div#itemInfo dt")

        for dt in dts:
            # 厳密に文字列一致で「発送元の地域」を探す
            if dt.string and dt.string.strip() == "発送元の地域":
                # 兄弟の dd を CSSセレクタで取得（1つ後の兄弟ノード）
                sibling_dd = dt.find_next_sibling("dd")
                if sibling_dd:
                    return sibling_dd.get_text(strip=True)
                break  # 一致が見つかったらそれ以上探す必要なし

        return None

    def _exstract_shipping_fee(self, soup: bs) -> Optional[int]:
        """
        送料を抽出(詳細ページ)
        """
        shipping_fee = soup.select_one("#itemPostage").text
        return shipping_fee

    def _extract_img_urls(self, soup: bs):
        img_urls = [
            img.get("src")
            for img in soup.select(".ProductImage__image img,.slick-slider img")
        ]
        img_urls = "|".join(list(set(img_urls)))
        return img_urls

    def _extract_price(self, soup: bs) -> Optional[int]:
        """
        商品価格抽出(一覧ページ)

        商品の価格を取得する関数

        Args:
            soup: BeautifulSoupオブジェクト

        Returns:
            int: 即決価格(bidorbuy)が存在する場合は即決価格、存在しない場合は現在価格(price)
        """
        # NOTE: __NEXT_DATA__から商品情報を取得
        script_tag = soup.select_one("#__NEXT_DATA__")
        data = json.loads(script_tag.string)

        # NOTE: 商品の詳細情報を取得
        detail = data["props"]["initialState"]["item"]["detail"]

        price = re.sub(r"\D", "", str(detail.get("bidorbuy", detail["price"])))

        return int(price)

    def _extract_condition(self, soup: bs) -> Optional[str]:
        """
        商品のconditionを抽出(詳細ページ)
        """
        try:
            # 新しいHTML構造での抽出
            if condition_element := soup.find("dt", text="商品の状態"):
                condition_text = condition_element.find_next("dd").get_text(strip=True)
                return condition_text
            # 古いHTML構造での抽出（後方互換性のため）
            elif condition_element := soup.find(
                class_="Section__tableHead", text="状態"
            ):
                condition_text = condition_element.parent.find(
                    "td", class_="Section__tableData"
                ).get_text(strip=True)
                condition = re.sub("\\n.*", "", condition_text)
                return condition
            else:
                logger.warning("NO CONDITION")
                return ""
        except Exception as e:
            logger.warning(f"商品の状態抽出中にエラーが発生しました: {str(e)}")

        return ""

    def _extract_description(self, soup: bs) -> Optional[str]:
        """
        商品詳細情報を抽出(詳細ページ)
        """
        item_desc = soup.select_one(".ProductExplanation__commentBody,#description")
        return item_desc.text if item_desc else None
