# Solución: Migrar Odoo de XML-RPC a JSON-RPC

## 📋 Resumen Ejecutivo

Si tu aplicación Python que se conecta a Odoo está fallando con el error:

```
RuntimeError: object unbound
File "cs_login_audit_log/models/res_users.py", line 23, in _check_credentials
    ip_address = request.httprequest.environ.get('REMOTE_ADDR')
```

**La solución es cambiar de XML-RPC a JSON-RPC**. Este cambio evita el módulo de auditoría problemático y además ofrece mejor rendimiento.

---

## 🔍 ¿Por qué ocurre el problema?

El módulo de terceros `cs_login_audit_log` tiene un bug que asume que todas las autenticaciones provienen de peticiones HTTP web. Cuando intentas conectarte via XML-RPC (`/xmlrpc/2/common`), el módulo intenta acceder a `request.httprequest` que no existe en ese contexto, causando el crash.

**JSON-RPC** (`/jsonrpc`) usa un endpoint diferente que **NO** es interceptado por este módulo defectuoso.

---

## ✅ Ventajas de JSON-RPC vs XML-RPC

| Característica | XML-RPC | JSON-RPC |
|---------------|---------|----------|
| **Payload Size** | ~30% más grande | Más compacto |
| **Parsing** | XML (lento) | JSON (nativo) |
| **Debugging** | Difícil de leer | Fácil de leer |
| **Compatibilidad** | Odoo 8+ | Odoo 9+ |
| **Performance** | Regular | Mejor |
| **Bug cs_login_audit_log** | ❌ Afectado | ✅ No afectado |

---

## 🚀 Implementación: Paso a Paso

### Paso 1: Actualizar Imports

**Antes (solo XML-RPC):**
```python
import xmlrpc.client
```

**Después (JSON-RPC):**
```python
import xmlrpc.client  # Mantener por compatibilidad
import requests
import json
```

### Paso 2: Modificar la Clase de Conexión

#### Opción A: Clase Completa con JSON-RPC

Reemplaza tu constructor de conexión con este código:

```python
import os
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

class OdooManager:
    def __init__(self):
        """Inicializar conexión con Odoo usando JSON-RPC"""
        try:
            # Cargar credenciales
            self.url = os.getenv('ODOO_URL')
            self.db = os.getenv('ODOO_DB')
            self.username = os.getenv('ODOO_USER')
            self.password = os.getenv('ODOO_PASSWORD')
            
            # Validar credenciales
            if not all([self.url, self.db, self.username, self.password]):
                raise ValueError("Faltan variables de entorno de Odoo")
            
            # Timeout configurable
            self.rpc_timeout = int(os.getenv('ODOO_RPC_TIMEOUT', '30'))
            
            # URL para JSON-RPC
            self.jsonrpc_url = f"{self.url}/jsonrpc"
            
            # === AUTENTICACIÓN VIA JSON-RPC ===
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
                self.models = self._create_jsonrpc_models_proxy()
                logging.info(f"✅ Conexión Odoo exitosa (JSON-RPC). UID: {self.uid}")
            else:
                self.uid = None
                self.models = None
                error = result.get('error', 'Sin respuesta')
                logging.warning(f"❌ Autenticación falló: {error}")
                
        except requests.exceptions.Timeout:
            self.uid = None
            self.models = None
            logging.warning("⏱️ Timeout en autenticación")
        except Exception as e:
            self.uid = None
            self.models = None
            logging.error(f"❌ Error en conexión: {e}")
    
    def _create_jsonrpc_models_proxy(self):
        """Crea un objeto proxy compatible con la API de xmlrpc.client"""
        class JSONRPCModelsProxy:
            def __init__(self, manager):
                self.manager = manager
            
            def execute_kw(self, db, uid, password, model, method, args, kwargs=None):
                """Wrapper que ejecuta llamadas via JSON-RPC"""
                if kwargs is None:
                    kwargs = {}
                
                try:
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
                        error = result["error"]
                        error_msg = error.get("data", {}).get("message", str(error))
                        logging.error(f"Error Odoo: {error_msg}")
                        return None
                    else:
                        return None
                        
                except Exception as e:
                    logging.error(f"Error en execute_kw: {e}")
                    return None
        
        return JSONRPCModelsProxy(self)
```

#### Opción B: Función de Conveniencia Reutilizable

Si prefieres algo más modular, crea un archivo `odoo_jsonrpc_client.py`:

