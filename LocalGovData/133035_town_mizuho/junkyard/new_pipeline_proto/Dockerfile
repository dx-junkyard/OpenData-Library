# Pythonのベースイメージを指定
FROM python:3.9-slim

RUN mkdir /work
RUN mkdir /app
RUN mkdir /app/pipeline

# 作業ディレクトリを設定
WORKDIR /app

# Gitをインストール
RUN apt-get update && \
    apt-get install -y git wget libgl1-mesa-glx libglib2.0-0 && \
    apt-get install -y mecab libmecab-dev mecab-ipadic-utf8  curl build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

#COPY ./app/* /app/
#COPY ./app/pipeline/* /app/pipeline/

# リポジトリをクローン
ARG PIPELINE_DL_DEF

#RUN wget "${PIPELINE_DL_DEF}" -O pipeline_download.json

#RUN pip install --no-cache-dir -r dl_requirements.txt
#RUN python pipeline_manager.py pipeline_download.json

WORKDIR /work

# 1. /work/pipelineがまだ無い場合
#   pipeline一式をコンテナイメージからmountしたローカルvolumeにコピー
# 2. 動作に必要なpythonライブラリ一式をインストール
# 3. mountしたローカルvolume上のpythonコードを実行
#   これにより、手元で編集したpythonコードをDockerコンテナ内に構築した環境で動作させられるため、試行錯誤が容易にできる
CMD if [ ! -d "/work/pipeline" ]; then cp -r /app/pipeline /work/; fi && pip install --no-cache-dir -r /work/pipeline/requirements.txt && python /work/pipeline/pipeline_framework.py /work/pipeline/pipeline.yaml

