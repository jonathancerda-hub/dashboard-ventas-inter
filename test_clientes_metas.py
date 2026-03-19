# Script para probar que los 3 clientes ahora aparecen
from odoo_manager import OdooManager
from dotenv import load_dotenv

load_dotenv()

print("="*80)
print("PRUEBA: Verificar que los clientes ahora aparecen en get_international_clients()")
print("="*80)

manager = OdooManager()

if not manager.uid:
    print("❌ Error: No se pudo conectar a Odoo")
    exit(1)

print(f"✅ Conectado a Odoo (UID: {manager.uid})\n")

# Obtener lista de clientes internacionales
print("🔍 Obteniendo lista de clientes internacionales...")
clientes = manager.get_international_clients()

print(f"✅ Total de clientes encontrados: {len(clientes)}\n")

# Buscar los 3 clientes específicos
clientes_a_verificar = [
    "VETERMEX ANIMAL HEALTH HONDURAS SA",
    "LABORATORIOS QUIMIO-VET, C.A.",
    "AL SALWA GOLD PROJECTS JOINT PARTNERSHIP"
]

print("Verificando clientes específicos:")
print("-" * 80)

for nombre_buscar in clientes_a_verificar:
    encontrado = False
    for cliente_id, cliente_nombre in clientes:
        if nombre_buscar.upper() in cliente_nombre.upper():
            print(f"✅ Encontrado: ID={cliente_id}, Nombre='{cliente_nombre}'")
            encontrado = True
            break
    
    if not encontrado:
        print(f"❌ NO encontrado: '{nombre_buscar}'")

print("\n" + "="*80)
print("Primeros 10 clientes de la lista:")
print("-" * 80)
for i, (cliente_id, cliente_nombre) in enumerate(clientes[:10], 1):
    print(f"{i}. ID={cliente_id}, Nombre='{cliente_nombre}'")

print("\n" + "="*80)
print("✅ Prueba completada")
print("="*80)
