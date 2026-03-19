"""
Script de migración automática: Google Sheets -> Supabase
Ejecuta migración sin confirmación interactiva
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
print("MIGRACIÓN AUTOMÁTICA: Google Sheets → Supabase")
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
    for año, clientes in sorted(metas_sheets.items()):
        print(f"   Año {año}: {len(clientes)} clientes")
    print(f"   TOTAL: {total_registros} registros")
    
except Exception as e:
    print(f"❌ Error leyendo Google Sheets: {e}")
    exit(1)

# 3. Verificar datos existentes
print("\n🔍 Verificando datos existentes en Supabase...")
try:
    metas_existentes = supabase_manager.read_metas_por_cliente()
    total_existentes = sum(len(clientes) for clientes in metas_existentes.values())
    
    if total_existentes > 0:
        print(f"⚠️  Ya hay {total_existentes} registros en Supabase")
        print("   Se hará UPSERT (actualizar existentes + agregar nuevos)")
    else:
        print("✅ Supabase está vacío")
except Exception as e:
    total_existentes = 0

# 4. Ejecutar migración
print(f"\n💾 Migrando {total_registros} registros a Supabase...")
try:
    success = supabase_manager.write_metas_por_cliente(metas_sheets)
    
    if success:
        print("✅ Migración completada exitosamente")
        
        # 5. Verificar
        print("\n🔍 Verificando migración...")
        metas_verificadas = supabase_manager.read_metas_por_cliente()
        
        totales_por_año = {}
        total_final = 0
        for año, clientes in metas_verificadas.items():
            count = len(clientes)
            totales_por_año[año] = count
            total_final += count
        
        print(f"✅ Registros verificados en Supabase:")
        for año in sorted(totales_por_año.keys()):
            print(f"   Año {año}: {totales_por_año[año]} clientes")
        print(f"   TOTAL: {total_final} registros")
        
        if total_final >= total_registros:
            print("\n🎉 ¡Migración 100% exitosa!")
        else:
            print(f"\n⚠️  Advertencia: Se esperaban {total_registros}, se encontraron {total_final}")
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
print(f"✅ Origen: Google Sheets")
print(f"✅ Destino: Supabase (ppmbwujtfueilifisxhs)")
print(f"✅ Registros migrados: {total_registros}")
print(f"✅ Estado: EXITOSO")
print("="*80)
print("\n💡 La aplicación ahora guardará todas las metas en Supabase.")
print("="*80)
