import os
import argparse
import pandas as pd

def process_csv_header(file_path):
    with open(file_path, 'r') as f:
        header = f.readline().strip()
        # ヘッダーのダブルクォーテーションを除去
        header = header.replace('"', '')
        columns = header.split(',')
    return columns

def save_processed_csv(file_path, columns, new_file_path):
    # CSVファイルを読み込む
    df = pd.read_csv(file_path, skiprows=1, header=None)
    df.columns = columns
    
    # 新しいファイル名を生成
    dir_name = os.path.dirname(file_path)
    
    # 処理済みのデータを新しいファイル名で保存
    df.to_csv(new_file_path, index=False)
    
    return new_file_path

def fix_broken_header(file_path, new_file_path):
    columns = process_csv_header(file_path)
    processed_path = save_processed_csv(file_path, columns, new_file_path)
    return processed_path

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fix CSV file header.')
    parser.add_argument('csv_path', type=str, help='Path to the CSV files.')
    args = parser.parse_args()
    base_name = os.path.basename(args.csv_path)
    dir_name = os.path.dirname(args.csv_path)
    new_file_name = "fixed_" + base_name
    new_file_path = os.path.join(dir_name, new_file_name)
    fix_broken_header(args.csv_path, new_file_path)
    print(f"Fixed file saved at: {new_file_path}")

