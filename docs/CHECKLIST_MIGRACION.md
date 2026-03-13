# ✅ CHECKLIST EJECUTABLE - Para Agente IA

> Sigue estos pasos en orden. Marca cada uno cuando lo completes.

---

## 🎯 OBJETIVO
Migrar conexión Odoo de XML-RPC a JSON-RPC para evitar error `RuntimeError: object unbound` del módulo `cs_login_audit_log`.

---

## FASE 1: PREPARACIÓN (5 min)

### [ ] 1.1 Verificar el problema
```bash
# Intenta conectar con el código actual
python app.py
# o
python odoo_manager.py
```

**¿Ves error con "RuntimeError: object unbound"?**
- ✅ Sí → Continúa con migración
- ❌ No → El problema es otro

### [ ] 1.2 Instalar dependencias
```bash
pip install requests
```

### [ ] 1.3 Verificar variables de entorno
```bash
# Verifica que existan estas variables en .env
cat .env | grep ODOO
```

**Debe mostrar:**
```
ODOO_URL=...
ODOO_DB=...
ODOO_USER=...
ODOO_PASSWORD=...
```

---

## FASE 2: LOCALIZACIÓN (5 min)

### [ ] 2.1 Encuentra el archivo de conexión
```bash
# Busca archivos que importan xmlrpc.client
grep -r "import xmlrpc.client" .
```

**Resultado típico:**
```
./odoo_manager.py:import xmlrpc.client
./odoo_client.py:import xmlrpc.client
```

### [ ] 2.2 Identifica la clase principal
Abre el archivo encontrado y busca la clase que gestiona Odoo.

**Usualmente:**
- `class OdooManager`
- `class OdooClient`
- `class OdooConnector`

### [ ] 2.3 Encuentra el método `__init__`
```python
def __init__(self):
    # Este es el método que hay que modificar
```

---

## FASE 3: BACKUP (2 min)

### [ ] 3.1 Crea respaldo
```bash
# Guarda el archivo original
cp odoo_manager.py odoo_manager.py.backup
```

### [ ] 3.2 Opcional: Crea rama git
```bash
git checkout -b fix/migrate-to-jsonrpc
```

---

## FASE 4: IMPLEMENTACIÓN (15 min)

### [ ] 4.1 Agregar imports
**Al inicio del archivo, después de los imports existentes:**

```python
import requests  # AGREGAR
import json      # AGREGAR
```

### [ ] 4.2 Modificar método `__init__`

**Busca esto:**
```python
common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
self.uid = common.authenticate(...)
self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
```

**Reemplaza con:**
```python
# Configuración JSON-RPC
self.rpc_timeout = 30
self.jsonrpc_url = f"{self.url}/jsonrpc"

# Autenticación JSON-RPC
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
    logging.info(f"✅ Odoo conectado (JSON-RPC). UID: {self.uid}")
else:
    self.uid = None
    self.models = None
```

### [ ] 4.3 Agregar método wrapper
**Después del método `__init__`, agrega:**

```python
def _create_jsonrpc_models_proxy(self):
    """Wrapper para mantener compatibilidad con código XML-RPC"""
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

### [ ] 4.4 Actualizar `authenticate_user` (si existe)

**Busca:**
```python
def authenticate_user(self, username, password):
```

**Si existe, reemplaza su contenido con:**
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
            
            return result["result"][0] if "result" in result and result["result"] else None
        return None
    except Exception as e:
        logging.error(f"Error: {e}")
        return None
```

---

## FASE 5: VERIFICACIÓN (5 min)

### [ ] 5.1 Verificar sintaxis
```bash
python -m py_compile odoo_manager.py
```

**Output esperado:** Sin errores

### [ ] 5.2 Crear script de prueba
```bash
# Crea test_conexion.py
cat > test_conexion.py << 'EOF'
import os
import requests
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
    print(f"✅ UID: {result['result']}")
else:
    print(f"❌ Error: {result}")
EOF
```

### [ ] 5.3 Ejecutar test
```bash
python test_conexion.py
```

**Output esperado:**
```
✅ UID: 6
```

### [ ] 5.4 Probar aplicación completa
```bash
python app.py
# o el comando que uses para iniciar
```

**Verifica:**
- ✅ No hay error `RuntimeError: object unbound`
- ✅ Log muestra "✅ Odoo conectado (JSON-RPC)"
- ✅ La aplicación carga datos de Odoo

---

## FASE 6: VALIDACIÓN FUNCIONAL (10 min)

### [ ] 6.1 Probar consultas básicas
```python
# En Python REPL o script
from odoo_manager import OdooManager

manager = OdooManager()
print(f"UID: {manager.uid}")

# Prueba consulta
partners = manager.models.execute_kw(
    manager.db, manager.uid, manager.password,
    'res.partner', 'search_read',
    [[]], {'limit': 3}
)
print(f"Partners: {len(partners)}")
```

