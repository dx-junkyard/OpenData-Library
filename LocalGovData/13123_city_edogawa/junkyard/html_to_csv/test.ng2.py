import yaml
import pandas as pd
from bs4 import BeautifulSoup

class InfoExtractor:
    def __init__(self, html_path, yaml_path):
        self.html_path = html_path
        self.yaml_path = yaml_path
        self.columns = {}
        self.load_yaml()

    def load_yaml(self):
        with open(self.yaml_path, 'r', encoding='utf-8') as file:
            data = yaml.load(file, Loader=yaml.FullLoader)
            self.columns = data['columns']

    def extract_info(self):
        with open(self.html_path, 'r', encoding='utf-8') as file:
            html_content = file.read()

        soup = BeautifulSoup(html_content, 'html.parser')
        data = {}
        detected_keys = set()

        for i in range(1, 7):
            headers = soup.find_all(f'h{i}')
            for header in headers:
                header_text = header.get_text(strip=True)
                next_tag = header.find_next_sibling()
                header_hierarchy = [header_text]

                while next_tag and next_tag.name not in [f'h{j}' for j in range(1, 7)]:
                    if next_tag.name in ['p', 'ul', 'li']:
                        value = next_tag.get_text(separator=' ', strip=True)
                        for key, values in self.columns.items():
                            if any(val in header_text for val in values):
                                data[key] = value
                                detected_keys.add(key)
                                break
                    next_tag = next_tag.find_next_sibling()

                # キーが発見されなかった場合には他の列名として考慮
                if header_text not in detected_keys and next_tag and next_tag.name in ['p', 'ul', 'li']:
                    data[header_text] = next_tag.get_text(separator=' ', strip=True)

        # YAMLで指定されたが未検出の列を追加
        for key in self.columns.keys():
            if key not in detected_keys:
                data[key] = None

        # 施設名が最初に移動
        if '施設名' in data:
            facility_name = data.pop('施設名')
            data = {'施設名': facility_name, **data}

        return data

    def save_to_csv(self, data, filename):
        df = pd.DataFrame([data])
        df.to_csv(filename, index=False)
        print("情報がCSVファイルに保存されました。")

# 使用例
extractor = InfoExtractor('./greenpalace.html', './columns.yaml')
info = extractor.extract_info()
extractor.save_to_csv(info, './extracted_info_detailed.csv')

