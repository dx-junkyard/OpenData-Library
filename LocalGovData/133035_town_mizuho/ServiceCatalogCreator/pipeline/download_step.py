import requests
import os
import json

class DownloadStep:
    def __init__(self, name, step_type, step_config):
        self.name = name
        self.step_type = step_type
        # `config`が文字列（ファイルパス）の場合、その内容を読み込む
        with open(step_config['config'], 'r') as f:
            self.config_json = json.load(f)
        self.download_dir = step_config['output_dir']
        # ダウンロードディレクトリが存在しない場合は作成
        os.makedirs(self.download_dir, exist_ok=True)

    def download_file(self, url, save_path):
        """指定されたURLからファイルをダウンロードし、指定されたパスに保存する"""
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()  # ステータスコードが200以外の場合は例外を発生させる
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"File downloaded successfully: {save_path}")
        except requests.RequestException as e:
            print(f"Failed to download {url}: {e}")

    def execute(self):
        """ダウンロードステップを実行する"""

        for file in self.config_json['files']:
            url = file['url']
            filename = file['filename']
            save_path = os.path.join(self.download_dir, filename)
            self.download_file(url, save_path)

