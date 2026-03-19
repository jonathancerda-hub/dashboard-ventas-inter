#!/usr/bin/env python
"""
test_odoo_jsonrpc.py

Script independiente para probar conexión JSON-RPC a Odoo
Úsalo ANTES de migrar para verificar que JSON-RPC funciona

USO:
----
1. Configura tus variables de entorno en .env:
   ODOO_URL=https://tu-empresa.odoo.com
   ODOO_DB=nombre-bd
   ODOO_USER=usuario@empresa.com
   ODOO_PASSWORD=tu_password_o_api_key

2. Ejecuta:
   python test_odoo_jsonrpc.py

3. Si ves "✅ TODAS LAS PRUEBAS EXITOSAS", JSON-RPC funciona
   y puedes proceder con la migración.

AUTOR: Jonathan Cerda
FECHA: Marzo 2026
"""

import requests
import os
import sys
import json
from dotenv import load_dotenv

# Colores para terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def print_header(msg):
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{msg}{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")

def test_odoo_jsonrpc():
    """Probar conexión completa con JSON-RPC"""
    
    print_header("🧪 TEST DE CONEXIÓN ODOO JSON-RPC")
    
    # 1. Cargar credenciales
    print_info("1. Cargando credenciales desde .env...")
    load_dotenv()
    
    url = os.getenv('ODOO_URL')
    db = os.getenv('ODOO_DB')
    username = os.getenv('ODOO_USER')
    password = os.getenv('ODOO_PASSWORD')
    
    # Validar credenciales
    missing = []
    if not url:
        missing.append('ODOO_URL')
    if not db:
        missing.append('ODOO_DB')
    if not username:
        missing.append('ODOO_USER')
    if not password:
        missing.append('ODOO_PASSWORD')
    
    if missing:
        print_error(f"Faltan variables de entorno: {', '.join(missing)}")
        print_info("Crea un archivo .env con:")
        print("   ODOO_URL=https://tu-empresa.odoo.com")
        print("   ODOO_DB=nombre-bd")
        print("   ODOO_USER=usuario@empresa.com")
        print("   ODOO_PASSWORD=tu_password_o_api_key")
        return False
    
    print(f"   URL: {url}")
    print(f"   DB: {db}")
    print(f"   Usuario: {username}")
    print_success("Credenciales cargadas\n")
    
    # 2. Construir URL JSON-RPC
    jsonrpc_url = f"{url.rstrip('/')}/jsonrpc"
    headers = {"Content-Type": "application/json"}
    timeout = 30
    
    # 3. Test: Obtener versión del servidor (sin autenticación)
    print_info("2. Probando endpoint JSON-RPC (sin autenticación)...")
    try:
        version_payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "common",
                "method": "version",
                "args": []
            },
            "id": 1
        }
        
        response = requests.post(jsonrpc_url, json=version_payload, headers=headers, timeout=timeout)
        response.raise_for_status()
        result = response.json()
        
        if "result" in result:
            version_info = result["result"]
            print_success(f"Endpoint JSON-RPC activo")
            print(f"   Odoo Version: {version_info.get('server_version', 'N/A')}")
            print(f"   Serie: {version_info.get('server_serie', 'N/A')}")
            print(f"   Protocol: {version_info.get('protocol_version', 'N/A')}\n")
        else:
            print_error(f"Respuesta inesperada: {result}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error(f"No se puede conectar a {url}")
        print_info("Verifica:")
        print("   - La URL es correcta")
        print("   - Tienes conexión a internet")
        print("   - No hay firewall bloqueando")
        return False
    except requests.exceptions.Timeout:
        print_error(f"Timeout después de {timeout}s")
        return False
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        return False
    
    # 4. Test: Autenticación
    print_info("3. Probando autenticación...")
    try:
        auth_payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "common",
                "method": "authenticate",
                "args": [db, username, password, {}]
            },
            "id": 2
        }
        
        response = requests.post(jsonrpc_url, json=auth_payload, headers=headers, timeout=timeout)
        response.raise_for_status()
        result = response.json()
        
        if "result" in result and result["result"]:
            uid = result["result"]
            print_success(f"Autenticación exitosa")
            print(f"   UID: {uid}\n")
        elif "error" in result:
            error = result["error"]
            error_msg = error.get("data", {}).get("message", str(error))
            print_error(f"Autenticación falló: {error_msg}")
            print_info("Verifica:")
            print("   - Usuario y contraseña son correctos")
            print("   - Si usas API Key, que no haya expirado")
            print("   - El usuario tiene permisos de acceso")
            return False
        else:
            print_error("Autenticación falló: credenciales incorrectas")
            return False
            
    except Exception as e:
        print_error(f"Error en autenticación: {e}")
        return False
    
    # 5. Test: Búsqueda simple
    print_info("4. Probando consulta de datos (res.partner)...")
    try:
        search_payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": [
                    db, uid, password,
                    'res.partner', 'search',
                    [[]], {'limit': 5}
                ]
            },
            "id": 3
        }
        
        response = requests.post(jsonrpc_url, json=search_payload, headers=headers, timeout=timeout)
        result = response.json()
        
        if "result" in result:
            partner_ids = result["result"]
            print_success(f"Búsqueda exitosa")
            print(f"   Encontrados {len(partner_ids)} partners (IDs: {partner_ids})\n")
        else:
            print_error(f"Error en búsqueda: {result}")
            return False
            
    except Exception as e:
        print_error(f"Error en consulta: {e}")
        return False
    
    # 6. Test: Lectura de datos
    print_info("5. Probando lectura de datos (res.partner)...")
    try:
        read_payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": [
                    db, uid, password,
                    'res.partner', 'read',
                    [partner_ids[:3]], {'fields': ['name', 'email']}
                ]
            },
            "id": 4
        }
        
        response = requests.post(jsonrpc_url, json=read_payload, headers=headers, timeout=timeout)
        result = response.json()
        
        if "result" in result:
            partners = result["result"]
            print_success(f"Lectura exitosa")
            print(f"   Datos leídos:")
            for p in partners:
                print(f"     - {p.get('name', 'N/A')} ({p.get('email', 'Sin email')})")
            print()
        else:
            print_error(f"Error en lectura: {result}")
            return False
            
    except Exception as e:
        print_error(f"Error en lectura: {e}")
        return False
    
    # 7. Test: search_read (más eficiente)
    print_info("6. Probando search_read (product.product)...")
    try:
        search_read_payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": "object",
                "method": "execute_kw",
                "args": [
                    db, uid, password,
                    'product.product', 'search_read',
                    [[]], {'fields': ['name', 'default_code'], 'limit': 3}
                ]
            },
            "id": 5
        }
        
        response = requests.post(jsonrpc_url, json=search_read_payload, headers=headers, timeout=timeout)
        result = response.json()
        
        if "result" in result:
            products = result["result"]
            print_success(f"Search_read exitoso")
            print(f"   Productos encontrados:")
            for p in products:
                code = p.get('default_code', 'N/A')
                name = p.get('name', 'Sin nombre')
                print(f"     [{code}] {name}")
            print()
        else:
            print_warning("No se pudieron leer productos (puede que no haya permisos)")
            
    except Exception as e:
        print_warning(f"Advertencia en lectura de productos: {e}")
    
    # 8. Comparación con XML-RPC
    print_info("7. Comparando con XML-RPC (opcional)...")
    try:
        import xmlrpc.client
        
        xmlrpc_common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        xmlrpc_uid = xmlrpc_common.authenticate(db, username, password, {})
        
        if xmlrpc_uid:
            print_warning("XML-RPC también funciona")
            print_info("   Sin embargo, JSON-RPC es preferible porque:")
            print("     - Evita bugs de módulos de auditoría")
            print("     - Es más rápido (JSON vs XML)")
            print("     - Los payloads son más pequeños")
            print("     - Más fácil de debuggear")
        else:
            print_success("XML-RPC está bloqueado (razón para usar JSON-RPC)")
            
    except Exception as e:
        print_success("XML-RPC está bloqueado")
        print_info(f"   Error XML-RPC: {str(e)[:100]}...")
        print_info("   ✅ JSON-RPC es la solución correcta")
    
    print()
    
    # RESUMEN FINAL
    print_header("✅ TODAS LAS PRUEBAS EXITOSAS")
    
    print(f"{Colors.GREEN}{Colors.BOLD}JSON-RPC está funcionando correctamente!{Colors.END}\n")
    
    print("📋 Próximos pasos:")
    print("   1. Copia 'odoo_jsonrpc_client.py' a tu proyecto")
    print("   2. Reemplaza las llamadas XML-RPC por JSON-RPC")
    print("   3. Lee la guía: docs/QUICK_START_MIGRACION.md")
    print()
    
    print("💡 Ejemplo de uso rápido:")
    print("   " + Colors.BLUE + "from odoo_jsonrpc_client import OdooJSONRPCClient" + Colors.END)
    print("   " + Colors.BLUE + "client = OdooJSONRPCClient(url, db, username, password)" + Colors.END)
    print("   " + Colors.BLUE + "partners = client.search_read('res.partner', [], limit=10)" + Colors.END)
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = test_odoo_jsonrpc()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Prueba interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
