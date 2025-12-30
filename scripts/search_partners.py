import os
import sys

# Asegurar que el directorio raíz del proyecto está en sys.path
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from odoo_manager import OdooManager

patterns = [
    'VETERMEX H',
    'VETERMEX',
    'LABORATORIOS QUIMIO-VET, C.A.',
    'QUIMIO-VET',
    'QUIMIO',
]

def search_pattern(mgr, pat):
    try:
        # Usar domain ilike para buscar coincidencias en res.partner
        domain = [[('name', 'ilike', pat)]]
        partners = mgr.models.execute_kw(mgr.db, mgr.uid, mgr.password, 'res.partner', 'search_read', domain,
                                         {'fields': ['id', 'name', 'country_id'], 'limit': 200})
        return partners
    except Exception as e:
        print('Error buscando patrón', pat, e)
        return []


def main():
    m = OdooManager()
    if not m.uid or not m.models:
        print('No hay conexión a Odoo (uid/models None).')
        return

    all_matches = {}
    for p in patterns:
        results = search_pattern(m, p)
        all_matches[p] = results

    for pat, res in all_matches.items():
        print('---', pat, '=>', len(res), 'result(s)')
        for r in res:
            cid = r.get('id')
            name = r.get('name')
            country = ''
            if r.get('country_id') and isinstance(r.get('country_id'), list):
                country = r['country_id'][1]
            print(cid, name, country)

if __name__ == '__main__':
    main()
