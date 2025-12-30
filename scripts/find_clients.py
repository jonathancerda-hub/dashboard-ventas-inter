import os
import sys

# Asegurar que el directorio raíz del proyecto está en sys.path
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from odoo_manager import OdooManager


def main():
    try:
        m = OdooManager()
        clients = m.get_filter_options().get('clientes', [])
        print("TOTAL_CLIENTES:", len(clients))
        matches = []
        for pid, name in clients:
            uname = (name or '').upper()
            if 'QUIMIO' in uname or 'VETERMEX' in uname:
                matches.append((pid, name))
        if matches:
            print('MATCHES_FOUND:')
            for pid, name in matches:
                print(pid, name)
        else:
            print('NO_MATCH')
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
