# 射水市のデータ

## 1. 年齢別人口データをPDFから抽出する
### ダウンロード定義の指定
```
export PIPELINE_DL_DEF="https://raw.githubusercontent.com/dx-junkyard/OpenData-Library/main/LocalGovData/162116_city_imizu/PopulationData/pipeline_download.json"
```

### 環境構築＆初回実行
```
git clone https://github.com/dx-junkyard/OpenData-Bridge-pipeline.git && cd OpenData-Bridge-pipeline && docker-compose build && docker-compose up
```

### 試行錯誤
- データ整形のためのコードと設定ファイル一式は./pipelineの下に配置されます。必要に応じて編集してください
- 以下のコマンドでコンテナを起動し、処理を再度実行します。
```
docker-compose up
```


