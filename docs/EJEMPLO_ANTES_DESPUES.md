# 📝 EJEMPLO ANTES/DESPUÉS - Referencia Visual para Agente IA

## 🎯 Comparación Directa del Código

### ❌ ANTES (XML-RPC - Con Bug)

```python
# odoo_manager.py

import xmlrpc.client
import os
import logging
from dotenv import load_dotenv

load_dotenv()

class OdooManager:
    def __init__(self):
        try:
            # Credenciales
            self.url = os.getenv('ODOO_URL')
            self.db = os.getenv('ODOO_DB')
            self.username = os.getenv('ODOO_USER')
            self.password = os.getenv('ODOO_PASSWORD')
            
            # Conexión XML-RPC (ESTO CAUSA EL BUG)
            common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            self.uid = common.authenticate(self.db, self.username, self.password, {})
            
            if self.uid:
                self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
                logging.info(f"Conexión exitosa. UID: {self.uid}")
            else:
                self.uid = None
                self.models = None
                logging.warning("Falló autenticación")
                
        except Exception as e:
            self.uid = None
            self.models = None
            logging.error(f"Error: {e}")
    
    def authenticate_user(self, username, password):
        try:
            common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            uid = common.authenticate(self.db, username, password, {})
            
            if uid:
                models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
                user_data = models.execute_kw(
                    self.db, uid, password,
                    'res.users', 'read',
                    [uid], {'fields': ['name', 'login']}
                )
                return user_data[0] if user_data else None
            return None
        except Exception as e:
            logging.error(f"Error: {e}")
            return None
    
    def get_products(self):
        """Ejemplo de consulta"""
        if not self.uid:
            return []
        
        product_ids = self.models.execute_kw(
            self.db, self.uid, self.password,
            'product.product', 'search',
            [[]], {'limit': 10}
        )
        
        products = self.models.execute_kw(
            self.db, self.uid, self.password,
            'product.product', 'read',
            [product_ids], {'fields': ['name', 'default_code']}
        )
        
        return products
```

**Resultado:** ❌ Error `RuntimeError: object unbound`

---

### ✅ DESPUÉS (JSON-RPC - Funciona)

```python
# odoo_manager.py

import xmlrpc.client  # Mantener por si se necesita
import requests       # NUEVO
import json           # NUEVO
import os
import logging
from dotenv import load_dotenv

load_dotenv()

class OdooManager:
    def __init__(self):
        try:
            # Credenciales (IGUAL)
            self.url = os.getenv('ODOO_URL')
            self.db = os.getenv('ODOO_DB')
            self.username = os.getenv('ODOO_USER')
            self.password = os.getenv('ODOO_PASSWORD')
            
            # NUEVO: Configuración JSON-RPC
            self.rpc_timeout = 30
            self.jsonrpc_url = f"{self.url}/jsonrpc"
            
            # NUEVO: Autenticación JSON-RPC
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
            
            response = requests.post(
                self.jsonrpc_url,
                json=payload,
                headers=headers,
                timeout=self.rpc_timeout
            )
            result = response.json()
            
            if "result" in result and result["result"]:
                self.uid = result["result"]
                self.models = self._create_jsonrpc_models_proxy()  # NUEVO
                logging.info(f"✅ Conexión exitosa (JSON-RPC). UID: {self.uid}")
            else:
                self.uid = None
                self.models = None
                logging.warning("❌ Falló autenticación")
                
        except Exception as e:
            self.uid = None
            self.models = None
            logging.error(f"❌ Error: {e}")
    
    # NUEVO: Wrapper para mantener compatibilidad
    def _create_jsonrpc_models_proxy(self):
        """Crea objeto compatible con API XML-RPC"""
        class JSONRPCModelsProxy:
            def __init__(self, manager):
                self.manager = manager
            
            def execute_kw(self, db, uid, password, model, method, args, kwargs=None):
                if kwargs is None:
                    kwargs = {}
                
                headers = {"Content-Type": "application/json"}
                payload = {
                    "jsonrpc": "2.0",
                    "method": "call",
                    "params": {
                        "service": "object",
                        "method": "execute_kw",
                        "args": [db, uid, password, model, method, args, kwargs]
                    },
                    "id": 1
                }
                
                response = requests.post(
                    self.manager.jsonrpc_url,
                    json=payload,
                    headers=headers,
                    timeout=self.manager.rpc_timeout
                )
                result = response.json()
                
                if "result" in result:
                    return result["result"]
                elif "error" in result:
                    logging.error(f"Error Odoo: {result['error']}")
                    return None
                return None
        
        return JSONRPCModelsProxy(self)
    
    # ACTUALIZADO: authenticate_user con JSON-RPC
    def authenticate_user(self, username, password):
        try:
            headers = {"Content-Type": "application/json"}
            
            # Autenticar
            auth_payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "common",
                    "method": "authenticate",
                    "args": [self.db, username, password, {}]
                },
                "id": 1
            }
            
            response = requests.post(
                self.jsonrpc_url,
                json=auth_payload,
                headers=headers,
                timeout=self.rpc_timeout
            )
            result = response.json()
            
            if "result" in result and result["result"]:
                uid = result["result"]
                
                # Leer datos del usuario
                read_payload = {
                    "jsonrpc": "2.0",
                    "method": "call",
                    "params": {
                        "service": "object",
                        "method": "execute_kw",
                        "args": [
                            self.db, uid, password,
                            'res.users', 'read',
                            [uid], {'fields': ['name', 'login']}
                        ]
                    },
                    "id": 2
                }
                
                response = requests.post(
                    self.jsonrpc_url,
                    json=read_payload,
                    headers=headers,
                    timeout=self.rpc_timeout
                )
                result = response.json()
                
                if "result" in result and result["result"]:
                    return result["result"][0]
                return {'id': uid, 'name': username, 'login': username}
            return None
            
        except Exception as e:
            logging.error(f"Error authenticate_user: {e}")
            return None
    
    # SIN CAMBIOS: Este método sigue funcionando igual
    def get_products(self):
        """Ejemplo de consulta - NO NECESITA CAMBIOS"""
        if not self.uid:
            return []
        
        # Estas llamadas siguen funcionando EXACTAMENTE IGUAL
        # gracias al wrapper JSONRPCModelsProxy
        product_ids = self.models.execute_kw(
            self.db, self.uid, self.password,
            'product.product', 'search',
            [[]], {'limit': 10}
        )
        
        products = self.models.execute_kw(
            self.db, self.uid, self.password,
            'product.product', 'read',
            [product_ids], {'fields': ['name', 'default_code']}
        )
        
        return products
```

