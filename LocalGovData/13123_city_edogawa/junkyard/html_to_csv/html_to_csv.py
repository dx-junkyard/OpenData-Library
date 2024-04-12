import pandas as pd
from bs4 import BeautifulSoup

# HTMLファイルの読み込み
with open('./greenpalace.html', 'r', encoding='utf-8') as file:
    html_content = file.read()

# BeautifulSoupでHTMLを解析
soup = BeautifulSoup(html_content, 'html.parser')

# ヘッダーとなる情報を格納する辞書を初期化
data = {}

# h1からh6タグを検索し、所在地、連絡先などの情報を抽出
for i in range(1, 7):
    headers = soup.find_all(f'h{i}')
    for header in headers:
        next_tag = header.find_next_sibling()
        while next_tag and next_tag.name not in [f'h{j}' for j in range(1, 7)]:
            if next_tag.name == 'p' or next_tag.name == 'ul':
                # ヘッダーテキストをキーとして内容を辞書に追加
                key = header.get_text(strip=True)
                value = next_tag.get_text(separator=' ', strip=True)
                data[key] = value
            next_tag = next_tag.find_next_sibling()

# pandas DataFrameに変換
df = pd.DataFrame([data])

# CSVファイルとして出力
df.to_csv('./extracted_info.csv', index=False)

print("情報がCSVファイルに保存されました。")

