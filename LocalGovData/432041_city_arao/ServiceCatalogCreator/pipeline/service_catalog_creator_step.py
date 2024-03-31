from bs4 import BeautifulSoup
import json
import os
import hashlib



class CatalogCreator:
    def __init__(self, html_content, source_url):
        self.source_url = source_url
        self.html_content = html_content
        self.services = self.parse_html_to_services()

    def parse_html_to_services(self):
        soup = BeautifulSoup(self.html_content, 'html.parser')
        services = []
        hierarchy_stack = []  # 階層スタック

        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'li', 'table', 'a']):
            if tag.name.startswith('h'):
                level = int(tag.name[1])  # hタグの階層レベル（1〜6）
                # 現在の階層より上の階層まで戻る
                while hierarchy_stack and len(hierarchy_stack) >= level:
                    hierarchy_stack.pop()

                new_service = {
                    'service': tag.text.strip(),
                    'details': [],
                    'url': self.source_url if not hierarchy_stack else ''  # 最上位階層にのみURLを設定
                }

                if hierarchy_stack:
                    hierarchy_stack[-1]['details'].append({k: v for k, v in new_service.items() if k != 'url' and v})
                else:
                    services.append(new_service)

                hierarchy_stack.append(new_service)
            else:
                if hierarchy_stack:
                    details_content = self.handle_detail_tag(tag)
                    if details_content:
                        hierarchy_stack[-1]['details'].append(details_content)

        # 中身が空のdetailsを持つ要素を削除
        services = [service for service in services if service['details']]

        return services

    def handle_detail_tag(self, tag):
        # 各タグの内容を処理
        if tag.name == 'ul':
            return [self.handle_detail_tag(li) for li in tag.find_all('li')]
        elif tag.name == 'li':
            return tag.text.strip()
        elif tag.name == 'table':
            return [[self.handle_detail_tag(td) for td in tr.find_all(['td', 'th'])] for tr in tag.find_all('tr')]
        elif tag.name == 'a':
            return {'href': tag.get('href')}
        else:
            return tag.text.strip()

    def get_services(self):
        return self.services





class ServiceCatalogCreatorStep:
    def __init__(self, step_config):
        self.progress_json_path = step_config['progress_file']
        self.output_json_path = step_config['output_json_path']
        self.url_mapping = self.load_mapping()
        self.services = []

    def load_mapping(self):
        """マッピング情報を読み込む"""
        with open(self.progress_json_path, 'r') as file:
            data = json.load(file)
        return data.get("visited", {})

    def generate_hash(self, details):
        # detailsをJSON文字列に変換し、そのハッシュ値を生成
        details_str = json.dumps(details, sort_keys=True)
        return hashlib.sha256(details_str.encode('utf-8')).hexdigest()

    def execute(self):
        unique_hashes = set()  # 生成されたハッシュ値を保持するセット
        unique_services = []

        for url, filepath in self.url_mapping.items():
            if filepath.endswith('.html'):
                with open(filepath, 'r', encoding='utf-8') as file:
                    html_content = file.read()
                creator = CatalogCreator(html_content, url)
                for service in creator.get_services():
                    service_hash = self.generate_hash(service['details'])
                    if service_hash not in unique_hashes:
                        unique_hashes.add(service_hash)
                        unique_services.append(service)
        self.services = unique_services
        self.save_services_to_json(self.output_json_path)

    def save_services_to_json(self, file_path):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.services, f, ensure_ascii=False, indent=4)


