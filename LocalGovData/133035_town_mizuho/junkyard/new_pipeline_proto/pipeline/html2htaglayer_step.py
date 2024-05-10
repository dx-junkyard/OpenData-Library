import os
import json
import yaml
import hashlib
import pandas as pd
from bs4 import BeautifulSoup
from lib.column_manager import ColumnManager
from lib.htag_node import  HTagNode as Node


class HtmlConverter:
    def __init__(self, soup, url):
        self.soup = soup
        self.url = url
        self.root = Node('Root', level=0)
        self.current_node = self.root
        self.parse_html_to_tree(self.soup.body)

    def parse_html_to_tree(self, soup):
        tags = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'table'], recursive=True)
        for tag in tags:
            if tag.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(tag.name[1])  # h1 -> 1, h2 -> 2, ...
                new_node = Node(tag.get_text(strip=True), level)
                if level > self.current_node.level:
                    # 現在のノードが親ノードとして適切である場合
                    self.current_node.add_child(new_node)
                else:
                    # 新しいノードが現在のノードのレベルと同じかそれ以上の場合、適切な親を見つける
                    while self.current_node.level >= level:
                        self.current_node = self.current_node.parent
                    self.current_node.add_child(new_node)
                self.current_node = new_node  # 更新された現在のノード
            elif tag.name == 'table':
                self.current_node.add_table(tag)
            elif tag.name == 'p':
                self.current_node.add_item(tag.get_text(strip=True))

    def display_tree(self, node=None, indent=0):
        if node is None:
            node = self.root
        print(' ' * indent + repr(node))
        for child in node.children:
            self.display_tree(child, indent + 2)




class Html2HtagLayerStep:
    def __init__(self, step_config):
        self.progress_json_path = step_config['progress_file']
        self.output_json_dir = step_config['output_json_dir']
        self.columns_yaml = step_config['columns_yaml']
        self.url_mapping = self.load_mapping()
        os.makedirs(self.output_json_dir, exist_ok=True)

#        self.column_manager = ColumnManager(self.columns_yaml)

        # キーワードリストを適切に処理する
        include_keywords = step_config.get('include_keywords', '')
        self.include_keywords = [keyword.strip() for keyword in include_keywords.split(",")] if include_keywords else []

        exclude_keywords = step_config.get('exclude_keywords', '')
        self.exclude_keywords = [keyword.strip() for keyword in exclude_keywords.split(",")] if exclude_keywords else []
        print(f"include / exclude : {self.include_keywords} / {self.exclude_keywords}")


    def load_mapping(self):
        with open(self.progress_json_path, 'r') as file:
            data = json.load(file)
        return data.get("visited", {})

    def generate_hash(self, details):
        if isinstance(details, pd.DataFrame):
            # レコード形式で辞書に変換
            details_dict_list = details.to_dict(orient='records')
            # リスト内の各辞書に対してキーを文字列に変換
            details_dict_list = [{str(key): value for key, value in record.items()} for record in details_dict_list]
        else:
            details_dict_list = details
       
        # JSON 形式でシリアライズするためには、リスト全体をダンプする
        details_str = json.dumps(details_dict_list, sort_keys=True)
        return hashlib.sha256(details_str.encode('utf-8')).hexdigest()

    def execute(self):
        unique_hashes = set()
        unique_tables = []
        service_json = None

        for url, filepath in self.url_mapping.items():
            if filepath.endswith('.html'):
                with open(filepath, 'r', encoding='utf-8') as file:
                    html_content = file.read()

                soup = BeautifulSoup(html_content, 'html.parser')
                # キーワードチェック
                if self.should_process(soup):
                    try:
                        #extractor = HtmlConverter(soup, url, self.column_manager)
                        extractor = HtmlConverter(soup, url)
                        extractor.display_tree()

                        #service_json = extractor.extract_tables()
                        #table_hash = self.generate_hash(service_json)
                        #if table_hash not in unique_hashes:
                        #    unique_hashes.add(table_hash)
                        #    unique_tables.append(service_json)
                    except ValueError as e:
                        print(f"Failed to parse table: {e}")
                        print(f"  error URL : {url}")
                    except IndexError as e:
                        print(f"Table format error: {e}")
                        print(f"  error URL : {url}")
                else:
                    print(f'処理対象の単語がふくまれていません')
                
                    

        #self.unique_services = unique_tables
        #self.save_table_to_json(self.output_json_dir)

    def should_process(self, soup):
        headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

        if headers:
            # 最初の見出しタグの次の兄弟要素から終わりまでの内容を抽出
            relevant_content = ''.join(str(sibling) for header in headers for sibling in header.find_all_next(string=True))
        else:
            # 見出しタグがない場合、すべてのコンテンツを評価
            #relevant_content = content
            # 見出しタグがない場合、処理をおこなわない
            return False

        include_matches = [keyword for keyword in self.include_keywords if keyword in relevant_content]
        exclude_matches = [keyword for keyword in self.exclude_keywords if keyword in relevant_content]

        include = bool(include_matches)
        exclude = bool(exclude_matches)

        matched_keywords = {'include': include_matches, 'exclude': exclude_matches}
        #print(f"matched keywords : {matched_keywords}")

        return include and not exclude

    def save_table_to_json(self, file_path):
        with open(f'{file_path}/service_catalog.json', "w", encoding="utf-8") as f:
            json.dump(self.unique_services, f, ensure_ascii=False, indent=4)

