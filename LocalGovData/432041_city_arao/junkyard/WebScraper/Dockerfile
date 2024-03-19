FROM python:3.9

COPY ./app /app

# 作業ディレクトリを設定
WORKDIR /work

RUN pip install --no-cache-dir -r /app/requirements.txt

CMD python /app/arao_web.py


