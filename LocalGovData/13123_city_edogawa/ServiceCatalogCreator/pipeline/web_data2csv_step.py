import os
import json
import yaml
import hashlib
import pandas as pd
from bs4 import BeautifulSoup

class ColumnManager:
    def __init__(self, yaml_path):
        self.column_config = {}
        self.special_columns = {'名称': None}  # 特殊カラムの初期設定
        self.load_yaml(yaml_path)

    def load_yaml(self, yaml_path):
        try:
            with open(yaml_path, 'r', encoding='utf-8') as file:
                data = yaml.load(file, Loader=yaml.FullLoader)
                self.column_config = data['columns']
        except FileNotFoundError:
            print(f"指定された YAML ファイル {yaml_path} が見つかりません。")
        except Exception as e:
            print(f"YAML の読み込みでエラーが発生しました: {str(e)}")

    def is_column(self, text):
        return any(text in values for values in self.column_config.values())

    def get_column_name(self, text):
        for column, identifiers in self.column_config.items():
            if any(identifier in text for identifier in identifiers):
                return column
        return None

    def validate_table(self, table):
        found_columns = set(table.keys())
        required_columns = set(self.column_config.keys()) - {'名称'}
        return len(found_columns & required_columns) > 0

    def set_special_column(self, name, value):
        self.special_columns[name] = value

    def get_special_column(self, name):
        return self.special_columns.get(name, None)

    def is_table_columns(self, node):
        for child in node.children:
            if self.is_column(child.title):
                print(f'find table columns: {node.title} -> {child.title}')
                return True
        return False
    def create_table(self, node):
        if not self.is_table_columns(node):
            return
        service = {}
        service['名称'] = node.title
        for child in node.children:
            service[child.title] = "  ".join(child.items)

        node.tables.append(pd.DataFrame([service]))
            

class Node:
    def __init__(self, title, level, parent=None):
        self.title = title
        self.level = level
        self.parent = parent # 親ノードへの参照
        self.children = []
        self.items = []
        self.tables = []

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

    def add_table(self, table):
        print(f'add table (title = {self.title}, level={self.level})')
        df = pd.read_html(str(table))[0]
        self.tables.append(df)

    def get_tables(self):
        if not self.tables:
            return {}
        else:
            return pd.concat(self.tables, ignore_index=True, sort=False).to_dict(orient='records')

    def __repr__(self):
        return f"Node(title='{self.title}', level={self.level}, items='{self.items[:30]}...', tables='{self.get_tables()}', children={self.children}\n)"


class HtmlConverter:
    def __init__(self, soup, url, column_manager):
        self.soup = soup
        self.url = url
        self.column_manager = column_manager
        self.root = Node('Root', level=0)
        self.current_node = self.root
        self.parse_html_to_tree(self.soup.body)
        self.apply_create_table(self.root)

    def apply_create_table(self, node):
        self.column_manager.create_table(node)
        for child in node.children:
            self.apply_create_table(child)

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




class WebDataToCSVConvertStep:
    def __init__(self, step_config):
        self.progress_json_path = step_config['progress_file']
        self.output_json_dir = step_config['output_json_dir']
        self.columns_yaml = step_config['columns_yaml']
        self.url_mapping = self.load_mapping()
        os.makedirs(self.output_json_dir, exist_ok=True)

        self.column_manager = ColumnManager(self.columns_yaml)

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
                        extractor = HtmlConverter(soup, url, self.column_manager)
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

