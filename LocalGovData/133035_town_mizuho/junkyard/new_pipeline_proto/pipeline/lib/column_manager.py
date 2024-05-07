import os
import yaml
import pandas as pd

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

    def get_column_config(self):
        return self.column_config

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
        print(f'check node title = {node.title}')
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
        service['概要'] = "  ".join(node.items)
        for child in node.children:
            service[child.title] = "  ".join(child.items)
        print(f'find table : title = {service["名称"]}, summary = {service["概要"]}')
        node.htag_tables.append(pd.DataFrame([service]))
            

