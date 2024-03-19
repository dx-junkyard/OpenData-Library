import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import hashlib
import time
import random
import mimetypes
import chardet
import urllib.robotparser
import json  # Ensure json is imported

class WebScraper:
    def __init__(self, start_url, user_agent='Mozilla/5.0', output_dir='./output', save_every=100, progress_file='progress.json'):
        self.start_url = start_url
        self.user_agent = user_agent
        self.output_dir = output_dir
        self.progress_file = progress_file
        self.visited = self.load_progress()
        self.counter = 0
        self.save_every = 100

    # 対象がスクレイピングOKか確認
    def is_allowed_url(self, url):
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(urllib.parse.urljoin(url, '/robots.txt'))
        parser.read()
        return parser.can_fetch(self.user_agent, url)
   
    # 進行状況を保存 
    def save_progress(self):
        with open(self.progress_file, 'w') as file:
            json.dump(self.visited , file, indent=2)

    # 進行状況を取得
    def load_progress(self):
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as file:
                return json.load(file)
        return {}
  
    # 取得ファイルの拡張子を取得 
    def get_extension(self, url, content_type):
        # URLから拡張子を推測
        guessed_extension = mimetypes.guess_extension(content_type.split(';')[0], strict=False)
        if guessed_extension:
            return guessed_extension
        # URLの末尾から拡張子を取得しようと試みる
        path = urlparse(url).path
        ext = os.path.splitext(path)[1]
        if ext:
            return ext
        # デフォルトの拡張子
        return '.html'

    # 
    def save_page_content(self, url, content, response):
        # ファイル拡張子取得
        content_type = response.headers.get('Content-Type', '')
        extension = self.get_extension(url, content_type)
        # 保存先パスを作成
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
        download_dir = os.getenv('OUTPUT_DIR', './output')
        filename = f"{download_dir}/{url_hash}.html"
        # 保存
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(content)
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
        to_visit = [self.start_url if self.start_url not in self.visited else None]
        total_urls = len(to_visit) + len(self.visited)  # 最初の総URL数
        completed_urls = len(self.visited)  # 最初の完了URL数
    
        download_dir = os.getenv('OUTPUT_DIR', './output')
        # Ensure the download directory exists
        os.makedirs(download_dir, exist_ok=True)

   
        while to_visit:
            current_url = to_visit.pop(0)
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
                            to_visit.append(absolute_link)
    
            except Exception as e:
                print(f"Error scraping {current_url}: {e}")
                continue

        print("\nScraping completed.")  # 最後に改行を入れて終了メッセージを表示 

if __name__ == "__main__":
    start_url = os.getenv('TARGET_URL', 'https://www.city.arao.lg.jp/')
    user_agent = os.getenv('USER_AGENT', 'Mozilla/5.0')
    output_dir = os.getenv('OUTPUT_DIR', './output')
    progress_json = os.getenv('PROGRESS', './app/progress.json')
    save_every = os.getenv('SAVE_EVERY', 100)

    ws = WebScraper(start_url, user_agent, output_dir, save_every, progress_json)
    ws.scrape_site()

