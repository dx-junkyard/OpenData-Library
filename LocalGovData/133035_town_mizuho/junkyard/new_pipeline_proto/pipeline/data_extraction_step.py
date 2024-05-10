import json
import os

class DataExtractionStep:
    def __init__(self, step_config):
        self.input_dir = step_config.get('input_dir', "./input")
        self.output_dir = step_config.get('output_dir', "./output")

    def execute(self):
        unique_hashes = set()  # 生成されたハッシュ値を保持するセット
        unique_events = []
