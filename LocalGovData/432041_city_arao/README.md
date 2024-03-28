# 荒尾市のデータ

## 1. 行政サービスのカタログを作成
### ダウンロード定義の指定
```
export PIPELINE_DL_DEF="https://raw.githubusercontent.com/dx-junkyard/OpenData-Library/main/LocalGovData/432041_city_arao/ServiceCatalogCreator/pipeline_download.json"
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

### 注意点
- 上記の手順どおり実行市た場合、指定サイト内のファイル収集が完了するまで止まりません。Macであれば control + c 等で適当なところで中断させてください。
- 処理結果は100ダウンロード単位でprogress.jsonに途中経過が記録され、"docker-compose up"で中断したところから再開します。
- ある程度ファイルが溜まった段階で、[./pipeline/pipeline.yamlのskip_flg](https://github.com/dx-junkyard/OpenData-Library/blob/ura/LocalGovData/432041_city_arao/ServiceCatalogCreator/pipeline/pipeline.yaml#L9)の値をyesもしくは項目削除することで、スクレイピングをスキップし、ダウンロード済のファイルをもとにカタログ作成に移行することができます。

