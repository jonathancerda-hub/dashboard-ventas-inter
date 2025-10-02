#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from odoo_manager import OdooManager

def check_limit_issue():
    print("=== VERIFICAR PROBLEMA DE LÍMITE ===")
    
    odoo = OdooManager()
    
    # Reproducir el dominio exacto de la consulta principal
    domain = [
        ('move_id.move_type', 'in', ['out_invoice', 'out_refund']),
        ('move_id.state', '=', 'posted'),
        ('product_id', '!=', False),
        ('product_id.default_code', '!=', False)
    ]
    
    # Filtros de exclusión de categorías
    excluded_categories = [315, 333, 304, 314, 318, 339]
    domain.append(('product_id.categ_id', 'not in', excluded_categories))
    
    # Filtros de fecha (2025-01-01 a 2025-12-31)
    domain.append(('move_id.invoice_date', '>=', '2025-01-01'))
    domain.append(('move_id.invoice_date', '<=', '2025-12-31'))
    
    try:
        print("🔍 Consultando TODAS las líneas que cumplen el dominio...")
        
        # Contar TODAS las líneas que cumplen el criterio
        all_lines_count = odoo.models.execute_kw(odoo.db, odoo.uid, odoo.password, 'account.move.line', 'search_count',
            [domain])
        
        print(f"📊 Total de líneas que cumplen el dominio: {all_lines_count}")
        
        # Obtener las primeras 5000 líneas (como hace la consulta principal)
        first_5000 = odoo.models.execute_kw(odoo.db, odoo.uid, odoo.password, 'account.move.line', 'search_read',
            [domain],
            {'fields': ['id', 'move_id'], 'limit': 5000, 'order': 'id desc'})  # El orden por defecto
        
        print(f"📊 Primeras 5000 líneas obtenidas: {len(first_5000)}")
        
        # Verificar si nuestras líneas S00791 están en las primeras 5000
        target_lines = [1394074, 1394076, 1394077, 1394080, 1189865, 1159874, 1159876, 1159877, 1159878, 1159886]
        found_lines = []
        
        for line in first_5000:
            if line['id'] in target_lines:
                found_lines.append(line['id'])
        
        print(f"\n🎯 Líneas S00791 encontradas en las primeras 5000: {len(found_lines)}")
        print(f"   Encontradas: {found_lines}")
        print(f"   Faltantes: {[x for x in target_lines if x not in found_lines]}")
        
        if len(found_lines) < 10:
            print(f"\n⚠️ PROBLEMA CONFIRMADO: Solo {len(found_lines)}/10 líneas S00791 están en las primeras 5000")
            print("💡 SOLUCIÓN: Aumentar el límite o usar consulta específica para S00791")
        else:
            print(f"\n✅ Todas las líneas S00791 están en las primeras 5000")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_limit_issue()