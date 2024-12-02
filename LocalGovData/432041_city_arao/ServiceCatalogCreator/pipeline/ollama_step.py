import os
import json
import yaml
import hashlib
import pandas as pd
from bs4 import BeautifulSoup
from openai import OpenAI
import logging

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



class OllamaStep:
    def __init__(self, step_config):
        self.progress_file_path = step_config['progress_file']
        self.input_json_path = step_config['input_json_file']
        self.output_json_path = step_config['output_json_file']
        self.progress_data = None
        self.url_to_filepath = None
        self.ollama_client = OllamaClient()

    def load_progress(self):
        """Load the progress JSON file once."""
        if self.progress_data is None:
            if not os.path.exists(self.progress_file_path):
                raise FileNotFoundError(f"{self.progress_file_path} does not exist.")
            with open(self.progress_file_path, "r", encoding="utf-8") as file:
                self.progress_data = json.load(file)
            self.url_to_filepath = self.progress_data.get("visited", {})

    def get_file_content(self, url):
        """Retrieve content from file corresponding to the URL."""
        self.load_progress()  # Ensure progress file is loaded

        # Check if URL exists in visited
        file_path = self.url_to_filepath.get(url)
        if file_path and os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        else:
            return None

    def load_data(self):
        """Load the JSON data file."""
        if not os.path.exists(self.input_json_path):
            raise FileNotFoundError(f"{self.input_json_path} does not exist.")
        with open(self.input_json_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def get_url_content(self):
        """Replace the '概要' field with a summary from OllamaStep.create_summary()."""
        data = self.load_data()
        total_entries = len(data)

        for index, entry in enumerate(data):
            url = entry.get("URL", {}).get("items")
            if url:
                html_content = self.get_file_content(url)
                if html_content:
                    # Replace the '概要' field with the summary
                    soup = BeautifulSoup(html_content, 'html.parser')
                    main_div = soup.find('div', id='contents')
                    entry["概要"] = self.ollama_client.create_summary(main_div)
            # 進捗の割合を計算して画面に表示する
            progress = (index + 1) / total_entries * 100
            logging.info(f"Progress: {progress:.2f}% ({index + 1}/{total_entries})")
        return data

    def execute(self):
        data = self.get_url_content()
        
        # 変更点：概要フィールドの形式を修正し、itemsとしてリストで保持
        for entry in data:
            if "概要" in entry:
                entry["概要"] = {"items": entry["概要"]}

        with open(self.output_json_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)


class OllamaClient:
    def __init__(self):
        # OpenAIクライアントのセットアップ
        self.client = OpenAI(
#            base_url='http://localhost:11434/v1/',
            base_url='http://host.docker.internal:11434/v1/',
            api_key='ollama',
        )

    def create_summary(self, content):
        prompt_new = f"""
        以下の内容を日本語で利用者向けのにサービスの説明を要約してほしい。

        {content}
        """
        prompt = f"""
        以下の内容から、施設やサービスに関する概要を3つの短い文で要約してください：

        {content}

        出力形式：
        1. [1つ目の要約文]
        2. [2つ目の要約文]
        3. [3つ目の要約文]
        注意事項：
    1. 提供されたテキスト内にある情報のみを使用し、外部情報は使用しないでください。
    2. 各項目の情報は、必ず提供されたテキスト内に存在することを確認してから出力してください。
    3. 抽出した情報は可能な限り簡潔にし、余分な説明は避けてください。
    4. 出力前に正確な内容か、仮説と反証して、確認しろ
        """

        try:
            chat_completion = self.client.chat.completions.create(
                model='qwen2.5-coder:7b-instruct',
#                model='llama3',
                messages=[
                    {
                        'role': 'user',
                        'content': prompt_new,
                    }
                ]
            )
            response = chat_completion.choices[0].message.content
            logging.info("LLMの応答を受信しました")
            return response.split('\n')
        except Exception as e:
            logging.error(f"LLMの呼び出しに失敗しました: {str(e)}")
            return []

