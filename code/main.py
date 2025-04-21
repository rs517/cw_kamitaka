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
    # インデックス情報を含むURL辞書を取得
    url_data = _load_url_data()
    # 元のURLとインデックスのマッピングを作成
    url_to_index_map = {}

    # 各URLのインデックスを記録
    for site_name, url_items in url_data.items():
        for url_item in url_items:
            url_to_index_map[url_item["url"]] = url_item["index"]

    for site_name, url_items in url_data.items():
        # URLsのリストを取得
        urls = [item["url"] for item in url_items]

        if site_name == "yahauc":
            spider = YahaucSpider(urls)
            site_data = spider.run()
            # 元のインデックスを各スクレイピング結果に追加
            for item in site_data:
                item["original_index"] = url_to_index_map.get(item["original_url"])
            scraped_data.extend(site_data)
        elif site_name == "mercari":
            spider = MercariSpider(urls)
            site_data = spider.run()
            # 元のインデックスを各スクレイピング結果に追加
            for item in site_data:
                item["original_index"] = url_to_index_map.get(item["original_url"])
            scraped_data.extend(site_data)
        else:
            # 未対応のサイトの場合は、URLだけを含む最小限のデータを追加
            for url_item in url_items:
                scraped_data.append(
                    {
                        "original_url": url_item["url"],
                        "original_index": url_item["index"],
                        # 他のフィールドは空のままにして、URLとインデックスだけを保持
                    }
                )

    # DataFrameを作成し、元のインデックス順にソート
    df = pd.DataFrame(scraped_data)
    if "original_index" in df.columns:
        df = df.sort_values("original_index")

    # 現在の日時を取得してファイル名を生成
    from datetime import datetime

    current_time = datetime.now().strftime("%Y%m%d%H%M")
    output_filename = current_dir / f"output_{current_time}.csv"
    # original_indexをインデックスに設定して出力
    df.set_index("original_index", inplace=True)
    df.to_csv(output_filename, encoding="utf-8-sig")


def _load_input_data():
    try:
        # Excelファイルが存在する場合はExcelから読み込む
        excel_path = current_dir / "入力.xlsx"
        if excel_path.exists():
            df = pd.read_excel(excel_path)
            # インデックスとURLのペアのリストを作成
            return [
                {"index": idx, "url": url}
                for idx, url in enumerate(df.iloc[:, 0].tolist())
            ]
        # CSVファイルが存在する場合はCSVから読み込む
        csv_path = current_dir / "入力.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            # インデックスとURLのペアのリストを作成
            return [
                {"index": idx, "url": url}
                for idx, url in enumerate(df.iloc[:, 0].tolist())
            ]
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
    インデックス情報を保持するように変更
    """
    loaded_urls = {}
    url_items = _load_input_data()  # インデックスとURLのペアのリスト

    try:
        url_mapping = _load_url_mapping()
        for mapping in url_mapping:
            loaded_urls[mapping["site_name"]] = []

        for url_item in url_items:
            found_match = False
            for mapping in url_mapping:
                if mapping["domain"] in url_item["url"]:
                    loaded_urls[mapping["site_name"]].append(url_item)
                    found_match = True
                    break

            # サイト名が見つからない場合は "unknown" に分類
            if not found_match:
                if "unknown" not in loaded_urls:
                    loaded_urls["unknown"] = []
                loaded_urls["unknown"].append(url_item)

    except Exception as e:
        print(e)
        return {}  # 空の辞書を返す（文字列ではなく）

    return loaded_urls


if __name__ == "__main__":
    main()
