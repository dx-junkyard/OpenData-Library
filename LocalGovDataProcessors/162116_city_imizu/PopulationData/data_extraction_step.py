import pandas as pd
import camelot
import fitz  # PyMuPDF
import glob
import os


class DataExtractionStep:
    def __init__(self, name, step_type, config):
        self.name = name
        self.step_type = step_type
        self.config = config

    def execute(self):
        input_dir = self.config['input_dir']
        output_dir = self.config['output_dir']

        # ディレクトリが存在しない場合は作成
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        # データ抽出の実装...
        self.imizu_pop_norm(input_dir,output_dir)


    def imizu_pop_norm(self,input_folder, output_folder):
        """
        指定されたフォルダ内の全てのPDFファイルを処理する関数。
        """
        # 指定されたフォルダ内の全てのPDFファイルを検索
        pdf_files = glob.glob(os.path.join(input_folder, '*.pdf'))
    
        for pdf_path in pdf_files:
            self.process_pdf_file(pdf_path, output_folder)

    def process_pdf_file(self,pdf_path, output_folder):
        """
        指定されたPDFファイルからデータを抽出し、CSVファイルとして出力する関数。
        """
        # PDFから表を抽出
        tables = camelot.read_pdf(pdf_path, pages="1-end", flavor='stream')
    
        # データフレームの初期化
        age_data = {'年齢': [], '男': [], '女': [], '計': []}
    
        # 各ページの表からデータを抽出
        for table in tables:
            df = table.df  # 表をデータフレームとして取得
            for i, row in df.iterrows():
                if i < 2 or not row[0].strip():
                    continue
                for j in range(0, len(row), 4):
                    if not row[j].strip():
                        continue
                    age = row[j].strip().replace(' ', '')
                    if age == '計':
                        continue
                    male = row[j+1].strip().replace(' ', '')
                    female = row[j+2].strip().replace(' ', '')
                    total = row[j+3].strip().replace(' ', '')
                    age_data['年齢'].append(age)
                    age_data['男'].append(male)
                    age_data['女'].append(female)
                    age_data['計'].append(total)
    
        # データフレームを作成
        age_df = pd.DataFrame(age_data)
        age_df['年齢'] = pd.to_numeric(age_df['年齢'], errors='coerce')
        age_df_sorted_correct_order = age_df.sort_values(by='年齢').reset_index(drop=True)
    
        # 出力ファイル名を設定
        output_filename = os.path.splitext(os.path.basename(pdf_path))[0] + '.csv'
        correct_order_csv_path = os.path.join(output_folder, output_filename)
    
        # CSVとして出力
        age_df_sorted_correct_order.to_csv(correct_order_csv_path, index=False)
        print(f"CSVファイルが作成されました: {correct_order_csv_path}")
