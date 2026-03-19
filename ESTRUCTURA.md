# Estructura del Proyecto - Dashboard Ventas Internacionales

## 📁 Estructura de carpetas

```
Dashboard-Ventas-INTER/
├── app.py                      # Aplicación principal Flask  
├── requirements.txt            # Dependencias del proyecto
├── runtime.txt                # Versión de Python para deploy
├── .env                       # Variables de entorno (no versionado)
├── .env.example              # Plantilla de variables de entorno
│
├── database/                  # 🗄️ Gestión de bases de datos
│   ├── __init__.py
│   ├── odoo_manager.py       # Conexión y queries a Odoo (XML-RPC/JSON-RPC)
│   ├── supabase_manager.py   # ✅ Gestión de metas en Supabase (PostgreSQL)
│   └── google_sheets_manager.py  # [Legacy] Solo para metas de equipos
│
├── migrations/                # 📦 Scripts de migración de datos
│   ├── __init__.py
│   ├── create_metas_table.sql        # SQL para crear tabla en Supabase
│   ├── migrate_auto.py               # Migración automática GSheets → Supabase
│   └── migrate_sheets_to_supabase.py # Migración interactiva
│
├── scripts/                   # 🔧 Utilidades y testing
│   ├── __init__.py
│   ├── test_odoo_jsonrpc.py         # Test de conexión Odoo JSON-RPC
│   ├── test_odoo_manager.py         # Test de OdooManager
│   ├── test_supabase_metas.py       # Test de guardado/lectura Supabase
│   ├── test_clientes_metas.py       # Verificar clientes en lista
│   ├── verificar_clientes_faltantes.py  # Buscar clientes específicos
│   ├── check_supabase_project.py    # Verificar proyecto Supabase conectado
│   ├── conectar_odoo.py             # Test básico de conexión Odoo
│   ├── odoo_connector_alternativo.py  # Múltiples métodos de conexión
│   └── odoo_jsonrpc_client.py       # Cliente JSON-RPC standalone
│
├── templates/                 # 🎨 Plantillas HTML (Jinja2)
│   ├── base.html
│   ├── dashboard_clean.html
│   ├── metas_cliente.html    # ✅ Ahora usa Supabase
│   ├── login.html
│   └── ...
│
├── static/                    # 📦 Archivos estáticos
│   ├── css/
│   ├── js/
│   └── world.json
│
├── docs/                      # 📚 Documentación del proyecto
│   ├── project-context.md
│   ├── arquitectura-sistema.md
│   └── ...
│
└── .github/                   # ⚙️ Configuración GitHub
    └── copilot-instructions.md

```

## 🔄 Cambios importantes

### ✅ Migración completada: Google Sheets → Supabase (metas de clientes)

**Antes:**
- Metas de clientes internacionales se guardaban en Google Sheets
- Latencia alta al leer/escribir
- Requería credenciales JSON de Google API

**Ahora:**
- ✅ Metas almacenadas en **PostgreSQL (Supabase)**
- ✅ Lectura/escritura instantánea
- ✅ 60 registros migrados (2025: 29 clientes, 2026: 31 clientes)
- ✅ Constraint único: `(año, cliente_id)` previene duplicados
- ✅ Trigger automático: `updated_at` se actualiza en cada modificación

**Archivos afectados:**
- `app.py`: Rutas `/dashboard` y `/metas_cliente` usan `supabase_manager`
- `database/supabase_manager.py`: Nuevo gestor de conexión a Supabase
- `migrations/create_metas_table.sql`: DDL de tabla `metas_clientes`

### Google Sheets (mantiene uso para)
- ❌ ~~Metas de clientes~~ → **Migrado a Supabase**
- ✅ Metas de equipos de venta (todavía en Google Sheets)

## 🚀 Instalación

```bash
# 1. Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# 4. Ejecutar aplicación
python app.py
```

## 🔑 Variables de entorno requeridas

```env
# Odoo ERP
ODOO_URL=https://tu-instancia.odoo.com
ODOO_DB=nombre-base-datos
ODOO_USER=usuario@empresa.com
ODOO_PASSWORD=password_o_api_key

# Supabase (para metas de clientes)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGc...

# Google Sheets (para metas de equipos)
GOOGLE_SHEET_NAME=NombreHoja

# OAuth2 Google
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxx

# Flask
SECRET_KEY=clave-secreta-aleatoria
FLASK_ENV=development  # o production
```

## 📊 Base de datos

### Supabase (PostgreSQL)
**Tabla:** `metas_clientes`
```sql
id, año, cliente_id, cliente_nombre, 
agrovet, petmedica, avivet, total, 
created_at, updated_at
```

**Queries comunes:**
```sql
-- Ver metas de 2026
SELECT * FROM metas_clientes WHERE año = '2026' ORDER BY total DESC;

-- Sumar total por año
SELECT año, SUM(total) as total_meta FROM metas_clientes GROUP BY año;
```

## 🧪 Testing

```bash
# Test de conexión Supabase
python scripts/test_supabase_metas.py

# Test de conexión Odoo
python scripts/test_odoo_manager.py

# Verificar clientes específicos
python scripts/verificar_clientes_faltantes.py
```

## 📝 Notas

- **Autenticación:** OAuth2 con Google
- **Sesiones:** Expiran tras 15 minutos de inactividad
- **Clientes:** Incluye clientes con pedidos sin facturar (agregados automáticamente)
- **Cache:** 10 minutos para reducir consultas a Odoo

## 🔗 Enlaces útiles

- [Supabase Dashboard](https://supabase.com/dashboard/project/ppmbwujtfueilifisxhs)
- [Documentación Odoo](https://www.odoo.com/documentation/)
- [Guía de migración JSON-RPC](docs/guia-migracion-xmlrpc-a-jsonrpc.md)
