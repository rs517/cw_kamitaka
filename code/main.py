import pandas as pd
import os
import sys
import json
from pathlib import Path

# 現在のファイルのディレクトリを取得して、そこを基準にする
current_dir = Path(__file__).parent
# sys.pathに追加して、このディレクトリをモジュール検索パスに入れる
sys.path.insert(0, str(current_dir))

from spiders.yahauc.yahauc_spider import YahaucSpider
from spiders.mercari.mercari_spider import MercariSpider


def main():
    scraped_data = []
    url_data = _load_url_data()

    for site_name, urls in url_data.items():
        if site_name == "yahauc":
            spider = YahaucSpider(urls)
            scraped_data.extend(spider.run())
        elif site_name == "mercari":
            spider = MercariSpider(urls)
            scraped_data.extend(spider.run())

    df = pd.DataFrame(scraped_data)
    # 現在の日時を取得してファイル名を生成
    from datetime import datetime

    current_time = datetime.now().strftime("%Y%m%d%H%M")
    output_filename = current_dir / f"output_{current_time}.csv"
    df.to_csv(output_filename, index=True, encoding="utf-8-sig")


def _load_input_data():
    try:
        # Excelファイルが存在する場合はExcelから読み込む
        excel_path = current_dir / "入力.xlsx"
        if excel_path.exists():
            df = pd.read_excel(excel_path)
            urls = df.iloc[:, 0].tolist()
            return urls
        # CSVファイルが存在する場合はCSVから読み込む
        csv_path = current_dir / "入力.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            urls = df.iloc[:, 0].tolist()
            return urls
        else:
            print("入力ファイルが見つかりません")
            return []
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return []


def _load_url_mapping():
    """
    url_mapping.jsonを読み込む
    """
    try:
        mapping_path = current_dir / "url_mapping.json"
        with open(mapping_path, "r") as f:
            url_mapping = json.load(f)
        return url_mapping
    except Exception as e:
        print(e)
        return {}


def _load_url_data():
    """
    urlsのリストから、url_mappingのdomainを含むもののsite_nameとdictを返す
    """
    loaded_urls = {}
    urls = _load_input_data()

    try:
        url_mapping = _load_url_mapping()
        for mapping in url_mapping:
            loaded_urls[mapping["site_name"]] = []

        for url in urls:
            for mapping in url_mapping:
                if mapping["domain"] in url:
                    loaded_urls[mapping["site_name"]].append(url)

    except Exception as e:
        print(e)
        return ""

    return loaded_urls


if __name__ == "__main__":
    main()
