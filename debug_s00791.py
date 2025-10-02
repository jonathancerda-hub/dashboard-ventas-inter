from odoo_manager import OdooManager
import json

# Crear instancia del manager
manager = OdooManager()

# Buscar específicamente S00791
print("🔍 Obteniendo datos de ventas...")
sales_data = manager.get_sales_lines(
    date_from='2025-01-01',
    date_to='2025-12-31'
)

# Buscar líneas que contengan S00791
s00791_lines = [sale for sale in sales_data if 'S00791' in str(sale.get('pedido', '')).upper()]

print(f'📊 Líneas encontradas para S00791: {len(s00791_lines)}')

if s00791_lines:
    print('\n🔍 Estructura de la primera línea S00791:')
    first_line = s00791_lines[0]
    
    # Mostrar campos relevantes para el filtro
    print(f'team_id: {first_line.get("team_id")} (tipo: {type(first_line.get("team_id")).__name__})')
    print(f'pedido: {first_line.get("pedido")}')
    print(f'factura: {first_line.get("factura")}')
    print(f'cliente: {first_line.get("cliente")}')
    print(f'producto: {first_line.get("producto")}')
    print(f'codigo_odoo: {first_line.get("codigo_odoo")}')
    
    # Verificar si tiene INTERNACIONAL en team_id
    team_id = first_line.get('team_id')
    if team_id and isinstance(team_id, list) and len(team_id) > 1:
        nombre_canal = team_id[1]
        print(f'✅ Nombre del canal: {nombre_canal}')
        print(f'✅ ¿Es INTERNACIONAL?: {"INTERNACIONAL" in nombre_canal.upper()}')
    else:
        print(f'❌ team_id no es una lista válida: {team_id}')
    
    # Probar el filtro de búsqueda
    search_term = 's00791'
    producto = first_line.get('producto', '').lower()
    codigo = first_line.get('codigo_odoo', '').lower()
    cliente = first_line.get('cliente', '').lower()
    pedido_lower = first_line.get('pedido', '').lower()
    factura = first_line.get('factura', '').lower()
    
    print(f'\n🔍 Probando filtro de búsqueda con "{search_term}":')
    print(f'  - En pedido "{pedido_lower}": {search_term in pedido_lower}')
    print(f'  - En producto "{producto}": {search_term in producto}')
    print(f'  - En código "{codigo}": {search_term in codigo}')
    print(f'  - En cliente "{cliente}": {search_term in cliente}')
    print(f'  - En factura "{factura}": {search_term in factura}')
    
else:
    print('❌ No se encontraron líneas para S00791 en los datos procesados')
    print(f'📊 Total de líneas en sales_data: {len(sales_data)}')
    
    # Mostrar algunos pedidos para debug
    pedidos_encontrados = set()
    for sale in sales_data[:10]:
        pedidos_encontrados.add(sale.get('pedido', 'Sin pedido'))
    
    print(f'🔍 Primeros 10 pedidos encontrados: {list(pedidos_encontrados)}')