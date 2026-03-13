# 🤖 PROMPT PARA AGENTE IA: Migrar Odoo de XML-RPC a JSON-RPC

> **Para usar con Claude/ChatGPT/Agentes IA en otros proyectos**

---

## 📋 Contexto del Problema

Aplicación Python conectada a Odoo **falla con este error**:

```
RuntimeError: object unbound
File "cs_login_audit_log/models/res_users.py", line 23, in _check_credentials
    ip_address = request.httprequest.environ.get('REMOTE_ADDR')
```

**Causa:** Módulo de terceros `cs_login_audit_log` bloquea XML-RPC  
**Solución:** Cambiar a JSON-RPC (evita el módulo problemático)

---

## 🎯 Instrucciones para el Agente IA

### PASO 1: Localizar el archivo de conexión

Busca el archivo que gestiona la conexión a Odoo. Usualmente se llama:
- `odoo_manager.py`
- `odoo_client.py`
- `odoo_connector.py`
- O dentro de `app.py` / `main.py`

**Busca código como:**
```python
import xmlrpc.client
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
```

### PASO 2: Modificar imports

**Agregar al inicio del archivo:**
```python
import requests  # NUEVO
import json      # NUEVO
```

**Verificar que `requests` esté instalado:**
```bash
pip install requests
```

### PASO 3: Reemplazar el método `__init__` o la función de autenticación

**Busca el código de autenticación XML-RPC y reemplázalo con:**

```python
def __init__(self):
    """Inicializar conexión con Odoo usando JSON-RPC"""
    try:
        # Cargar credenciales (ajusta según el proyecto)
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
            logging.warning(f"❌ Autenticación falló")
            
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

### PASO 4: Si hay método `authenticate_user`, también actualizarlo

**Busca:**
```python
def authenticate_user(self, username, password):
    common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
    uid = common.authenticate(...)
```

**Reemplaza con:**
```python
def authenticate_user(self, username, password):
    """Autenticar usuario contra Odoo via JSON-RPC"""
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
            else:
                return {'id': uid, 'name': username, 'login': username}
        else:
            return None
            
    except Exception as e:
        logging.error(f"Error en authenticate_user: {e}")
        return None
```

### PASO 5: Crear script de prueba

Crea `test_conexion_odoo.py`:

```python
#!/usr/bin/env python
"""Probar conexión JSON-RPC a Odoo"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

url = os.getenv('ODOO_URL')
db = os.getenv('ODOO_DB')
username = os.getenv('ODOO_USER')
password = os.getenv('ODOO_PASSWORD')

print(f"Probando conexión a: {url}")

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
        print(f"✅ Autenticación exitosa! UID: {uid}")
        
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
            print(f"✅ Consulta exitosa! Encontrados {len(partners)} partners:")
            for p in partners:
                print(f"   - {p['name']}")
            
            print("\n🎉 MIGRACIÓN EXITOSA A JSON-RPC")
        else:
            print(f"❌ Error en consulta: {result}")
    else:
        print(f"❌ Autenticación falló: {result}")
        
except Exception as e:
    print(f"❌ Error: {e}")
```

**Ejecutar:**
```bash
python test_conexion_odoo.py
```

---

## ✅ Checklist de Verificación

Después de implementar los cambios, verifica:

- [ ] `import requests` agregado
- [ ] Código de autenticación usa `jsonrpc_url` en lugar de `xmlrpc/2/common`
- [ ] Método `_create_jsonrpc_models_proxy()` implementado
- [ ] Variable `self.models` usa el proxy JSON-RPC
- [ ] Test script ejecuta exitosamente
- [ ] Aplicación principal puede conectarse a Odoo
- [ ] No hay errores de `RuntimeError: object unbound`

---

## 🎯 Ubicaciones Típicas del Código

### Flask
```python
# Usualmente en app.py o manager.py
from odoo_manager import OdooManager

data_manager = OdooManager()  # Se conecta aquí
```

### Django
```python
# Usualmente en settings.py o apps.py
from .odoo_client import OdooClient

ODOO = OdooClient()
```

### FastAPI
```python
# Usualmente en main.py o dependencies.py
from odoo_connector import OdooConnector

odoo = OdooConnector()
```

---

## 🐛 Errores Comunes y Soluciones

### Error: "ModuleNotFoundError: No module named 'requests'"
```bash
pip install requests
```

### Error: "Connection refused"
Verifica que `ODOO_URL` no tenga espacios ni caracteres extra:
```python
self.url = os.getenv('ODOO_URL').strip()
```

### Error: "Authentication failed"
1. Verifica credenciales en `.env`
2. Prueba login en Odoo web primero
3. Considera usar API Key en lugar de contraseña

### Error: "Timeout"
Aumenta el timeout:
```python
self.rpc_timeout = 60  # segundos
```

---

## 📄 Template de Comentario para Commit

```
fix: Migrar conexión Odoo de XML-RPC a JSON-RPC

- Reemplaza xmlrpc.client con requests + JSON-RPC
- Evita bug del módulo cs_login_audit_log que bloquea XML-RPC
- Mejora rendimiento (JSON más ligero que XML)
- Mantiene compatibilidad con API existente via proxy

Archivos modificados:
- odoo_manager.py: Autenticación y wrapper JSON-RPC
- test_conexion_odoo.py: Script de validación

Probado en: Odoo 16.0
Referencia: RuntimeError object unbound en cs_login_audit_log
```

---

## 📚 Recursos Necesarios

Archivos de referencia completos en este proyecto:

1. `odoo_manager.py` - Implementación completa
2. `odoo_jsonrpc_client.py` - Cliente standalone reutilizable
3. `test_odoo_jsonrpc.py` - Script de prueba completo
4. `docs/guia-migracion-xmlrpc-a-jsonrpc.md` - Documentación técnica

---

## 💡 Tip para el Agente IA

**Si el proyecto ya tiene código complejo:**

1. **No elimines todo el código existente**, solo reemplaza la sección de autenticación
2. **Mantén la estructura de la clase** existente
3. **El wrapper `JSONRPCModelsProxy`** garantiza compatibilidad con código que usa `models.execute_kw()`
4. **Todas las llamadas existentes** a `models.execute_kw()` seguirán funcionando sin cambios

**La clave es:** Cambiar cómo se autentica y cómo se ejecutan las llamadas, pero mantener la misma interfaz API.

---

**Última actualización:** Marzo 2026  
**Autor:** Jonathan Cerda  
**Proyecto origen:** Dashboard-Ventas-INTER
