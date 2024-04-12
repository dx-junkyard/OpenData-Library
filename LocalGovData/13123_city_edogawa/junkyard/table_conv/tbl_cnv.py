# 必要なライブラリをインポート
import pandas as pd
from bs4 import BeautifulSoup

# HTMLファイルの読み込み
with open('./ichijihoiku.html', 'r', encoding='utf-8') as file:
    html_content = file.read()

# BeautifulSoupでHTMLを解析
soup = BeautifulSoup(html_content, 'html.parser')

# 全てのテーブルを見つける
tables = soup.find_all('table')

# CSVファイルに保存する前に、テーブルデータを処理
for index, table in enumerate(tables):
    # pandasのread_htmlを使ってテーブルをDataFrameに変換
    df = pd.read_html(str(table))[0]
    
    # セルの結合を解除する処理
    df = df.ffill().bfill()

    # CSVファイルとして出力
    df.to_csv(f'./table_{index + 1}.csv', index=False)

# 成功したことを表示
print("テーブルをCSVファイルに保存しました。")

