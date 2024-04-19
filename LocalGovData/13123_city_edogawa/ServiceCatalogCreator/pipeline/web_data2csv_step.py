import os
import json
import yaml
import hashlib
import pandas as pd
from bs4 import BeautifulSoup

import yaml
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



class HtmlConverter:
    def __init__(self, soup, column_manager):
        self.soup = soup
        self.column_manager = column_manager

    def extract_tables(self):
        headers_stack = []
        dataframes = []
        current_table = {}
        current_name = None
        current_level = None
        column_layer_level = None
        service_name = None

        headers = self.soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])

        for i, header in enumerate(headers):
            level = int(header.name[1])  # h1 -> 1, h2 -> 2, etc.
            header_text = header.get_text(strip=True)
            #print(f"level({level}), text = {header_text}")

            # サービス名を作るための素材
            while len(headers_stack) >= level:
                headers_stack.pop()
            headers_stack.append(header_text)

            # 
            if self.column_manager.is_column(header_text) or (column_layer_level is None and column_layer_level == level):
                service_name = " - ".join(headers_stack)
                column_layer_level = level  # カラムとして扱う層のlevelとして設定
                current_table[header_text] = self.collect_data(header)
                #print(f"column_layer_level[{level}] start : header_text = {header_text}")
            else:
                # カラム対象の層よりも高い層のヘッダーが現れたら、テーブルとして新たに開始
                if column_layer_level is None or column_layer_level > level:
                    #print(f"column_layer_level[{level}] end : header_text = {header_text}")
                    service_name = " - ".join(headers_stack)
                    columne_layer_level = None
                    if current_table:
                        df = pd.DataFrame([current_table])
                        df.insert(0, '名称', service_name)
                        dataframes.append(df)
                        current_table = {}
                        #print(f"column_layer_level[{level}] end -> add table ")
                else:
                    # データをテーブルに追加
                    current_table.setdefault(header_text, self.collect_data(header))
                    #print(f"column_layer_level[{level}] == : header_text = {header_text}")

        # 最後のテーブルを追加
        if current_table:
            df = pd.DataFrame([current_table])
            df.insert(0, '名称', service_name)
            dataframes.append(df)

        return dataframes

    def collect_data(self, header):
        collected_text = []
        next_tag = header.find_next_sibling()
        while next_tag and next_tag.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            collected_text.append(next_tag.get_text(separator=' ', strip=True))
            next_tag = next_tag.find_next_sibling()
        return ' '.join(collected_text)




# TableExtractor
# 以下２つの処理を行う
# 1. html中に直接記載されているテーブルを取得する 
# 2. htmlの構造をテーブル化する
class TableExtractor:
    def __init__(self, soup, url, columns_yaml):
        self.table_list = []
        self.html_tbl_list = []
        self.soup = soup
        self.columns_yaml = columns_yaml
        self.url = url
        self.column_manager = ColumnManager(columns_yaml)
        self.extract_tables()
        self.html_to_table()
     
    # 1. html中に直接記載されているテーブルを取得する 
    def extract_tables(self):
        tables = self.soup.find_all('table')
        for table in tables:
            try:
                df = pd.read_html(str(table))[0]
                df['URL'] = self.url  # URL列を追加
                self.table_list.append(df)
            except ValueError as e:
                print(f"Failed to parse table: {e}")
                print(f"  error URL : {self.url}")
            except IndexError as e:
                print(f"Table format error: {e}")
                print(f"  error URL : {self.url}")

    # 2. htmlの構造をテーブル化する
    def html_to_table(self):
        converter = HtmlConverter(self.soup, self.column_manager)
        extracted_tables = converter.extract_tables()
        for df in extracted_tables:
            df['URL'] = self.url  # 各DataFrameにURL列を追加
        self.html_tbl_list.extend(extracted_tables)
 

    # 1,2の手法で取得したテーブルをreturnする
    def get_tables(self):
        print(f"URL : {self.url}")
        print(f"  table / html_tbl : {len(self.table_list)} / {len(self.html_tbl_list)}")
        return self.table_list + self.html_tbl_list or []


class WebDataToCSVConvertStep:
    def __init__(self, step_config):
        self.progress_json_path = step_config['progress_file']
        self.output_csv_dir = step_config['output_csv_dir']
        self.columns_yaml = step_config['columns_yaml']
        self.url_mapping = self.load_mapping()
        os.makedirs(self.output_csv_dir, exist_ok=True)

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

        for url, filepath in self.url_mapping.items():
            if filepath.endswith('.html'):
                with open(filepath, 'r', encoding='utf-8') as file:
                    html_content = file.read()

                soup = BeautifulSoup(html_content, 'html.parser')
                # キーワードチェック
                if self.should_process(soup):
                    extractor = TableExtractor(soup, url, self.columns_yaml)
                    ext_tables = extractor.get_tables()
                    for ext_table in ext_tables:
                        table_hash = self.generate_hash(ext_table)
                        if table_hash not in unique_hashes:
                            unique_hashes.add(table_hash)
                            unique_tables.append(ext_table)

        self.df_list = unique_tables
        self.save_table_to_csv(self.output_csv_dir)

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

    def save_table_to_csv(self, file_path):
        for index, df in enumerate(self.df_list):
            df.to_csv(f'{file_path}/table_{index + 1}.csv', index=False)

