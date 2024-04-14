import os
import json
import yaml
import hashlib
import pandas as pd
from bs4 import BeautifulSoup

#
class HtmlConverter:
    def __init__(self, soup, yaml_path):
        #self.html_content = html_content
        self.soup = soup
        self.yaml_path = yaml_path
        self.columns = {}
        self.load_yaml()
        self.data = self.extract_info()

    def load_yaml(self):
        try:
            with open(self.yaml_path, 'r', encoding='utf-8') as file:
                data = yaml.load(file, Loader=yaml.FullLoader)
                self.columns = data['columns']
                #print(f"columns : {str(self.columns)}")
        except FileNotFoundError:
            print("指定されたcolumns_yamlファイル{self.yaml_path}が見つかりません。")
        except OSError as e:
            print(f"columns_yamlの読み込みでエラーが発生しました: {e.strerror}") 

    def extract_info(self):
        data = {}

        # Initialize facility_name_found as False
        facility_name_found = False

        for header in self.soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            header_text = header.get_text(strip=True)
            collected_text = []

            for sibling in header.find_next_siblings():
                if sibling.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    break
                collected_text.append(sibling.get_text(separator=' ', strip=True))

            full_text = ' '.join(collected_text)

            # Match headers to specified YAML keys
            for key, identifiers in self.columns.items():
                if any(identifier in header_text for identifier in identifiers):
                    data[key] = full_text
                    if key == '施設名':
                        facility_name_found = True

            # If '施設名' key is specified but not found, use the first header text
            if '施設名' not in data and not facility_name_found:
                data['施設名'] = header_text if header_text else 'Unknown'

        return data

    def get_tables(self):
        df = pd.DataFrame([self.data])
        tables = []
        tables.append(df)
        return tables


# TableExtractor
# 以下２つの処理を行う
# 1. html中に直接記載されているテーブルを取得する 
# 2. htmlの構造をテーブル化する
class TableExtractor:
    def __init__(self, html_content, url, columns_yaml):
        self.table_list = []
        self.html_tbl_list = []
        self.html_content = html_content
        self.columns_yaml = columns_yaml
        self.url = url
        # BeautifulSoupでHTMLを解析
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.extract_tables()
        self.html_to_table()
     
    # 1. html中に直接記載されているテーブルを取得する 
    def extract_tables(self):
        tables = self.soup.find_all('table')
        for table in tables:
            try:
                df = pd.read_html(str(table))[0]
                self.table_list.append(df)
            except ValueError as e:
                print(f"Failed to parse table: {e}")
                print(f"  error URL : {self.url}")
            except IndexError as e:
                print(f"Table format error: {e}")
                print(f"  error URL : {self.url}")
 
    # 2. htmlの構造をテーブル化する
    def html_to_table(self):
        converter = HtmlConverter(self.soup, self.columns_yaml)
        self.html_tbl_list.extend(converter.get_tables())

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

    def load_mapping(self):
        """マッピング情報を読み込む"""
        with open(self.progress_json_path, 'r') as file:
            data = json.load(file)
        return data.get("visited", {})


    def generate_hash(self, details):
        if isinstance(details, pd.DataFrame):
            details_dict_list = details.to_dict(orient='records')  # レコード形式で辞書に変換
    
            # リスト内の各辞書に対してキーを文字列に変換
            details_dict_list = [{str(key): value for key, value in record.items()} for record in details_dict_list]
        else:
            details_dict_list = details
    
        # JSON 形式でシリアライズするためには、リスト全体をダンプする
        details_str = json.dumps(details_dict_list, sort_keys=True)
        return hashlib.sha256(details_str.encode('utf-8')).hexdigest()


    def generate_hash_old2(self, details):
        if isinstance(details, pd.DataFrame):
            details_dict = details.to_dict(orient='records')  # レコード形式で辞書に変換
        else:
            details_dict = details
    
        # タプルキーを文字列に変換
        details_dict = {str(key): value for key, value in details_dict.items()}
    
        details_str = json.dumps(details_dict, sort_keys=True)
        return hashlib.sha256(details_str.encode('utf-8')).hexdigest()
    

    def generate_hash_old(self, details):
        # DataFrameを辞書に変換
        if isinstance(details, pd.DataFrame):
            details_dict = details.to_dict(orient='records')  # レコード形式で辞書に変換
        else:
            details_dict = details
   
        # タプルキーを文字列に変換
        details_dict = {str(key): value for key, value in details_dict.items()}

        details_str = json.dumps(details_dict, sort_keys=True)
        return hashlib.sha256(details_str.encode('utf-8')).hexdigest()


    def generate_hash_old(self, details):
        # detailsをJSON文字列に変換し、そのハッシュ値を生成
        details_str = json.dumps(details, sort_keys=True)
        return hashlib.sha256(details_str.encode('utf-8')).hexdigest()

    def execute(self):
        unique_hashes = set()  # 生成されたハッシュ値を保持するセット
        unique_tables = []

        for url, filepath in self.url_mapping.items():
            if filepath.endswith('.html'):
                with open(filepath, 'r', encoding='utf-8') as file:
                    html_content = file.read()
                extractor = TableExtractor(html_content, url, self.columns_yaml)
                ext_tables = extractor.get_tables()
                for ext_table in ext_tables:
                    table_hash = self.generate_hash(ext_table)
                    if table_hash not in unique_hashes:
                        unique_hashes.add(table_hash)
                        unique_tables.append(ext_table)
        self.df_list = unique_tables
        self.save_table_to_csv(self.output_csv_dir)

    def save_table_to_csv(self, file_path):
        for index, df in enumerate(self.df_list):
            # CSVファイルとして出力
            df.to_csv(f'{file_path}/table_{index + 1}.csv', index=False)



