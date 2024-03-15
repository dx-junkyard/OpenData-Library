import json
import pandas as pd
from collections import OrderedDict
import os
from glob import glob
import argparse
import chardet


def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

def load_mapping_rules(path):
    """JSONファイルからマッピングルールを読み込む"""
    with open(path, "r", encoding="utf-8") as f:
        mapping_rules = json.load(f)
    mapping_rules = OrderedDict(mapping_rules)

    return mapping_rules

def csv_conv(path,header_line):
    detected_encoding = detect_encoding(path)
    if detected_encoding == None:
        detected_encoding = 'shift_jis'
    try:
        return pd.read_csv(path, encoding=detected_encoding, header=header_line)
    except Exception as e:
        print(f"Could not read {path} with detected encoding {detected_encoding}: {e}")
        return None

def load_csv(filename):
    # 文字コード判定
    detected_encoding = detect_encoding(filename)

    # ファイルを全ての行で読み込み
    with open(filename, 'r', encoding=detected_encoding, errors='replace') as f:
        lines = f.readlines()

    header_line = 0  # ヘッダー行の初期位置

    # ヘッダー行を発見するまでの空の列を持つ行をチェック
    for idx, line in enumerate(lines):
        cells = line.strip().split(',')
        if '' in cells:
            header_line = idx + 1
        else:
            break

    # pandasでcsvを読み込み、ヘッダー行を指定
    df = csv_conv(filename, header_line)
    return df


def trans_column_name(df, mapping_rules):
    """DataFrameの列名をマッピングルールに基づいて変更する"""
    for column_name in df.columns:
        for key, value in mapping_rules.items():
            if column_name in value:
                df.rename(columns={column_name: key}, inplace=True)
                break
        else:
            print("drop column : " + column_name)
            df.drop(column_name, axis=1, inplace=True)
    return df

def main(directory_path):
    output_file = "combined.csv"
    mapping_file = "mapping_rules.json"

    """指定されたディレクトリ内のCSVファイルを読み込み、結合して新しいCSVファイルに出力する"""
    if not os.path.exists(directory_path):
        print(f"The directory {directory_path} does not exist.")

    csv_files = glob(os.path.join(directory_path, "*.csv"))
    print("CSV files in directory:", csv_files)

    merge(csv_files, mapping_file, output_file)

def merge(csv_files, mapping_config, output_file):
    mapping_rules = load_mapping_rules(mapping_config)
    combined_csv = pd.DataFrame(columns=list(mapping_rules.keys()))
    for file in csv_files:
        print("proc CSV file :" + file)
        df = load_csv(file)
        if df is None or df.empty:
            print(f"Failed to load {file}")
            continue

        # 行数を確認（変更前）
        original_row_count = len(df)

        df = trans_column_name(df, mapping_rules)

        # 行数を確認（変更後）
        new_row_count = len(df)

        # 行数が減った場合は報告
        if original_row_count != new_row_count:
            print(f"Warning: {original_row_count - new_row_count} rows were removed in {file}")
        else:
            print(f"CSV load OK.: {original_row_count} rows were loaded in {file}")


        # Ensure that the DataFrame has the same columns as combined_csv before concatenating
        for col in combined_csv.columns:
            if col not in df.columns:
                df[col] = None  # Add missing columns to df, filling with None

        # Debug output
        print(f"Processing {file}")
        print("combined_csv columns:", combined_csv.columns)
        print("df columns:", df.columns)

        # Ensure columns are in the same order
        df = df[combined_csv.columns]

        combined_csv = pd.concat([combined_csv, df], ignore_index=True, sort=False)

    combined_csv = combined_csv[list(mapping_rules.keys())]
    combined_csv.replace(to_replace='"', value='', regex=True, inplace=True)
    combined_csv.dropna(how='all', inplace=True)
    combined_csv.fillna('', inplace=True)

    combined_csv.to_csv(output_file, index=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process and combine CSV files from a specified directory.')
    parser.add_argument('directory_path', type=str, help='Path to the directory containing the CSV files.')
    args = parser.parse_args()
    main(args.directory_path)

