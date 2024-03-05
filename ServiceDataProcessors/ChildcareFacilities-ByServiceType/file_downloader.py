import requests
import os
import json

def download_file(url, save_path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        return True
    except requests.RequestException:
        return False

def main():
    config_file = "download_config.json"
    download_dir = "./sample_data"
    download(config_file, 'files', download_dir)
    download(config_file, 'converters', download_dir)

def download(config_file, target, download_dir):
    # JSONファイルの読み込み
    print("download config : " + config_file)
    with open(config_file, 'r') as f:
        config = json.load(f)

    # ディレクトリが存在しない場合は作成
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)

    for item in config.get(target, []):
        download_url = item.get('url')
        default_url = item.get('cache_url')
        filename = item.get('filename')

        save_path = os.path.join(download_dir, filename)

        # ファイルのダウンロード
        if not download_file(download_url, save_path):
            print(f"Failed to download from {download_url}. Trying default URL...")
            if not download_file(default_url, save_path):
                print(f"Failed to download from default URL {default_url} as well.")

if __name__ == "__main__":
    main()

