import os
import yaml
import pandas as pd
from bs4 import BeautifulSoup

class HTagNode:
    def __init__(self, title, level, parent=None):
        #print(f'[new node] level = {level}, title = [{title}]')
        self.title = title
        self.level = level
        self.parent = parent # 親ノードへの参照
        self.children = []
        self.items = []
        self.htag_tables = []
        self.tables = []

    def truncate_list_after_keyword(self, lst, keyword):
        if keyword in lst:
            # キーワードが見つかったインデックスを取得
            index = lst.index(keyword)
            # キーワード直前のインデックスまでのリストを返す
            return lst[:index]
        else:
            # キーワードがリストにない場合は、元のリストをそのまま返す
            return lst

    def get_content(self, th=7):
        content_list = []
        child_content_list = []
        if self.level >= th:
            return content_list
        for child in self.children:
            child_content_list += child.get_content(th)
        content_list = [self.title] + self.items + child_content_list
        content_list = self.truncate_list_after_keyword(content_list, "このページを評価する")
        return [s for s in content_list if len(s) > 1]

    def add_child(self, child):
        # 新しい子ノードが追加される際、適切な親を見つける
        current_node = self
        while current_node.level >= child.level and current_node.parent is not None:
            current_node = current_node.parent
        # 適切な親ノードに子を追加
        current_node.children.append(child)
        child.parent = current_node

    def add_item(self, item):
        self.items.append(item)

    def matches_keywords(self, keywords):
        # タイトルが指定されたキーワードのいずれかにマッチするか確認
        return any(self.title.startswith(keyword) for keyword in keywords)

    def matches_keywords_old(self, keywords):
        # タイトルが指定されたキーワードのいずれかにマッチするか確認
        return any(keyword in self.title for keyword in keywords)

    def add_table(self, table):
        # BeautifulSoupを使用してtableタグを解析
        soup = BeautifulSoup(str(table), 'html.parser')
        # captionを見つける
        caption = soup.find('caption')
        caption_text = caption.get_text(strip=True) if caption else "No caption"
        
        # tableをDataFrameに変換
        df = pd.read_html(str(table))[0]
        # DataFrameの既存の列の最後にcaption列を追加
        df['caption'] = caption_text
        #print(f'add table (title = {self.title}, caption = {caption_text}, level={self.level})')

        # 変換したDataFrameをtablesリストに追加
        self.tables.append(df)

    def get_htag_tables(self):
        if not self.htag_tables:
            return {}
        else:
            return pd.concat(self.htag_tables, ignore_index=True, sort=False).to_dict(orient='records')

    def get_tables(self):
        if not self.tables:
            return {}
        else:
            return pd.concat(self.tables, ignore_index=True, sort=False).to_dict(orient='records')

    def __repr__(self):
        return f"HTagNode(title='{self.title}', level={self.level}, items='{self.items[:3]}...', htag_tables='{self.get_htag_tables()}', tag_tables='{self.get_tables()}' \n)"
        #return f"Node(title='{self.title}', level={self.level}, items='{self.items[:3]}...'\n)"
        #return f"Node(title='{self.title}', level={self.level}, items='{self.items[:30]}...', tables='{self.get_tables()}', children={self.children}\n)"