```python
"""
odoo_jsonrpc_client.py
Cliente JSON-RPC para Odoo (evita bugs de módulos XML-RPC)
"""

import requests
import logging

class OdooJSONRPCClient:
    """Cliente JSON-RPC para Odoo compatible con la API de xmlrpc.client"""
    
    def __init__(self, url, db, username, password, timeout=30):
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.timeout = timeout
        self.jsonrpc_url = f"{url}/jsonrpc"
        self.uid = None
        
        # Autenticar automáticamente
        self.authenticate()
    
    def authenticate(self):
        """Autenticar y obtener UID"""
        try:
            result = self._call_json_rpc(
                service="common",
                method="authenticate",
                args=[self.db, self.username, self.password, {}]
            )
            self.uid = result
            return self.uid
        except Exception as e:
            logging.error(f"Authentication failed: {e}")
            return None
    
    def _call_json_rpc(self, service, method, args):
        """Llamada genérica JSON-RPC"""
        headers = {"Content-Type": "application/json"}
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "service": service,
                "method": method,
                "args": args
            },
            "id": 1
        }
        
        response = requests.post(
            self.jsonrpc_url,
            json=payload,
            headers=headers,
            timeout=self.timeout
        )
        result = response.json()
        
        if "result" in result:
            return result["result"]
        elif "error" in result:
            raise Exception(f"Odoo error: {result['error']}")
        else:
            raise Exception("Invalid response from Odoo")
    
    def execute_kw(self, model, method, args, kwargs=None):
        """Ejecutar método de modelo Odoo"""
        if kwargs is None:
            kwargs = {}
        
        if not self.uid:
            raise Exception("Not authenticated")
        
        return self._call_json_rpc(
            service="object",
            method="execute_kw",
            args=[self.db, self.uid, self.password, model, method, args, kwargs]
        )
    
    def search(self, model, domain, limit=None, offset=None, order=None):
        """Buscar registros"""
        kwargs = {}
        if limit:
            kwargs['limit'] = limit
        if offset:
            kwargs['offset'] = offset
        if order:
            kwargs['order'] = order
        
        return self.execute_kw(model, 'search', [domain], kwargs)
    
    def read(self, model, ids, fields=None):
        """Leer registros"""
        kwargs = {}
        if fields:
            kwargs['fields'] = fields
        
        return self.execute_kw(model, 'read', [ids], kwargs)
    
    def search_read(self, model, domain, fields=None, limit=None, offset=None, order=None):
        """Buscar y leer en una sola llamada"""
        kwargs = {}
        if fields:
            kwargs['fields'] = fields
        if limit:
            kwargs['limit'] = limit
        if offset:
            kwargs['offset'] = offset
        if order:
            kwargs['order'] = order
        
        return self.execute_kw(model, 'search_read', [domain], kwargs)
```

**Uso:**

```python
from odoo_jsonrpc_client import OdooJSONRPCClient
import os

# Conectar
client = OdooJSONRPCClient(
    url=os.getenv('ODOO_URL'),
    db=os.getenv('ODOO_DB'),
    username=os.getenv('ODOO_USER'),
    password=os.getenv('ODOO_PASSWORD')
)

# Usar
products = client.search_read(
    'product.product',
    domain=[],
    fields=['name', 'default_code'],
    limit=10
)

for product in products:
    print(f"{product['default_code']} - {product['name']}")
```

---

### Paso 3: Actualizar requirements.txt

```txt
# Antes (solo tenías):
# (nada relacionado a requests si solo usabas xmlrpc)

# Ahora agrega:
requests>=2.31.0
```

Instalar:
```bash
pip install requests
```

---

## 🧪 Script de Prueba

Crea `test_odoo_connection.py` para validar la migración:

```python
#!/usr/bin/env python
"""Test de conexión Odoo con JSON-RPC"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_jsonrpc_connection():
    """Probar conexión JSON-RPC a Odoo"""
    
    # Credenciales
    url = os.getenv('ODOO_URL')
    db = os.getenv('ODOO_DB')
    username = os.getenv('ODOO_USER')
    password = os.getenv('ODOO_PASSWORD')
    
    print(f"Conectando a: {url}")
    print(f"Base de datos: {db}")
    print(f"Usuario: {username}")
    print()
    
    # Autenticar
    jsonrpc_url = f"{url}/jsonrpc"
    headers = {"Content-Type": "application/json"}
    
    auth_payload = {
        "jsonrpc": "2.0",
        "method": "call",
        "params": {
            "service": "common",
            "method": "authenticate",
            "args": [db, username, password, {}]
        },
        "id": 1
    }
    
    try:
        response = requests.post(jsonrpc_url, json=auth_payload, headers=headers, timeout=10)
        result = response.json()
        
        if "result" in result and result["result"]:
            uid = result["result"]
            print(f"✅ Autenticación exitosa!")
            print(f"   UID: {uid}")
            
            # Probar consulta
            search_payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "object",
                    "method": "execute_kw",
                    "args": [
                        db, uid, password,
                        'res.partner', 'search_read',
                        [[]], {'fields': ['name'], 'limit': 3}
                    ]
                },
                "id": 2
            }
            
            response = requests.post(jsonrpc_url, json=search_payload, headers=headers, timeout=10)
            result = response.json()
            
            if "result" in result:
                partners = result["result"]
                print(f"\n✅ Consulta exitosa!")
                print(f"   Encontrados {len(partners)} partners:")
                for p in partners:
                    print(f"   - {p['name']}")
                
                print("\n" + "="*50)
                print("🎉 MIGRACIÓN EXITOSA A JSON-RPC")
                print("="*50)
                return True
            else:
                print(f"❌ Error en consulta: {result}")
                return False
        else:
            print(f"❌ Autenticación falló: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_jsonrpc_connection()
```