**Output esperado:**
```
UID: 6
Partners: 3
```

### [ ] 6.2 Probar funcionalidad principal de la app
```bash
# Depende de tu aplicación
# Ejemplos:

# Si es Flask:
curl http://localhost:5000/api/products

# Si es CLI:
python main.py --list-products

# Si tiene dashboard:
# Abre en navegador y verifica que cargue datos
```

### [ ] 6.3 Verificar logs
```bash
tail -f app.log
# o donde se guarden los logs
```

**Busca:**
- ✅ "Odoo conectado (JSON-RPC)"
- ❌ NO debe haber "RuntimeError: object unbound"

---

## FASE 7: LIMPIEZA (3 min)

### [ ] 7.1 Eliminar código comentado (si hay)
Revisa que no queden líneas XML-RPC comentadas

### [ ] 7.2 Actualizar requirements.txt
```bash
echo "requests>=2.31.0" >> requirements.txt
```

### [ ] 7.3 Agregar comentario en código
```python
# odoo_manager.py - Línea 1
"""
NOTA: Este módulo usa JSON-RPC en lugar de XML-RPC para evitar el bug
del módulo cs_login_audit_log que bloquea conexiones externas.
Migración realizada: [FECHA]
"""
```

---

## FASE 8: DOCUMENTACIÓN (5 min)

### [ ] 8.1 Actualizar README.md
```markdown
## Conexión a Odoo

Esta aplicación usa **JSON-RPC** para conectarse a Odoo (no XML-RPC).

Ventajas:
- Evita bug del módulo `cs_login_audit_log`
- Mejor rendimiento
- Payloads más ligeros
```

### [ ] 8.2 Commit de cambios
```bash
git add .
git commit -m "fix: Migrar conexión Odoo de XML-RPC a JSON-RPC

- Reemplaza xmlrpc.client con requests + JSON-RPC
- Evita bug RuntimeError del módulo cs_login_audit_log
- Mejora rendimiento (JSON más ligero que XML)
- Mantiene compatibilidad total con API existente

Fixes #[ISSUE_NUMBER]"
```

### [ ] 8.3 Crear PR (si aplica)
```bash
git push origin fix/migrate-to-jsonrpc
# Crea PR en GitHub/GitLab
```

---

## FASE 9: MONITOREO POST-DEPLOY (Después del deploy)

### [ ] 9.1 Verificar en producción
- ✅ Aplicación inicia correctamente
- ✅ Se conecta a Odoo
- ✅ Consultas funcionan
- ✅ No hay errores en logs

### [ ] 9.2 Monitorear por 24h
```bash
# Revisa logs periódicamente
grep -i "error" /var/log/app.log
grep -i "odoo" /var/log/app.log
```

### [ ] 9.3 Eliminar backup (después de 1 semana)
```bash
# Solo si todo funciona bien
rm odoo_manager.py.backup
```

---

## 🚨 ROLLBACK SI ALGO FALLA

### Si necesitas revertir:
```bash
# Opción 1: Desde backup
cp odoo_manager.py.backup odoo_manager.py

# Opción 2: Desde git
git checkout main -- odoo_manager.py

# Reiniciar aplicación
python app.py
```

---

## 📊 RESUMEN DE TIEMPOS

| Fase | Tiempo Estimado |
|------|-----------------|
| Preparación | 5 min |
| Localización | 5 min |
| Backup | 2 min |
| Implementación | 15 min |
| Verificación | 5 min |
| Validación | 10 min |
| Limpieza | 3 min |
| Documentación | 5 min |
| **TOTAL** | **~50 min** |

---

## ✅ CRITERIOS DE ÉXITO

Al completar todas las fases:

- ✅ No hay error `RuntimeError: object unbound`
- ✅ Log muestra "Odoo conectado (JSON-RPC)"
- ✅ Todas las consultas a Odoo funcionan
- ✅ Tests pasan exitosamente
- ✅ Aplicación funciona igual que antes
- ✅ Código documentado y commiteado

---

## 🆘 TROUBLESHOOTING RÁPIDO

| Error | Solución |
|-------|----------|
| `ModuleNotFoundError: requests` | `pip install requests` |
| `Connection refused` | Verifica `ODOO_URL` en `.env` |
| `Authentication failed` | Verifica credenciales en `.env` |
| `Timeout` | Aumenta `self.rpc_timeout = 60` |
| `JSON decode error` | Verifica formato de respuesta |

---

**Usa este checklist marcando cada ítem. Al terminar todo marcado, la migración está completa.**
