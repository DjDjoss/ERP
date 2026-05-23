import os
import chardet

def check_sql_files_encoding(folder_path):
    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.sql'):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'rb') as f:
                rawdata = f.read()
                result = chardet.detect(rawdata)
                encoding = result['encoding']
                confidence = result['confidence']
                print(f"File: {filename} - Encoding: {encoding} (Confidence: {confidence:.2f})")

if __name__ == "__main__":
    folder = "chemin/vers/votre/dossier/sql"  # Remplacez par le chemin réel
    check_sql_files_encoding(folder)
