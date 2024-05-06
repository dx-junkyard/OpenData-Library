import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote
import os
import hashlib
import time
import random
import mimetypes
import chardet
import urllib.robotparser
import json  # Ensure json is imported

class WebScraperStep:
    def __init__(self, step_config):
        self.start_url = step_config['start_url']
        self.user_agent = step_config['user_agent']
        self.output_dir = step_config['output_dir']
        self.progress_file = step_config['progress_file']
        self.save_every = step_config['save_every']
        self.visited = self.load_progress()
        self.counter = 0
        progress_data = self.load_progress()
        self.visited = progress_data.get('visited', {})
        self.to_visit = progress_data.get('to_visit', [self.start_url])

    def save_progress(self):
        progress_data = {
            'visited': self.visited,
            'to_visit': self.to_visit
        }
        with open(self.progress_file, 'w') as file:
            json.dump(progress_data, file, indent=2)

    # 対象がスクレイピングOKか確認
    def is_allowed_url(self, url):
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(urllib.parse.urljoin(url, '/robots.txt'))
        parser.read()
        return parser.can_fetch(self.user_agent, url)
   
    # 進行状況を取得
    def load_progress(self):
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as file:
                return json.load(file)
        return {}

    # URLからファイルの拡張子を推定する関数
    def get_extension_from_url(self, url):
        parsed_url = urlparse(unquote(url))
        _, ext = os.path.splitext(parsed_url.path)
        return ext if ext else '.html'  # デフォルトは .html

    # 
    def save_page_content(self, url, content, response):
        # ファイル拡張子取得
        content_type = response.headers.get('Content-Type', '')
        extension = self.get_extension_from_url(url)
        # 保存先パスを作成
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        download_dir = os.getenv('OUTPUT_DIR', './output')
        filename = f"{download_dir}/{url_hash}{extension}"
        # 保存
        mode = 'wb' if content_type.startswith('image/') else 'w'
        with open(filename, mode, encoding='utf-8' if mode == 'w' else None) as file:
            file.write(content if mode == 'w' else response.content)
        # 完了履歴の追加
        print(f"Saved {url} as {filename}")
        self.visited[url] = filename
        
        # counterをインクリメントして、指定された数ごとに進行状況を保存
        self.counter += 1
        if self.counter >= self.save_every:
            self.save_progress()
            self.counter = 0  # カウンターをリセット
   
    def print_progress(self, completed, total):
        if total > 0:
            progress_percentage = (completed / total) * 100
            print(f"Progress: {completed}/{total} ({progress_percentage:.2f}%) completed.", end='\r')
 
    def scrape_site(self):
        total_urls = len(self.to_visit) + len(self.visited)  # 最初の総URL数
        completed_urls = len(self.visited)  # 最初の完了URL数
    
        download_dir = os.getenv('OUTPUT_DIR', './output')
        # Ensure the download directory exists
        os.makedirs(download_dir, exist_ok=True)

   
        while self.to_visit:
            current_url = self.to_visit.pop(0)
            if not current_url or current_url in self.visited or not self.is_allowed_url(current_url):
                continue
    
            try:
                time.sleep(random.uniform(0.5, 1.5))  # Random delay to reduce server load
                response = requests.get(current_url, headers={'User-Agent': self.user_agent})
                detected_encoding = chardet.detect(response.content)['encoding']
                response.encoding = detected_encoding

                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    self.save_page_content(current_url, response.text, response)
                    completed_urls += 1  # 完了カウントをインクリメント
                    self.print_progress(completed_urls, total_urls)  # 進捗表示の更新
    
                    for link in soup.find_all('a', href=True):
                        absolute_link = urljoin(current_url, link['href'])
                        if absolute_link not in self.visited and urlparse(absolute_link).netloc == urlparse(self.start_url).netloc:
                            self.to_visit.append(absolute_link)
    
            except Exception as e:
                print(f"Error scraping {current_url}: {e}")
                continue

        print("\nScraping completed.")  # 最後に改行を入れて終了メッセージを表示 
    def execute(self):
        self.scrape_site()


