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

    #def validate_table(self, table):
    #    found_columns = set(table.keys())
    #    required_columns = set(self.column_config.keys())
    #    return found_columns & required_columns



class HtmlConverter:
    def __init__(self, soup, url, column_manager):
        self.soup = soup
        self.url = url
        self.column_manager = column_manager

    def extract_tables(self):
        headers_stack = []
        hierarchy_stack = []
        dataframes = []
        current_table = {}
        current_name = None
        current_level = None
        column_layer_level = None
        service_name = None
        summary = None

        tags = self.soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'li', 'table', 'a'])

        new_service = {
            'summary': '',
            'details': [],
            'tables': None,
            'url': self.url
        }

        for i, tag in enumerate(tags):
            if tag.name.startswith('h'):
                level = int(tag.name[1])  # h1 -> 1, h2 -> 2, etc.
                tag_text = tag.get_text(strip=True)
                #print(f"level({level}), text = {tag_text}")
    
                # 属性、名称を作るためのlist
                while len(headers_stack) >= level:
                    headers_stack.pop()
                headers_stack.append(tag_text)
    
                # 
                if self.column_manager.is_column(tag_text) or (column_layer_level is None and column_layer_level == level):
                    service_name = headers_stack[-1]
                    attribute_name = " - ".join(headers_stack[:-1]) if len(headers_stack) > 1 else ""
                    column_layer_level = level  # カラムとして扱う層のlevelとして設定
                    current_table[tag_text] = self.collect_data(tag)
                    #print(f"column_layer_level[{level}] start : tag_text = {tag_text}")
                else:
                    if summary  == None:
                        summary = tag_text
                    # カラム対象の層よりも高い層のヘッダーが現れたら、テーブルとして新たに開始
                    if column_layer_level is None or column_layer_level > level:
                        #print(f"column_layer_level[{level}] end : tag_text = {tag_text}")
                        service_name = headers_stack[-1]
                        attribute_name = " - ".join(headers_stack[:-1]) if len(headers_stack) > 1 else ""
                        column_layer_level = None
                        if current_table:
                            df = pd.DataFrame([current_table])
                            df.insert(0, '名称', service_name)
                            if attribute_name != "":
                                df.insert(0, '大項目', attribute_name) 
                            dataframes.append(df)
                            current_table = {}
                            #print(f"column_layer_level[{level}] end -> add table ")
                    else:
                        # データをテーブルに追加
                        current_table.setdefault(tag_text, self.collect_data(tag))
                        #print(f"column_layer_level[{level}] == : tag_text = {tag_text}")
            else:
                if tag.name == 'table':
                    df = pd.read_html(str(tag))[0]
                    if self.column_manager.validate_table(df):
                      dataframes.append(df)
                else:
                    if new_service['summary']  == None and tag.name != 'table':
                        new_service['summary'] = tag.get_text(strip=True)
                    else:
                        details_content = self.handle_detail_tag(tag)
                        if details_content:
                            new_service['details'].append(details_content)
    
        # 最後のテーブルを追加
        if current_table:
            df = pd.DataFrame([current_table])
            df.insert(0, '名称', service_name)
            if attribute_name != "":
                df.insert(0, '大項目', attribute_name) 
            dataframes.append(df)

        new_service['tables'] = pd.concat(dataframes, ignore_index=True, sort=False).to_dict(orient='records')

        return new_service


    def handle_detail_tag(self, tag):
        # 各タグの内容を処理
        if tag.name == 'ul':
            return [self.handle_detail_tag(li) for li in tag.find_all('li')]
        elif tag.name == 'li':
            return tag.text.strip()
        elif tag.name == 'a':
            return {'text': tag.get_text(strip=True), 'url': tag.get('href')}
        else:
            return tag.text.strip()


    def collect_data(self, header):
        collected_text = []
        next_tag = header.find_next_sibling()
        while next_tag and next_tag.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            collected_text.append(next_tag.get_text(separator=' ', strip=True))
            next_tag = next_tag.find_next_sibling()
        return ' '.join(collected_text)





class WebDataToCSVConvertStep:
    def __init__(self, step_config):
        self.progress_json_path = step_config['progress_file']
        self.output_csv_dir = step_config['output_csv_dir']
        self.columns_yaml = step_config['columns_yaml']
        self.url_mapping = self.load_mapping()
        os.makedirs(self.output_csv_dir, exist_ok=True)

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
                        service_json = extractor.extract_tables()
                    except ValueError as e:
                        print(f"Failed to parse table: {e}")
                        print(f"  error URL : {self.url}")
                    except IndexError as e:
                        print(f"Table format error: {e}")
                        print(f"  error URL : {self.url}")
                    table_hash = self.generate_hash(service_json)
                    if table_hash not in unique_hashes:
                        unique_hashes.add(table_hash)
                        unique_tables.append(service_json)
                    

        self.unique_services = unique_tables
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
        with open(f'{file_path}/service_catalog.json', "w", encoding="utf-8") as f:
            json.dump(self.unique_services, f, ensure_ascii=False, indent=4)
        #for index, df in enumerate(self.df_list):
        #    df.to_csv(f'{file_path}/table_{index + 1}.csv', index=False)

