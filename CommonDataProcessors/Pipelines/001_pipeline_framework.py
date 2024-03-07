import sys
from step_factory import StepFactory
import yaml

# ステップクラスのインポート
from download_step import DownloadStep
from data_extraction_step import DataExtractionStep

# ステップをファクトリーに登録
StepFactory.register_step('download', DownloadStep)
StepFactory.register_step('data_extraction', DataExtractionStep)

def execute_pipeline(pipeline_config_path):
    with open(pipeline_config_path, 'r') as file:
        pipeline_config = yaml.safe_load(file)

    for step_config in pipeline_config.get('steps', []):
        step = StepFactory.create_step(step_config['type'], step_config['name'], step_config['type'], step_config)
        step.execute()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        execute_pipeline(sys.argv[1])

