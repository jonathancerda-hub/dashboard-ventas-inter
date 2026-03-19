"""
Script de migración: Google Sheets -> Supabase
Importa todas las metas existentes de Google Sheets a Supabase
"""

import logging
import sys
sys.path.append('..')
from database.google_sheets_manager import GoogleSheetsManager
from database.supabase_manager import SupabaseManager
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

print("="*80)
print("MIGRACIÓN: Google Sheets → Supabase")
print("="*80)

# 1. Inicializar managers
print("\n📊 Conectando a Google Sheets...")
gs_manager = GoogleSheetsManager(
    credentials_file='credentials.json',
    sheet_name=os.getenv('GOOGLE_SHEET_NAME')
)

print("🗄️  Conectando a Supabase...")
supabase_manager = SupabaseManager()

# 2. Leer todas las metas desde Google Sheets
print("\n📖 Leyendo metas desde Google Sheets...")
try:
    metas_sheets = gs_manager.read_metas_por_cliente()
    
    if not metas_sheets:
        print("⚠️  No hay metas en Google Sheets para migrar")
        exit(0)
    
    # Contar registros
    total_registros = 0
    for año, clientes in metas_sheets.items():
        total_registros += len(clientes)
    
    print(f"✅ Encontradas metas en Google Sheets:")
    for año, clientes in metas_sheets.items():
        print(f"   Año {año}: {len(clientes)} clientes")
    print(f"   TOTAL: {total_registros} registros")
    
except Exception as e:
    print(f"❌ Error leyendo Google Sheets: {e}")
    exit(1)

# 3. Verificar si ya hay datos en Supabase
print("\n🔍 Verificando datos existentes en Supabase...")
try:
    metas_existentes = supabase_manager.read_metas_por_cliente()
    total_existentes = sum(len(clientes) for clientes in metas_existentes.values())
    
    if total_existentes > 0:
        print(f"⚠️  Ya hay {total_existentes} registros en Supabase")
        print("   El script hará MERGE (actualizar existentes + agregar nuevos)")
    else:
        print("✅ Supabase está vacío, se insertarán todos los registros")
except Exception as e:
    print(f"⚠️  Error verificando Supabase: {e}")
    total_existentes = 0

# 4. Confirmar migración
print("\n" + "="*80)
respuesta = input(f"¿Migrar {total_registros} registros de Google Sheets a Supabase? (s/n): ")
if respuesta.lower() != 's':
    print("❌ Migración cancelada")
    exit(0)

# 5. Guardar en Supabase
print(f"\n💾 Migrando {total_registros} registros a Supabase...")
try:
    success = supabase_manager.write_metas_por_cliente(metas_sheets)
    
    if success:
        print("✅ Migración completada exitosamente")
        
        # 6. Verificar
        print("\n🔍 Verificando migración...")
        metas_verificadas = supabase_manager.read_metas_por_cliente()
        
        total_verificados = 0
        for año, clientes in metas_verificadas.items():
            total_verificados += len(clientes)
        
        print(f"✅ Registros en Supabase: {total_verificados}")
        
        if total_verificados == total_registros:
            print("✅ ¡Migración 100% exitosa!")
        else:
            print(f"⚠️  Advertencia: Se esperaban {total_registros}, se encontraron {total_verificados}")
    else:
        print("❌ Error en la migración")
        exit(1)
        
except Exception as e:
    print(f"❌ Error migrando a Supabase: {e}")
    logging.exception(e)
    exit(1)

print("\n" + "="*80)
print("RESUMEN DE MIGRACIÓN")
print("="*80)
print(f"Origen: Google Sheets")
print(f"Destino: Supabase (ppmbwujtfueilifisxhs)")
print(f"Registros migrados: {total_registros}")
print(f"Estado: ✅ EXITOSO")
print("="*80)
print("\n💡 IMPORTANTE: La aplicación ahora usará Supabase.")
print("   Las metas nuevas se guardarán automáticamente en Supabase.")
print("="*80)
