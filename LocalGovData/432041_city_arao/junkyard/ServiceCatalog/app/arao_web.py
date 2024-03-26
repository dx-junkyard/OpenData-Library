from bs4 import BeautifulSoup
import json
import os
import hashlib

class CatalogCreator:
    def __init__(self, html_content, source_url):
        self.events = self.parse_html_to_events(html_content, source_url)

    def load_progress_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    def parse_html_to_events(self, html_content, source_url):
        soup = BeautifulSoup(html_content, 'html.parser')
        events = []
        current_h1 = ""
        for tag in soup.find_all(['h1', 'h2']):
            if tag.name == 'h1':
                current_h1 = tag.text.strip()
            elif tag.name == 'h2':
                service_name = f"{current_h1} - {tag.text.strip()}"
                details = self.extract_details(tag)
                events.append({
                    "service": service_name,
                    "details": details,
                    "url": source_url
                })
        return events

    def extract_details(self, start_tag):
        details = []
        next_tag = start_tag.find_next_sibling()
        while next_tag and next_tag.name not in ['h1', 'h2']:
            if next_tag.name in ['h3', 'h4', 'p', 'ul', 'table']:
                details.append(self.handle_detail_tag(next_tag))
            next_tag = next_tag.find_next_sibling()
        return details

    def handle_detail_tag(self, tag):
        if tag.name == 'ul':
            return {"list": [li.text.strip() for li in tag.find_all('li')]}
        elif tag.name == 'table':
            return {"table": self.extract_table_data(tag)}
        else:
            return {"text": tag.text.strip()}

    def extract_table_data(self, table):
        rows = []
        for tr in table.find_all('tr'):
            cols = tr.find_all(['td', 'th'])
            rows.append([col.text.strip() for col in cols])
        return rows
    def get_events(self):
        return self.events


class CatalogManager:
    def __init__(self, progress_json_path):
        self.progress_json_path = progress_json_path
        self.url_mapping = self.load_mapping()
        self.events = []

    def load_mapping(self):
        """マッピング情報を読み込む"""
        with open(self.progress_json_path, 'r') as file:
            mapping = json.load(file)
        return mapping

    def generate_hash(self, details):
        # detailsをJSON文字列に変換し、そのハッシュ値を生成
        details_str = json.dumps(details, sort_keys=True)
        return hashlib.sha256(details_str.encode('utf-8')).hexdigest()
    
    def analyze_htmls(self,json_file):
        unique_hashes = set()  # 生成されたハッシュ値を保持するセット
        unique_events = []

        for url, filepath in self.url_mapping.items():
            if filepath.endswith('.html'):
                with open(filepath, 'r', encoding='utf-8') as file:
                    html_content = file.read()
                creator = CatalogCreator(html_content, url)
                for event in creator.get_events():
                    event_hash = self.generate_hash(event['details'])
                    if event_hash not in unique_hashes:
                        unique_hashes.add(event_hash)
                        unique_events.append(event)
        self.events = unique_events
        self.save_events_to_json(json_file)

    def save_events_to_json(self, file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.events, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":
    # Replace 'progress.json' with the correct path to your progress file
    progress_json_path = os.getenv('PROGRESS', './app/progress.json')
    output_json_path = os.getenv('OUTPUT', './services.json')
    catalog_manager = CatalogManager(progress_json_path)
    catalog_manager.analyze_htmls(output_json_path)
