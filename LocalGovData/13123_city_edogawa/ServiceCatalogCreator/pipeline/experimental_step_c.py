import json
import re

class ExperimentalStepC:
    def __init__(self, step_config):
        self.json_file_path = step_config.get('input_json_path', "./service.json")
        self.output_json_path = step_config.get('output_json_path', "./service.json")
        self.filter_key = step_config.get('filter_key', "窓口,サービス,情報")

    def execute(self):
        self.keywords = [keyword.strip() for keyword in self.filter_key.split(',')]
        try:
            self.data = self.load_json_data()
        except Exception as e:
            print(f"Error loading JSON data: {e}")
            return
        try:
            results = self.extract_relevant_services(self.data, self.keywords)
        except Exception as e:
            print(f"Error extracting services: {e}")
            return
        self.save_to_json_file(results, self.output_json_path)

    def load_json_data(self):
        with open(self.json_file_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    def search_keyword_in_details(self, details, keywords):
        results = []
        for item in details:
            if isinstance(item, dict):
                href = item.get('href', '')
                if href and any(keyword in href for keyword in keywords):
                    results.append(item)
                elif 'details' in item:
                    sub_results = self.search_keyword_in_details(item['details'], keywords)
                    if sub_results:
                        results.append(item)
            elif isinstance(item, list):
                if any(keyword in str(subitem) for subitem in item for keyword in keywords):
                    results.append(item)
            elif isinstance(item, str) and any(keyword in item for keyword in keywords):
                results.append(item)
        return results

    def extract_relevant_services(self, json_data, keywords):
        relevant_services = []
        for service in json_data:
            try:
                matches = self.search_keyword_in_details(service['details'], keywords)
                if matches:
                    relevant_services.append({
                        'service': service['service'],
                        'matches': matches,
                        'url': service['url']
                    })
            except Exception as e:
                print(f"Error processing service {service['service']}: {e}")
        relevant_services = [service for service in relevant_services if service['matches']]
        return relevant_services

    def save_to_json_file(self, data, filename):
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

