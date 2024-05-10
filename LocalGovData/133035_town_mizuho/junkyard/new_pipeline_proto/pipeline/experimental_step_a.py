import MeCab
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

japanese_stop_words = ['の', 'に', 'は', 'を', 'た', 'が']

class ExperimentalStepA:
    def __init__(self, step_config):
        self.json_file_path = step_config.get('input_json_path', "./service.bk.json")
        self.output_json_path = step_config.get('output_json_path', "./service.json")
        self.n_clusters = step_config.get('n_clusters', 5)

    def mecab_tokenizer(self, text):
        m = MeCab.Tagger()
        return [token.split('\t')[0] for token in m.parse(text).split('\n') if token.strip() != 'EOS' and token.strip() != '']

    def execute_service_cluster(self):
        self.data = self.load_json_data()
        self.services = [item['service'] for item in self.data]
        self.cluster_services(self.n_clusters)
        self.save_clustered_data_to_json(self.output_json_path)

    def execute(self):
        self.data = self.load_json_data()
        self.details_texts = self.prepare_details_texts()
        self.services = [item['service'] for item in self.data]
        self.cluster_services_based_on_details(self.n_clusters)
        self.save_clustered_data_to_json(self.output_json_path)

    def load_json_data(self):
        """JSONファイルを読み込む"""
        with open(self.json_file_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    def prepare_details_texts(self):
        """detailsからテキストデータを準備する"""
        details_texts = []
        for item in self.data:
            details_text = ''
            for detail in item['details']:
                if isinstance(detail, dict):
                    # テキスト、リスト、テーブルデータを文字列に変換
                    text_parts = [v for k, v in detail.items() if isinstance(v, (list, str))]
                    text = ', '.join(text_parts) if text_parts else ''
                else:
                    text = str(detail)
                details_text += ' ' + text
            details_texts.append(details_text.strip())
        return details_texts

    def cluster_services_based_on_details(self, n_clusters=5):
        """detailsのテキストデータを基にしてserviceをクラスタリングし、結果を元のデータに追加する"""
        vectorizer = TfidfVectorizer(stop_words='english')
        X = vectorizer.fit_transform(self.details_texts)
        
        model = KMeans(n_clusters=n_clusters, random_state=42)
        model.fit(X)
        
        clusters = model.predict(X)
        
        # 元のデータにクラスタIDを追加
        for item, cluster_id in zip(self.data, clusters):
            item['cluster_id'] = int(cluster_id)
    
    def cluster_services(self, n_clusters=5):
        """サービスをクラスタリングし、結果を元のデータに追加する"""
        #vectorizer = TfidfVectorizer(stop_words='english')
        vectorizer = TfidfVectorizer(tokenizer=self.mecab_tokenizer, stop_words=japanese_stop_words)
        X = vectorizer.fit_transform(self.services)
        
        model = KMeans(n_clusters=n_clusters, random_state=42)
        model.fit(X)
        
        clusters = model.predict(X)
        
        # 元のデータにクラスタIDを追加
        for item, cluster_id in zip(self.data, clusters):
            item['cluster_id'] = int(cluster_id)

    def save_clustered_data_to_json(self, output_json_path):
        """クラスタリング結果を含むデータをクラスター番号順にソートしてJSONファイルに保存する"""
        sorted_data = sorted(self.data, key=lambda x: x['cluster_id'])
        
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(sorted_data, f, ensure_ascii=False, indent=4)
    
    def save_clustered_data_to_json_bk(self, output_json_path):
        """クラスタリング結果を含むデータをJSONファイルに保存する"""
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    

