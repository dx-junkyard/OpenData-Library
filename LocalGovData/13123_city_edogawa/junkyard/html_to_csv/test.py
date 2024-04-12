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

        # Initialize facility_name_found as False
        facility_name_found = False

        for header in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
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

    def save_to_csv(self, data, filename):
        df = pd.DataFrame([data])
        df.to_csv(filename, index=False)
        print("Information saved to CSV file.")


# Usage example
extractor = InfoExtractor('./greenpalace.html', './columns.yaml')
info = extractor.extract_info()
extractor.save_to_csv(info, './output.csv')

