import json
import os

class ExperimentalStepC:
    def __init__(self, step_config):
        self.progress_json_path = step_config.get('progress_file', "./progress.json")
        self.output_json_path = step_config.get('output_json_path', "./service.json")
        self.events = []

    def execute(self):
        unique_hashes = set()  # 生成されたハッシュ値を保持するセット
        unique_events = []
