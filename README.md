# Dashboard de Ventas Farmacéuticas

Una aplicación web desarrollada en Flask que funciona como un **Dashboard de Ventas** en tiempo real, conectándose a un sistema ERP (Odoo) y a Google Sheets para visualizar, analizar y gestionar datos de ventas y metas comerciales.

## Características Principales

- **Dashboard Internacional**: Visualización de KPIs, análisis de ventas por cliente, línea comercial y producto. Incluye gráficos interactivos y de tipo "drill-down".
- **Dashboard Nacional**: Enfocado en el rendimiento de las líneas comerciales y los vendedores individuales contra sus metas mensuales.
- **Gestión de Metas**: Interfaces para configurar metas de venta por línea comercial y por vendedor, almacenadas en Google Sheets.
- **Autenticación Segura**: Sistema de inicio de sesión que valida credenciales contra Odoo y verifica al usuario contra una lista blanca (whitelist) para un control de acceso granular.
- **Exportación de Datos**: Funcionalidad para exportar datos de ventas facturadas y pedidos pendientes a formato Excel (`.xlsx`).
- **Visualización Detallada**: Tablas paginadas y con filtros para explorar en detalle las ventas y los pedidos pendientes.

## Tecnologías Utilizadas

*   **Backend**:
    *   Python
    *   Flask (Micro-framework web)
    *   Pandas (Manipulación y agregación de datos)
    *   `xmlrpc.client` (Comunicación con la API de Odoo)
    *   `gspread` (Interacción con la API de Google Sheets)
    *   `python-dotenv` (Gestión de variables de entorno)

*   **Frontend**:
    *   HTML5 / Jinja2
    *   CSS3
    *   JavaScript
    *   ECharts & Chart.js (Librerías de gráficos)

*   **Fuentes de Datos**:
    *   Odoo (ERP)
    *   Google Sheets

## Configuración y Puesta en Marcha

Sigue estos pasos para configurar y ejecutar el proyecto en tu entorno local.

### 1. Prerrequisitos

- Python 3.x instalado.
- Acceso a una instancia de Odoo.
- Una cuenta de Google con acceso a la API de Google Sheets y un documento de Sheets preparado.

### 2. Clonar el Repositorio

```bash
git clone <url-del-repositorio>
cd <nombre-del-directorio>
```

### 3. Crear y Activar un Entorno Virtual

Es una buena práctica trabajar en un entorno virtual para aislar las dependencias del proyecto.

```bash
# En Windows
python -m venv venv
.\venv\Scripts\activate

# En macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Instalar Dependencias

Instala todas las librerías necesarias desde el archivo `requirements.txt`.

```bash
pip install -r requirements.txt
```

### 5. Configurar Variables de Entorno

Crea un archivo llamado `.env` en la raíz del proyecto y añade las siguientes variables con tus credenciales. Este archivo es ignorado por Git para proteger la información sensible.

```ini
# Credenciales de Odoo
ODOO_URL=https://tu-instancia.odoo.com
ODOO_DB=nombre_de_tu_db
ODOO_USER=tu_usuario_odoo
ODOO_PASSWORD=tu_contraseña_odoo

# Configuración de Google Sheets
GOOGLE_SHEET_NAME="Nombre de tu Documento de Google Sheets"

# Clave secreta de Flask (puedes generar una cadena aleatoria)
SECRET_KEY='una_clave_secreta_muy_segura'
```

### 6. Configurar Credenciales de Google API

1.  Sigue la guía de Google para crear una **Cuenta de Servicio** y obtener un archivo de credenciales JSON.
2.  Renombra este archivo a `credentials.json` y colócalo en la raíz del proyecto.
3.  Abre el archivo `credentials.json`, copia el correo electrónico de la cuenta de servicio (campo `client_email`) y compártelo con permisos de "Editor" en tu documento de Google Sheets.

### 7. Configurar Usuarios Permitidos

Crea un archivo llamado `allowed_users.json` en la raíz del proyecto. Este archivo define qué usuarios (por su correo de Odoo) pueden acceder a la aplicación.

```json
{
    "allowed_emails": [
        "usuario1@tuempresa.com",
        "gerente.ventas@tuempresa.com"
    ]
}
```

### 8. Ejecutar la Aplicación

Una vez que todo está configurado, puedes iniciar el servidor de desarrollo de Flask.

```bash
python app.py
```

La aplicación estará disponible en `http://127.0.0.1:5000`.

## 9. Despliegue en Producción

Para desplegar la aplicación en un entorno de producción, no se debe usar el servidor de desarrollo de Flask (`app.run()`). En su lugar, se recomienda utilizar un servidor WSGI como **Gunicorn** (que ya está incluido en `requirements.txt`).

### Ejemplo de Ejecución con Gunicorn

```bash
# El comando --bind 0.0.0.0:8000 expone la aplicación en el puerto 8000.
# El comando --workers 4 inicia 4 procesos para manejar peticiones concurrentes.
gunicorn --bind 0.0.0.0:8000 --workers 4 app:app
```

**Consideraciones Adicionales:**

-   **Variables de Entorno**: En producción, es más seguro gestionar las variables de entorno a través del sistema operativo o de herramientas de despliegue, en lugar de un archivo `.env`.
-   **Modo Debug**: Asegúrate de que el modo de depuración de Flask esté desactivado (`debug=False` en `app.py`).
-   **Proxy Inverso**: Es una buena práctica colocar un servidor web como Nginx o Apache delante de Gunicorn para que actúe como proxy inverso, gestione las peticiones HTTPS y sirva los archivos estáticos de manera eficiente.

## 10. Solución de Problemas (Troubleshooting)

*   **Error: "No tienes permiso para acceder a esta aplicación."**
    *   **Causa**: El usuario se autenticó correctamente en Odoo, pero su correo electrónico no está en la lista blanca.
    *   **Solución**: Añade el correo del usuario al array `allowed_emails` en el archivo `allowed_users.json` y reinicia la aplicación.

*   **Error: "Error de configuración: El archivo de usuarios permitidos no se encuentra."**
    *   **Causa**: El archivo `allowed_users.json` no existe en la raíz del proyecto.
    *   **Solución**: Crea el archivo `allowed_users.json` siguiendo el formato especificado en la sección de configuración.

*   **Error al conectar con Odoo o Google Sheets.**
    *   **Causa**: Las credenciales en el archivo `.env` o `credentials.json` son incorrectas, o hay un problema de red.
    *   **Solución**: Verifica que todas las variables en `.env` sean correctas y que el archivo `credentials.json` esté bien configurado y en la ubicación correcta. Asegúrate de que el servidor donde se ejecuta la aplicación tenga acceso a internet y pueda alcanzar las URLs de Odoo y Google.

*   **Los datos en el dashboard principal no se actualizan.**
    *   **Causa**: El dashboard principal utiliza un sistema de caché que almacena los datos durante 10 minutos para mejorar el rendimiento.
    *   **Solución**: Espera a que el caché expire (10 minutos) o, si necesitas una actualización inmediata, reinicia el servidor de la aplicación Flask.

---

*Este README fue generado para documentar la estructura y configuración del proyecto Dashboard de Ventas.*