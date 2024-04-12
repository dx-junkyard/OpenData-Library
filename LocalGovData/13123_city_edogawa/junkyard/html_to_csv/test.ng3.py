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

        # Improved header extraction method
        for i in range(1, 7):
            headers = soup.find_all(f'h{i}')
            for header in headers:
                current_tag = header.next_sibling
                while current_tag and current_tag.name not in [f'h{j}' for j in range(1, 7)]:
                    if hasattr(current_tag, 'text') and current_tag.text.strip():
                        text_content = ' '.join(current_tag.text.split())
                        # Matching section titles to YAML column names
                        for key, values in self.columns.items():
                            if any(value in header.text for value in values):
                                data[key] = text_content
                                break
                        # Handling data without specific YAML keys
                        if header.text.strip() not in data:
                            data[header.text.strip()] = text_content
                    current_tag = current_tag.next_sibling

        # Ensure facility name is handled correctly
        if '施設名' not in data:
            if headers:
                data['施設名'] = headers[0].text.strip()

        return data

    def save_to_csv(self, data, filename):
        df = pd.DataFrame([data])
        df.to_csv(filename, index=False)
        print("Information saved to CSV file.")

# Usage example
extractor = InfoExtractor('./greenpalace.html', './columns.yaml')
info = extractor.extract_info()
extractor.save_to_csv(info, './output.csv')

