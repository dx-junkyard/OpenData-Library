import yaml
import pandas as pd
import json
import importlib.util
import argparse

def load_module_from_path(name, path):
    try:
        # モジュール仕様の取得
        spec = importlib.util.spec_from_file_location(name, path)

        # 仕様がNoneの場合、モジュールのロードに失敗している
        if spec is None:
            print(f"Cannot load module from {path}")
            return None

        # モジュールの作成とロード
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        return module

    except FileNotFoundError:
        print(f"File not found: {path}")
    except SyntaxError as e:
        print(f"Syntax error in {path}: {e}")
    except Exception as e:
        print(f"Error loading module from {path}: {e}")

    return None


def execute_pipeline(yaml_file):
    with open(yaml_file, 'r') as file:
        pipeline = yaml.safe_load(file)

    for step in pipeline['steps']:
        if step['type'] == 'download':
            merge_module = load_module_from_path("download", "file_downloader.py")
            merge_module.download(step['download_config'], "files", step['download_dir'])
            merge_module.download(step['download_config'], "converters", "./")
    
        elif step['type'] == 'merge':
            merge_module = load_module_from_path("merge", "datanorm.py")
            merge_module.merge(step['input_files'], step['transform_config'], step['output_file'])
       
        elif step['type'] == 'imizu_pop_norm':
            merge_module = load_module_from_path("imizu_pop_norm", "imizushi_population_data_norm.py")
            merge_module.imizu_pop_norm(step['input_dir'], step['output_dir'])
       
        elif step['type'] == 'rm_dq':
            merge_module = load_module_from_path("fix_broken_header", "fix_broken_header.py")
            merge_module.fix_broken_header(step['input_file'], step['output_file'])
       

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='pipeline exe.')
    parser.add_argument('yaml_path', type=str, help='Path to the yaml file.')
    args = parser.parse_args()
    execute_pipeline(args.yaml_path)         

