import MeCab
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

japanese_stop_words = ['の', 'に', 'は', 'を', 'た', 'が']

class ExperimentalStepB:
    def __init__(self, step_config):
        self.json_file_path = step_config.get('input_json_path', "./service.bk.json")
        self.output_json_path = step_config.get('output_json_path', "./service.json")
        self.n_clusters = step_config.get('n_clusters', 5)

    def mecab_tokenizer(self, text):
        m = MeCab.Tagger()
        return [token.split('\t')[0] for token in m.parse(text).split('\n') if token.strip() != 'EOS' and token.strip() != '']
    def execute(self):
        self.data = self.load_json_data()
        self.services = [item['service'] for item in self.data]
        self.cluster_services(self.n_clusters)
        self.save_clustered_data_to_json(self.output_json_path)

    def load_json_data(self):
        """JSONファイルを読み込む"""
        with open(self.json_file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    
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
        """クラスタリング結果を含むデータをJSONファイルに保存する"""
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    

