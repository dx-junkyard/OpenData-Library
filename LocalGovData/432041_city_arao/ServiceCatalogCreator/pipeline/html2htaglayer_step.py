import os
import json
import yaml
import hashlib
import pandas as pd
import torch
import numpy as np
from bs4 import BeautifulSoup
from lib.column_manager import ColumnManager
from lib.htag_node import  HTagNode as Node
from transformers import BertTokenizer, BertModel


class HtmlConverter:
    def __init__(self, soup, url, columns):
        self.soup = soup
        self.url = url
        self.root = Node('Root', level=0)
        self.current_node = self.root
        self.columns = columns
        self.parse_html_to_tree(self.soup.body)
        self.item_level = 6
        self.title = None
        self.sub_title = None
        self.summary = None

    def parse_html_to_tree(self, soup):
        tags = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'table', 'span', 'li'], recursive=True)
        for tag in tags:
            if tag.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(tag.name[1])  # h1 -> 1, h2 -> 2, ...
                #print(f'[node dump] {str(tag)}')
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
            elif tag.name == 'p' or tag.name == 'span' or tag.name == 'li':
                self.current_node.add_item(tag.get_text(strip=True))

    def display_tree(self, node=None, indent=0):
        if node is None:
            node = self.root
        print(' ' * indent + repr(node))
        for child in node.children:
            self.display_tree(child, indent + 2)

    def collect_data_from_nodes(self, node=None, collected_data=None):
        if node is None:
            node = self.root
        if collected_data is None:
            collected_data = {}

        # キーワードにマッチするかどうか確認し、マッチしたらJSONデータを集める
        for key, keywords in self.columns.items():
            if node.matches_keywords(keywords):
                if node.level < self.item_level:
                    self.item_level = node.level
                collected_data[key] = {
                    'items': node.get_content()
                }
                #print(f'match collected_data={str(collected_data[key])}')

        # 子ノードも再帰的に処理
        for child in node.children:
            self.collect_data_from_nodes(child, collected_data)

        return collected_data


    def create_title(self, node=None):

        if node is None:
            node = self.root

        # 項目検出層より上
        if node.level >= self.item_level:
            return 
        elif node.level > 0 and self.title is None:
            if node.title == "":
                return
            self.title = []
            self.title.append(node.title)
            self.summary = node.get_content(th=self.item_level)

        # 子ノードも再帰的に処理
        for child in node.children:
            self.create_title(child)




class Html2HtagLayerStep:
    def __init__(self, step_config):
        self.progress_json_path = step_config['progress_file']
        self.output_json_dir = step_config['output_json_dir']
        self.columns_yaml = step_config['columns_yaml']
        self.url_mapping = self.load_mapping()
        # BERTモデルとトークナイザーの初期化
        self.tokenizer = BertTokenizer.from_pretrained('cl-tohoku/bert-base-japanese-v3')
        self.model = BertModel.from_pretrained('cl-tohoku/bert-base-japanese-v3')
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

    def result_check(self, html_converter):
        if html_converter.title == ["利用者別に探す"]:
            print(f'result_check: false(利用者別に探す)')
            return False
        else:
            print(f'result_check: OK')
            return True
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
                        extractor = HtmlConverter(soup, url, self.column_manager.get_column_config())
                        service_info = extractor.collect_data_from_nodes()
                        # 空の要素は飛ばす
                        if len(service_info) == 0:
                            continue
                        if not self.result_check(extractor):
                            continue
                        extractor.create_title()
                        service_info['正式名称'] = {
                            'items': extractor.title
                        }
                        service_info['概要'] = {
                            'items': extractor.summary
                        }
                        service_info['URL'] = {
                            'items': url
                        }

                        service_json = json.dumps(service_info, ensure_ascii=False, indent=4)
                        service_hash = self.generate_hash(service_json)
                        if service_hash not in unique_hashes:
                            unique_hashes.add(service_hash)
                            unique_tables.append(service_info)
                    except ValueError as e:
                        print(f"Failed to parse html: {e}")
                        print(f"  error URL : {url}")
                    except IndexError as e:
                        print(f"Table format error: {e}")
                        print(f"  error URL : {url}")
                else:
                    print(f'処理対象の単語がふくまれていません')

        self.save_json(unique_tables, self.output_json_dir)
        self.save_embedding(unique_tables, self.output_json_dir)

    def should_process(self, soup):
        main_div = soup.find('div', id='contents')
        if main_div:
            headers = main_div.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        else:
            print(f'not found main')
            return False

        if headers:
            # 最初の見出しタグの次の兄弟要素から終わりまでの内容を抽出
            #relevant_content = ''.join(str(sibling) for header in headers for sibling in header.find_all_next(string=True))
            relevant_content = ' '.join(tag.get_text() for tag in headers)
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
        #print(f"relevant keywords : {relevant_content}")
        print(f"matched keywords : {matched_keywords}")

        return include and not exclude

    def save_table_to_json(self, file_path):
        with open(f'{file_path}/service_catalog.json', "w", encoding="utf-8") as f:
            json.dump(self.unique_services, f, ensure_ascii=False, indent=4)

    def save_json(self, data, file_path):
        with open(f'{file_path}/service_catalog.json', "w", encoding="utf-8") as f:
            json_str = json.dumps(data, ensure_ascii=False, indent=4)
            # print(str(data))
            # print('---------')
            print(json_str)
            f.write(json_str)
        #self.read_and_print_json('{file_path}/service_catalog.json')

    def read_and_print_json(self,file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(data)

    def save_embedding(self, data, file_path):
        """
        サービス情報の概要テキストをベクトル化し、JSONファイルに保存する
        :param data: サービス情報のリスト
        :param file_path: 保存先のファイルパス
        """
        overview_embeddings = []
        entries = []

        for service in data:
            # 概要テキストを取得
            overview_items = service.get('概要', {}).get('items', [])
            if isinstance(overview_items, list):
                overview = " ".join(overview_items)
            elif isinstance(overview_items, str):
                overview = overview_items
            else:
                print(f"Invalid format: {overview_items}")
                continue  # 不正な形式はスキップ

            # テキストが空でない場合のみ処理
            if overview:
                embedding = self.get_embedding(overview)
                overview_embeddings.append(embedding)

                entry = {
                    'overview': overview,
                    'formal_name': service.get('正式名称', {}).get('items', ['N/A'])[0],
                    'url': service.get('URL', {}).get('items', 'N/A')
                }
                entries.append(entry)

        # JSONデータとして保存
        self.save_embeddings_to_file(overview_embeddings, entries, f'{file_path}/service_catalog_embeddings.json')

    def get_embedding(self, text):
        """
        テキストをBERTモデルを使用してベクトル化する
        :param text: テキスト
        :return: ベクトルデータ
        """
        inputs = self.tokenizer(text, return_tensors='pt', max_length=512, truncation=True)
        outputs = self.model(**inputs)
        embedding = outputs.last_hidden_state.mean(dim=1)
        return embedding.squeeze(0).detach().numpy()

    def save_embeddings_to_file(self, embeddings, entries, output_file):
        """
        ベクトルデータをJSONファイルに保存する
        :param embeddings: ベクトルデータのリスト
        :param entries: サービス情報のリスト
        :param output_file: 保存先のファイルパス
        """
        data = {
            'embeddings': np.array(embeddings).tolist(),
            'entries': entries
        }
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
