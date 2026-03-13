# 🎯 COPY-PASTE RÁPIDO: Arreglar Odoo XML-RPC → JSON-RPC

**Para Claude/ChatGPT en otro proyecto. Solo copiar y pegar este mensaje:**

---

> Hola Claude, necesito que arregles un problema de conexión a Odoo en este proyecto.

## Problema
La aplicación Python falla al conectarse a Odoo con este error:
```
RuntimeError: object unbound
cs_login_audit_log/models/res_users.py", line 23
```

## Solución
Cambiar de XML-RPC a JSON-RPC. Sigue estos pasos:

### 1. Instalar requests
```bash
pip install requests
```

### 2. Localiza el archivo de conexión Odoo
Busca el archivo que contiene código como:
```python
import xmlrpc.client
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
```

Suele estar en: `odoo_manager.py`, `odoo_client.py`, `app.py`, o similar.

### 3. Agrega estos imports al inicio
```python
import requests
import json
```

### 4. Reemplaza el código de autenticación

**Busca el método `__init__` que tiene código XML-RPC y reemplázalo con:**

```python
def __init__(self):
    try:
        # Credenciales (ajusta según tu proyecto)
        self.url = os.getenv('ODOO_URL')
        self.db = os.getenv('ODOO_DB')
        self.username = os.getenv('ODOO_USER')
        self.password = os.getenv('ODOO_PASSWORD')
        
        if not all([self.url, self.db, self.username, self.password]):
            raise ValueError("Faltan variables de entorno de Odoo")
        
        self.rpc_timeout = 30
        self.jsonrpc_url = f"{self.url}/jsonrpc"
        
        # Autenticar con JSON-RPC
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
        
        response = requests.post(self.jsonrpc_url, json=payload, headers=headers, timeout=self.rpc_timeout)
        result = response.json()
        
        if "result" in result and result["result"]:
            self.uid = result["result"]
            self.models = self._create_jsonrpc_models_proxy()
            logging.info(f"✅ Odoo conectado (JSON-RPC). UID: {self.uid}")
        else:
            self.uid = None
            self.models = None
            logging.warning("❌ Autenticación falló")
    except Exception as e:
        self.uid = None
        self.models = None
        logging.error(f"Error: {e}")

def _create_jsonrpc_models_proxy(self):
    """Wrapper para mantener compatibilidad con código existente"""
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
            
            return result.get("result") if "result" in result else None
    
    return JSONRPCModelsProxy(self)
```

### 5. Si existe método `authenticate_user`, también actualizarlo

```python
def authenticate_user(self, username, password):
    try:
        headers = {"Content-Type": "application/json"}
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
        
        response = requests.post(self.jsonrpc_url, json=auth_payload, headers=headers, timeout=self.rpc_timeout)
        result = response.json()
        
        if "result" in result and result["result"]:
            uid = result["result"]
            
            read_payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "object",
                    "method": "execute_kw",
                    "args": [self.db, uid, password, 'res.users', 'read', [uid], {'fields': ['name', 'login']}]
                },
                "id": 2
            }
            
            response = requests.post(self.jsonrpc_url, json=read_payload, headers=headers, timeout=self.rpc_timeout)
            result = response.json()
            
            return result["result"][0] if "result" in result and result["result"] else {'id': uid, 'name': username, 'login': username}
        return None
    except Exception as e:
        logging.error(f"Error authenticate_user: {e}")
        return None
```

### 6. Crea script de prueba `test_odoo.py`

```python
import os, requests
from dotenv import load_dotenv

load_dotenv()
url = f"{os.getenv('ODOO_URL')}/jsonrpc"
payload = {
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
        "service": "common",
        "method": "authenticate",
        "args": [os.getenv('ODOO_DB'), os.getenv('ODOO_USER'), os.getenv('ODOO_PASSWORD'), {}]
    },
    "id": 1
}

response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
result = response.json()

if "result" in result and result["result"]:
    print(f"✅ Conexión exitosa! UID: {result['result']}")
else:
    print(f"❌ Error: {result}")
```

**Ejecuta:** `python test_odoo.py`

### 7. Verifica que funcione

- [ ] No más error `RuntimeError: object unbound`
- [ ] Log muestra "✅ Odoo conectado (JSON-RPC)"
- [ ] Todas las consultas funcionan normal

## Notas Importantes

1. **No cambies** el resto del código que usa `models.execute_kw()` - el wrapper mantiene compatibilidad
2. **JSON-RPC** evita el módulo bugueado `cs_login_audit_log`
3. **Mismo comportamiento**, solo cambia el protocolo de comunicación
4. **Mejor rendimiento** (JSON es más rápido que XML)

## Si algo falla

- Verifica que `requests` esté instalado: `pip install requests`
- Verifica `.env` tiene `ODOO_URL`, `ODOO_DB`, `ODOO_USER`, `ODOO_PASSWORD`
- Aumenta timeout si es lento: `self.rpc_timeout = 60`

---

**Implementa estos cambios y confirma cuando funcione. Si encuentras algún problema específico, avísame con el error exacto.**
