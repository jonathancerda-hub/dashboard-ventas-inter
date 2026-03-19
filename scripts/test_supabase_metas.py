"""
Test completo de escritura y lectura de metas en Supabase
"""
from supabase_manager import SupabaseManager
import logging

logging.basicConfig(level=logging.INFO)

print("="*80)
print("TEST: Guardar y leer metas en Supabase")
print("="*80)

manager = SupabaseManager()

# 1. Crear datos de prueba
print("\n📝 Creando datos de prueba...")
metas_test = {
    "2026": {
        "48808": {
            "cliente_nombre": "VETERMEX ANIMAL HEALTH HONDURAS SA",
            "agrovet": 100000.0,
            "petmedica": 50000.0,
            "avivet": 30000.0
        },
        "37979": {
            "cliente_nombre": "LABORATORIOS QUIMIO-VET, C.A.",
            "agrovet": 80000.0,
            "petmedica": 40000.0,
            "avivet": 20000.0
        },
        "52512": {
            "cliente_nombre": "AL SALWA GOLD PROJECTS JOINT PARTNERSHIP",
            "agrovet": 60000.0,
            "petmedica": 30000.0,
            "avivet": 10000.0
        }
    }
}

# 2. Guardar en Supabase
print("\n💾 Guardando metas en Supabase...")
success = manager.write_metas_por_cliente(metas_test)

if success:
    print("✅ Metas guardadas exitosamente")
else:
    print("❌ Error guardando metas")
    exit(1)

# 3. Leer desde Supabase
print("\n📖 Leyendo metas desde Supabase...")
metas_leidas = manager.read_metas_por_cliente()

# 4. Verificar
print(f"\n🔍 Verificación:")
print(f"   Años en respuesta: {list(metas_leidas.keys())}")

if "2026" in metas_leidas:
    clientes = list(metas_leidas["2026"].keys())
    print(f"   Clientes en 2026: {len(clientes)}")
    
    for cliente_id, metas in metas_leidas["2026"].items():
        nombre = metas.get('cliente_nombre', 'Sin nombre')
        total = metas.get('agrovet', 0) + metas.get('petmedica', 0) + metas.get('avivet', 0)
        print(f"\n   ✅ Cliente ID {cliente_id}:")
        print(f"      Nombre: {nombre}")
        print(f"      AGROVET: ${metas.get('agrovet', 0):,.0f}")
        print(f"      PETMEDICA: ${metas.get('petmedica', 0):,.0f}")
        print(f"      AVIVET: ${metas.get('avivet', 0):,.0f}")
        print(f"      TOTAL: ${total:,.0f}")
else:
    print("   ❌ No se encontraron metas para 2026")

print("\n" + "="*80)
print("✅ TEST COMPLETADO")
print("="*80)
