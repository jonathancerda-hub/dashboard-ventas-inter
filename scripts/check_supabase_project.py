"""
Script para verificar y mostrar información del proyecto Supabase conectado
"""
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')

print("="*80)
print("PROYECTO SUPABASE CONFIGURADO EN .env")
print("="*80)
print(f"\n📍 URL del proyecto: {url}")
print(f"\n🔑 API Key (primeros 50 chars): {key[:50]}...")

# Extraer referencia del proyecto de la URL
if url:
    proyecto_ref = url.replace('https://', '').replace('.supabase.co', '')
    print(f"\n📦 Referencia del proyecto: {proyecto_ref}")
    print(f"\n🌐 Dashboard del proyecto:")
    print(f"   https://supabase.com/dashboard/project/{proyecto_ref}")
    print(f"\n   SQL Editor directo:")
    print(f"   https://supabase.com/dashboard/project/{proyecto_ref}/editor")

print("\n" + "="*80)
print("INSTRUCCIONES:")
print("="*80)
print("""
1. Abre el SQL Editor en la URL de arriba
2. Verifica que estés en el proyecto correcto (el nombre debe coincidir)
3. Crea una nueva query (+ New query)
4. Pega el contenido de create_metas_table.sql
5. Ejecuta con RUN o Ctrl+Enter
""")
print("="*80)
