import os
import sys
from dotenv import load_dotenv

# Asegurar que el directorio raíz del proyecto está en sys.path
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

load_dotenv()

from google_sheets_manager import GoogleSheetsManager


def main():
    sheet_name = os.getenv('GOOGLE_SHEET_NAME', 'MetasDashboardVentas')
    gs = GoogleSheetsManager(credentials_file='credentials.json', sheet_name=sheet_name)

    year = '2025'

    # Valores provistos por el usuario (números sin comas)
    # LABORATORIOS QUIMIO-VET, C.A. -> partner_id 37979
    # VETERMEX H -> partner_id 48808
    nuevos = {
        '37979': {
            'cliente_nombre': 'LABORATORIOS QUIMIO-VET, C.A.',
            'agrovet': 508284.0,
            'petmedica': 0.0,
            'avivet': 0.0
        },
        '48808': {
            'cliente_nombre': 'VETERMEX H',
            'agrovet': 87358.0,
            'petmedica': 250000.0,
            'avivet': 14198.0
        }
    }

    try:
        metas = gs.read_metas_por_cliente() or {}
        if year not in metas:
            metas[year] = {}

        # Merge: conservar otras metas y reemplazar/añadir estas
        for cid, data in nuevos.items():
            existing = metas[year].get(cid, {})
            # Merge values, override with provided
            merged = existing.copy()
            merged.update(data)
            metas[year][cid] = merged

        gs.write_metas_por_cliente(metas)
        print('Metas actualizadas y escritas en Google Sheets para año', year)
    except Exception as e:
        print('Error actualizando metas:', e)


if __name__ == '__main__':
    main()
