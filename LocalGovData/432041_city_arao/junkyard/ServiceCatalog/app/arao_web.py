import json
from bs4 import BeautifulSoup
from collections import Counter
import re
import os
import csv


class ConsultationService:
    def __init__(self, category, name, details, contact, hours):
        self.category = category
        self.name = name
        self.details = details
        self.contact = contact
        self.hours = hours

    def __repr__(self):
        return f"{self.name} - {self.category}\n詳細: {self.details}\n連絡先: {self.contact}\n受付時間: {self.hours}"

class ServiceManager:
    def __init__(self,file_path):
        self.services = []
        if file_path.endswith('.html'):
            self.services = self.extract_consultation_services(file_path)
    def extract_consultation_services(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        soup = BeautifulSoup(html_content, 'html.parser')
        services = []
        categories = soup.find_all('h3')
    
        for category in categories:
            next_node = category.find_next_sibling()
            while next_node and next_node.name != 'h3':
                if next_node.name == 'table':
                    rows = next_node.find_all('tr')[1:]  # Skip header row
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) == 4:  # Ensure there are enough columns
                            name = cols[0].text.strip()
                            detail = cols[1].text.strip()
                            contact = cols[2].text.strip()
                            hours = cols[3].text.strip().replace('\n', ', ')
                            service = ConsultationService(category.text.strip(), name, detail, contact, hours)
                            services.append(service)
                next_node = next_node.find_next_sibling()
        
        return services

    def services_to_csv(self, file_path):
        with open(file_path, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['カテゴリ' ,'相談窓口', '詳細', '連絡先', '受付時間'])  # ヘッダー
    
            for service in self.services:
                writer.writerow([service.category, service.name, service.details, service.contact, service.hours])




if __name__ == "__main__":
    service_manager = ServiceManager('./output/f477371bf71ee5f166ff157f83e994dd.html')
    service_manager.services_to_csv('./service.csv')
    
    #progress_json_path = os.getenv('PROGRESS', './app/progress.json')
    #keyword = os.getenv('EXT_KEYWORD', '子育て')

