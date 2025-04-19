# Python スクリプト実行手順（Windows / Python 3.12）

このプロジェクトでは `main.py` を Python 3.12 で実行します。

Windows 環境において、次の3通りの方法でスクリプトを実行できます：

- ✅ グローバル環境で実行する（最も簡単）
- 🛡️ 仮想環境（venv）を使って実行する（おすすめ）
- 🐳 Docker コンテナ上で実行する（より再現性を重視する場合）

---

## 🔧 Python 3.12 をインストール（共通）

1. 公式サイトから Python 3.12 をダウンロード  
   👉 https://www.python.org/downloads/release/python-3120/

2. インストール時に **「Add Python to PATH」** にチェックを入れてから進めてください。

3. インストール確認（コマンドプロンプトで）:

```
python --version
```

---

## ✅ 方法①：グローバル環境で実行する

最も簡単な方法です。すぐに試したい場合はこちら。

### ステップ

1. プロジェクトフォルダに移動（例: `cd デスクトップ\myproject`）

```
cd デスクトップ\myproject
```

2. ライブラリをインストール(最初だけでOK！！)

```
pip install -r requirements/common.txt
```

3. `main.py` を実行

```
python main.py
```

> ✅ これで完了です！

---

## 🛡️ 方法②：仮想環境（venv）で実行する

他のプロジェクトとライブラリのバージョンが混ざらないようにしたい場合におすすめです。

### ステップ

1. プロジェクトフォルダに移動

```
cd デスクトップ\myproject
```

2. 仮想環境を作成

```
python -m venv venv
```

3. 仮想環境を有効化

```
venv\Scripts\activate
```

> `(venv)` と表示されれば成功です！

4. ライブラリをインストール

```
pip install -r requirements/common.txt
```

5. `main.py` を実行

```
python main.py
```

6. 仮想環境を終了（任意）

```
deactivate
```

---

## 🐳 補足：Docker を使った実行（上級者向け）

もし Docker が使える場合は、Python のバージョンや依存関係を完全に分離して実行可能です。

- チーム開発や CI 環境において、**実行環境の差をなくす**目的で有効です。
- 詳細な手順はここでは省略しますが、`Dockerfile` と `docker-compose.yml` を使えば簡単に構築可能です。

---

## ⚖️ 環境ごとのメリット比較

| 環境       | メリット                                                                 | 想定対象       |
|------------|------------------------------------------------------------------------|----------------|
| グローバル | ✅ セットアップが最も簡単<br>✅ 初心者でもすぐ動かせる                    | 初心者、個人利用 |
| venv       | ✅ 他プロジェクトと環境を分離できる<br>✅ Python 標準機能で軽量           | 中級者以上、日常開発 |
| Docker     | ✅ OS 依存なしの完全再現可能環境<br>✅ チーム開発・CI/CD に強い            | チーム・本番運用 |

---

## 📂 ファイル構成の例

```
myproject/
├── main.py
├── requirements/
│   └── common.txt         ← 必要なライブラリ一覧
├── venv/                  ← 仮想環境（venv使用時に作成されます）
└── README.md              ← このファイル
```

---

## 🔄 新しいサイトの追加方法

このプロジェクトで新しいサイト用のスクレイピングを追加するには、次の3つのステップが必要です。

### 1. スパイダーの作成

1. `code/spiders/[sitename]/` ディレクトリを作成

```
# 例: RakutenのスパイダーならRakutenディレクトリを作成
mkdir code/spiders/rakuten
```

2. このディレクトリ内に`[sitename]_spider.py`ファイルを作成
   - ChatGPTや生成AIを使って、BaseSpiderを継承したスパイダークラスを作成できます
   - 既存のスパイダー（例：YahaucSpider）を参考にしてください

#### ChatGPT/生成AIへのプロンプト例

以下のようなプロンプトを使って新しいスパイダーを作成できます：

```
以下のYahaucSpiderというスクレイピングコードを参考に、[新しいサイト名]用のスクレイピングスパイダーを作成してください。
最終的に取得できるscraped_dataは既存のルールに従ってください。

基本的な構造は同じで、[新しいサイト名]のHTMLから必要な情報を抽出するメソッドを実装してください。

スクレイピング対象のURLは次のとおりです：
[ターゲットURLを貼り付け]

対象サイトのHTMLサンプルは以下のとおりです：
[HTMLサンプルを貼り付け]

抽出したい情報：
- 商品画像のURL
- 商品価格
- 送料情報
- 商品タイトル
- 商品説明文
- 商品状態説明文

※YahaucSpiderのコード:
[YahaucSpiderのコードを貼り付け]
```

サンプルコード（雛形）:

```python
from spiders._base_spider import BaseSpider
import logging
from bs4 import BeautifulSoup as bs
from typing import Optional
import re
import json
import os
from pathlib import Path

# ロギングの基本設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# 現在のファイルのディレクトリを取得
current_dir = Path(__file__).parent


class 新サイト名Spider(BaseSpider):
    name = "新サイト名"

    def __init__(self, urls):
        super().__init__(urls)

    def run(self):
        scraped_data = self.crawl_urls()
        return scraped_data

    def crawl_urls(self):
        # YahaucSpiderのcrawl_urlsメソッドを参考に実装
        # ...

    def _scrape(self, url):
        soup = self._get_html(url)
        # サイト固有の商品情報抽出ロジックを実装
        # ...
        
        scraped_data = {
            "image_urls": image_urls,
            "original_url": url,
            "price": price,
            # 他の必要なデータ...
        }
        return scraped_data

    # 必要なヘルパーメソッドを追加
```

### 2. URLマッピングの追加

`code/url_mapping.json`ファイルに新しいサイトのドメイン情報を追加します。

例えば、楽天市場を追加する場合:

```json
[
    // ... 既存のマッピング ...
    {
        "domain": "www.rakuten.co.jp",
        "site_name": "rakuten"
    }
]
```

### 3. main.pyへの統合

`code/main.py`ファイルの以下の箇所に新しいスパイダーのインポートと条件分岐を追加します。

1. ファイル上部にインポート文を追加:

```python
# 既存のインポート
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
# 新しいスパイダーのインポートを追加
from spiders.新サイト名.新サイト名_spider import 新サイト名Spider
```

2. mainメソッド内の条件分岐に新しいサイトを追加:

```python
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
        elif site_name == "新サイト名":  # 新しい条件分岐
            spider = 新サイト名Spider(urls)
            scraped_data.extend(spider.run())
        # ... その他のサイト ...
```

### 動作確認

1. 入力ファイル（`入力.xlsx` または `入力.csv`）に新しいサイトのURLを追加
2. スクリプトを実行して正常に動作するか確認:

```
python code/main.py
```

---

これで新しいサイトのスクレイピングが追加できます。既存のスパイダーのコードを参考にしながら、各サイトの構造に合わせた実装を行ってください。
