# Script para verificar si los clientes existen en Odoo
from odoo_manager import OdooManager
from dotenv import load_dotenv

load_dotenv()

# Clientes reportados como faltantes
clientes_a_buscar = [
    "VETERMEX ANIMAL HEALTH HONDURAS SA",
    "LABORATORIOS QUIMIO-VET, C.A.",
    "AL SALWA GOLD PROJECTS JOINT PARTNERSHIP"
]

print("="*80)
print("VERIFICACIÓN DE CLIENTES FALTANTES EN ODOO")
print("="*80)

manager = OdooManager()

if not manager.uid:
    print("❌ Error: No se pudo conectar a Odoo")
    exit(1)

print(f"✅ Conectado a Odoo (UID: {manager.uid})\n")

for cliente_nombre in clientes_a_buscar:
    print(f"\n🔍 Buscando: {cliente_nombre}")
    print("-" * 80)
    
    try:
        # Buscar el partner en Odoo
        partners = manager.models.execute_kw(
            manager.db, manager.uid, manager.password, 'res.partner', 'search_read',
            [[('name', 'ilike', cliente_nombre)]],
            {'fields': ['id', 'name', 'country_id', 'active'], 'limit': 5}
        )
        
        if not partners:
            print(f"   ❌ No encontrado en res.partner")
            continue
        
        for partner in partners:
            partner_id = partner['id']
            partner_name = partner['name']
            country = partner.get('country_id', [False, ''])[1] if partner.get('country_id') else 'Sin país'
            activo = "✅ Activo" if partner.get('active', True) else "❌ Inactivo"
            
            print(f"   ✅ Encontrado: ID={partner_id}, Nombre='{partner_name}'")
            print(f"      País: {country}, Estado: {activo}")
            
            # Verificar facturas posteadas
            facturas = manager.models.execute_kw(
                manager.db, manager.uid, manager.password, 'account.move.line', 'search_count',
                [[
                    ('partner_id', '=', partner_id),
                    ('move_id.journal_id.name', '=', 'F150 (Venta exterior)'),
                    ('move_id.state', '=', 'posted'),
                    ('account_id.code', 'like', '70%')
                ]]
            )
            print(f"      📄 Facturas posteadas (F150): {facturas}")
            
            # Verificar pedidos de venta
            pedidos = manager.models.execute_kw(
                manager.db, manager.uid, manager.password, 'sale.order', 'search_count',
                [[
                    ('partner_id', '=', partner_id),
                    ('team_id.name', 'ilike', 'INTERNACIONAL')
                ]]
            )
            print(f"      📦 Pedidos de venta internacionales: {pedidos}")
            
            # Verificar líneas de factura con filtros completos
            lineas = manager.models.execute_kw(
                manager.db, manager.uid, manager.password, 'account.move.line', 'search_count',
                [[
                    ('partner_id', '=', partner_id),
                    ('move_id.journal_id.name', '=', 'F150 (Venta exterior)'),
                    ('move_id.state', '=', 'posted'),
                    ('account_id.code', 'like', '70%'),
                    ('product_id', '!=', False),
                    ('product_id.default_code', 'not ilike', '%SERV%'),
                    ('product_id.default_code', 'not like', '81%'),
                ]]
            )
            print(f"      📊 Líneas con filtros completos: {lineas}")
    
    except Exception as e:
        print(f"   ❌ Error buscando cliente: {e}")

print("\n" + "="*80)
print("✅ Verificación completada")
print("="*80)
