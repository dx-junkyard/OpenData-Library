import json
import os

class AttributionProcStep:
    def __init__(self, name, step_type, step_config):
        self.name = name
        self.step_type = step_type
        # `config`が文字列（ファイルパス）の場合、その内容を読み込む
        with open(step_config['config'], 'r') as f:
            self.config_json = json.load(f)
        self.output_dir = step_config['output_dir']
        # ダウンロードディレクトリが存在しない場合は作成
        os.makedirs(self.output_dir, exist_ok=True)

    def execute(self):
        attribution_info = self.extract_info_from_json(self.config_json)
        readme_path = self.output_dir + "/README.md"
        with open(readme_path, mode='w') as f:
            f.write(attribution_info)

    def extract_info_from_json(self,json_data):
        # タイトルと説明の抽出
        title = json_data["title"]
        description = json_data["description"]
    
        # 出典情報の抽出と重複排除
        attributions = set(item["attribution"] + "（License : " + item["license"] + "）" for item in json_data["files"])
        attribution = "、".join(attributions)
    
        # 出力結果の生成
        output = self.generate_markdown_table(json_data)
        output += f"\n\n# 利用について\n本データは後述する出典元のライセンスを考慮の上、ご利用ください。\nその他の制限はありません。\n\n```\n出典：本データは、{attribution}が公開する、{title}に関する情報を基に作成されました。\n"
        output += "加工内容の説明：" + description + "\n```"
    
        return output
    def generate_markdown_table(self, json_data):
        # タイトルの取得
        title = json_data["title"]
    
        # テーブルヘッダーの作成
        markdown_table = f"# データの説明\n## {title}\n"
        markdown_table += "|title|file名|\n"
        markdown_table += "|----|----|\n"
    
        # ファイル情報の取得とテーブルへの追加
        for file_info in json_data["files"]:
            markdown_table += f"|{file_info['title']}|{file_info['filename'].replace('.pdf', '.csv')}|\n"
    
        return markdown_table
    
    
