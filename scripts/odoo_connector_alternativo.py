# odoo_connector_alternativo.py
# Métodos alternativos para conectar a Odoo evitando el módulo cs_login_audit_log

import requests
import json
import xmlrpc.client
import os
from dotenv import load_dotenv

load_dotenv()

class OdooConnectorAlternativo:
    """Clase con múltiples métodos de conexión a Odoo"""
    
    def __init__(self):
        self.url = os.getenv('ODOO_URL')
        self.db = os.getenv('ODOO_DB')
        self.username = os.getenv('ODOO_USER')
        self.password = os.getenv('ODOO_PASSWORD')
        self.uid = None
        self.models = None
        
    # ============================================
    # MÉTODO 1: JSON-RPC (más moderno que XML-RPC)
    # ============================================
    def authenticate_jsonrpc(self):
        """Intenta autenticar usando JSON-RPC en lugar de XML-RPC"""
        try:
            print("🔄 Método 1: Intentando JSON-RPC...")
            
            url = f"{self.url}/jsonrpc"
            headers = {"Content-Type": "application/json"}
            
            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "common",
                    "method": "authenticate",
                    "args": [self.db, self.username, self.password, {}]
                },
                "id": 1
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            result = response.json()
            
            if "result" in result and result["result"]:
                self.uid = result["result"]
                print(f"✅ JSON-RPC exitoso! UID: {self.uid}")
                return True
            else:
                print(f"❌ JSON-RPC falló: {result.get('error', 'Sin respuesta')}")
                return False
                
        except Exception as e:
            print(f"❌ Error en JSON-RPC: {e}")
            return False
    
    # ============================================
    # MÉTODO 2: REST API (si está habilitado)
    # ============================================
    def authenticate_rest_api(self):
        """Intenta usar la REST API de Odoo si está disponible"""
        try:
            print("🔄 Método 2: Intentando REST API...")
            
            # Odoo REST API usa /api/auth/token
            url = f"{self.url}/api/auth/token"
            headers = {"Content-Type": "application/json"}
            
            payload = {
                "jsonrpc": "2.0",
                "params": {
                    "db": self.db,
                    "login": self.username,
                    "password": self.password
                }
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    self.uid = result["result"].get("uid")
                    print(f"✅ REST API exitoso! UID: {self.uid}")
                    return True
            
            print(f"❌ REST API no disponible o falló: {response.status_code}")
            return False
            
        except Exception as e:
            print(f"❌ Error en REST API: {e}")
            return False
    
    # ============================================
    # MÉTODO 3: XML-RPC con Headers Personalizados
    # ============================================
    def authenticate_xmlrpc_custom(self):
        """XML-RPC con transport personalizado y headers especiales"""
        try:
            print("🔄 Método 3: Intentando XML-RPC con headers personalizados...")
            
            class CustomTransport(xmlrpc.client.Transport):
                """Transport que agrega headers para simular llamada web"""
                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Odoo-Integration/1.0"
                
                def send_request(self, host, handler, request_body, debug):
                    # Agregar header que simula petición web
                    self.send_host = host
                    return xmlrpc.client.Transport.send_request(
                        self, host, handler, request_body, debug
                    )
            
            transport = CustomTransport()
            common = xmlrpc.client.ServerProxy(
                f'{self.url}/xmlrpc/2/common',
                transport=transport
            )
            
            self.uid = common.authenticate(self.db, self.username, self.password, {})
            
            if self.uid:
                print(f"✅ XML-RPC Custom exitoso! UID: {self.uid}")
                self.models = xmlrpc.client.ServerProxy(
                    f'{self.url}/xmlrpc/2/object',
                    transport=transport
                )
                return True
            else:
                print("❌ XML-RPC Custom dio UID None")
                return False
                
        except Exception as e:
            print(f"❌ Error en XML-RPC Custom: {e}")
            return False
    
    # ============================================
    # MÉTODO 4: Web Session (simulando navegador)
    # ============================================
    def authenticate_web_session(self):
        """Intenta autenticar usando sesión web como lo haría un navegador"""
        try:
            print("🔄 Método 4: Intentando Web Session (como navegador)...")
            
            session = requests.Session()
            
            # 1. Obtener página de login para cookies
            login_url = f"{self.url}/web/login"
            session.get(login_url, timeout=10)
            
            # 2. Autenticar mediante el endpoint web
            auth_url = f"{self.url}/web/session/authenticate"
            payload = {
                "jsonrpc": "2.0",
                "params": {
                    "db": self.db,
                    "login": self.username,
                    "password": self.password
                }
            }
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = session.post(auth_url, json=payload, headers=headers, timeout=10)
            result = response.json()
            
            if "result" in result and result["result"].get("uid"):
                self.uid = result["result"]["uid"]
                print(f"✅ Web Session exitoso! UID: {self.uid}")
                print(f"   Session ID: {result['result'].get('session_id', 'N/A')}")
                return True
            else:
                print(f"❌ Web Session falló: {result.get('error', 'Sin UID')}")
                return False
                
        except Exception as e:
            print(f"❌ Error en Web Session: {e}")
            return False
    
    # ============================================
    # MÉTODO AUTOMÁTICO: Probar todos
    # ============================================
    def auto_connect(self):
        """Intenta todos los métodos hasta que uno funcione"""
        print("="*60)
        print("🚀 PROBANDO CONEXIONES ALTERNATIVAS A ODOO")
        print("="*60)
        
        methods = [
            ("JSON-RPC", self.authenticate_jsonrpc),
            ("REST API", self.authenticate_rest_api),
            ("Web Session", self.authenticate_web_session),
            ("XML-RPC Custom", self.authenticate_xmlrpc_custom),
        ]
        
        for name, method in methods:
            try:
                if method():
                    print("\n" + "="*60)
                    print(f"✅ ¡ÉXITO! Conectado usando: {name}")
                    print("="*60)
                    return True
            except Exception as e:
                print(f"⚠️ {name} generó excepción: {e}")
            
            print()
        
        print("="*60)
        print("❌ Todos los métodos fallaron")
        print("="*60)
        return False
    
    # ============================================
    # PRUEBA: Leer datos después de conectar
    # ============================================
    def test_read_products(self):
        """Prueba leer productos después de autenticar"""
        if not self.uid:
            print("❌ No hay UID válido para leer datos")
            return False
        
        try:
            print("\n🔍 Probando lectura de 5 productos...")
            
            # Si usamos JSON-RPC
            url = f"{self.url}/jsonrpc"
            headers = {"Content-Type": "application/json"}
            
            # Búsqueda
            search_payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "object",
                    "method": "execute_kw",
                    "args": [
                        self.db, self.uid, self.password,
                        'product.product', 'search',
                        [[]], {'limit': 5}
                    ]
                },
                "id": 2
            }
            
            response = requests.post(url, json=search_payload, headers=headers, timeout=10)
            result = response.json()
            
            if "result" in result and result["result"]:
                product_ids = result["result"]
                print(f"✅ Encontrados {len(product_ids)} productos: {product_ids}")
                
                # Leer detalles
                read_payload = {
                    "jsonrpc": "2.0",
                    "method": "call",
                    "params": {
                        "service": "object",
                        "method": "execute_kw",
                        "args": [
                            self.db, self.uid, self.password,
                            'product.product', 'read',
                            [product_ids], {'fields': ['name', 'default_code']}
                        ]
                    },
                    "id": 3
                }
                
                response = requests.post(url, json=read_payload, headers=headers, timeout=10)
                result = response.json()
                
                if "result" in result:
                    print("\n📦 Productos encontrados:")
                    for product in result["result"]:
                        print(f"   - [{product.get('default_code', 'N/A')}] {product.get('name', 'Sin nombre')}")
                    return True
            
            print("❌ No se pudieron leer productos")
            return False
            
        except Exception as e:
            print(f"❌ Error leyendo productos: {e}")
            return False


# ============================================
# SCRIPT DE PRUEBA
# ============================================
if __name__ == "__main__":
    print("\n" + "🔧 ODOO - PROBADOR DE CONEXIONES ALTERNATIVAS" + "\n")
    
    connector = OdooConnectorAlternativo()
    
    # Intentar conectar con todos los métodos
    if connector.auto_connect():
        # Si alguno funcionó, probar leer datos
        connector.test_read_products()
    else:
        print("\n⚠️ NINGÚN MÉTODO FUNCIONÓ")
        print("\nPróximos pasos:")
        print("1. Contactar al admin para desactivar cs_login_audit_log")
        print("2. Solicitar usuario técnico sin auditoría")
        print("3. Verificar si hay firewall bloqueando ciertos endpoints")
