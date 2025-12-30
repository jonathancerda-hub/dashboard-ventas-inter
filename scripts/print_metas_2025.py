import os
import sys
from dotenv import load_dotenv

# Asegurar que el directorio raíz del proyecto está en sys.path
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from google_sheets_manager import GoogleSheetsManager

load_dotenv()

gs = GoogleSheetsManager(credentials_file='credentials.json', sheet_name=os.getenv('GOOGLE_SHEET_NAME'))
metas = gs.read_metas_por_cliente() or {}
if '2025' in metas:
    print('--- Metas 2025 ---')
    for cid, data in metas['2025'].items():
        print(cid, data)
else:
    print('No hay metas para 2025')