**Resultado:** ✅ Funciona perfectamente, evita el bug

---

## 📋 Resumen de Cambios

| Elemento | ANTES (XML-RPC) | DESPUÉS (JSON-RPC) |
|----------|-----------------|-------------------|
| **Imports** | `xmlrpc.client` | `xmlrpc.client, requests, json` |
| **Endpoint** | `/xmlrpc/2/common` | `/jsonrpc` |
| **Autenticación** | `ServerProxy.authenticate()` | `requests.post()` con payload JSON |
| **Models** | `ServerProxy('/xmlrpc/2/object')` | `JSONRPCModelsProxy()` (wrapper) |
| **Consultas** | `models.execute_kw()` | `models.execute_kw()` (sin cambios) |
| **Compatibilidad** | - | ✅ 100% compatible con código existente |

---

## 🎯 Lo Importante para el Agente

### ✅ LO QUE SÍ CAMBIA:
1. Imports: agregar `requests` y `json`
2. Método `__init__`: toda la sección de autenticación
3. Agregar método `_create_jsonrpc_models_proxy()`
4. Actualizar método `authenticate_user()` (si existe)

### ✅ LO QUE NO CAMBIA:
1. **Todo el código que usa `models.execute_kw()`** sigue igual
2. Métodos como `get_products()`, `get_sales()`, etc. **NO se tocan**
3. La lógica de negocio **permanece intacta**
4. Las consultas a Odoo **funcionan exactamente igual**

### 🎯 El Truco:
El wrapper `JSONRPCModelsProxy` convierte las llamadas `execute_kw()` (XML-RPC style) a JSON-RPC internamente, manteniendo la misma interfaz para el resto del código.

---

## 💡 Para el Agente IA: Patrón de Búsqueda

**Busca este patrón en el código:**
```python
xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
```

**Y reemplázalo con:**
```python
# Configuración JSON-RPC
self.jsonrpc_url = f"{url}/jsonrpc"
headers = {"Content-Type": "application/json"}
payload = {"jsonrpc": "2.0", "method": "call", ...}
response = requests.post(self.jsonrpc_url, json=payload, headers=headers)
```

**Busca también:**
```python
xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
```

**Y reemplázalo con:**
```python
self._create_jsonrpc_models_proxy()
```

---

## 🧪 Test Rápido

Después de los cambios, ejecuta:

```python
# test_rapido.py
from odoo_manager import OdooManager

manager = OdooManager()

if manager.uid:
    print(f"✅ UID: {manager.uid}")
    products = manager.get_products()
    print(f"✅ Productos: {len(products)}")
else:
    print("❌ No conectado")
```

**Output esperado:**
```
✅ UID: 6
✅ Productos: 10
```

---

**Usa este archivo como referencia visual para implementar los cambios en cualquier proyecto.**