Ejecutar:
```bash
python test_odoo_connection.py
```

---

## 📊 Comparación de Código

### Antes (XML-RPC)

```python
import xmlrpc.client

# Conexión
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

# Consulta
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
partners = models.execute_kw(
    db, uid, password,
    'res.partner', 'search_read',
    [[]], {'limit': 10}
)
```

### Después (JSON-RPC)

```python
import requests

# Conexión
jsonrpc_url = f"{url}/jsonrpc"
headers = {"Content-Type": "application/json"}

auth = {
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "service": "common",
        "method": "authenticate",
        "args": [db, username, password, {}]
    },
    "id": 1
}
response = requests.post(jsonrpc_url, json=auth, headers=headers)
uid = response.json()["result"]

# Consulta
query = {
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "service": "object",
        "method": "execute_kw",
        "args": [db, uid, password, 'res.partner', 'search_read', [[]], {'limit': 10}]
    },
    "id": 2
}
response = requests.post(jsonrpc_url, json=query, headers=headers)
partners = response.json()["result"]
```

---

## 🎯 Checklist de Migración

- [ ] Instalar `requests`: `pip install requests`
- [ ] Agregar imports: `import requests`, `import json`
- [ ] Reemplazar `xmlrpc.client.ServerProxy` con llamadas HTTP POST
- [ ] Cambiar endpoint: `/xmlrpc/2/common` → `/jsonrpc`
- [ ] Actualizar payload al formato JSON-RPC 2.0
- [ ] Crear wrapper `JSONRPCModelsProxy` para compatibilidad
- [ ] Actualizar método `authenticate_user` si existe
- [ ] Probar con `test_odoo_connection.py`
- [ ] Verificar todas las consultas existentes
- [ ] Actualizar documentación del proyecto
- [ ] Commit y deploy

---

## 🐛 Troubleshooting

### Error: "Connection refused"
```python
# Verificar que la URL no tenga espacios o caracteres extra
url = os.getenv('ODOO_URL').strip()
```

### Error: "Invalid credentials"
```python
# Usar API Key en lugar de contraseña (Odoo 14+)
# Generar en: Preferencias → Seguridad de la cuenta → API Keys
```

### Error: "Timeout"
```python
# Aumentar timeout
response = requests.post(url, json=payload, timeout=60)
```

### JSON no se parsea correctamente
```python
# Verificar Content-Type
headers = {"Content-Type": "application/json"}
```

---

## 📚 Recursos Adicionales

- [Documentación oficial Odoo External API](https://www.odoo.com/documentation/16.0/developer/reference/external_api.html)
- [JSON-RPC Specification 2.0](https://www.jsonrpc.org/specification)
- [Requests Library Docs](https://docs.python-requests.org/)

---

## 🔒 Seguridad

**Recomendaciones:**

1. **Usar API Keys** en lugar de contraseñas (Odoo 14+)
2. **HTTPS siempre** en producción
3. **Timeout apropiado** para evitar bloqueos
4. **Validar respuestas** antes de usarlas
5. **Logging seguro** (no registrar contraseñas)

```python
# Ejemplo de logging seguro
logging.info(f"Conectando a {url} con usuario {username[:3]}***")
```

---

## 📝 Notas Finales

Esta solución:
- ✅ Evita el bug del módulo `cs_login_audit_log`
- ✅ No requiere cambios en el servidor Odoo
- ✅ Es compatible con código XML-RPC existente (via wrapper)
- ✅ Mejora el rendimiento
- ✅ Facilita el debugging

**Tiempo estimado de migración:** 30-60 minutos para un proyecto típico.

---

## 📞 Contacto

Si tienes problemas con la migración, verifica:
1. Que tu versión de Odoo sea 9+ (JSON-RPC no existe en Odoo 8)
2. Que `requests` esté instalado correctamente
3. Que las credenciales sean correctas (prueba login web primero)

**Autor:** Jonathan Cerda  
**Fecha:** Marzo 2026  
**Versión:** 1.0
