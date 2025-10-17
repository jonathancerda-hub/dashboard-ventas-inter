# Contexto del Proyecto: Dashboard de Ventas Farmacéuticas

## 1. Resumen del Proyecto

Este proyecto es una aplicación web desarrollada en Flask que funciona como un **Dashboard de Ventas** para una empresa farmacéutica. La aplicación se conecta en tiempo real a un sistema ERP (Odoo) y a Google Sheets para visualizar, analizar y gestionar datos de ventas y metas comerciales.

El dashboard está dividido en dos grandes áreas:
1.  **Ventas Internacionales**: Un dashboard principal que muestra KPIs, análisis de ventas por cliente, línea comercial, producto y otras clasificaciones.
2.  **Ventas Nacionales**: Un dashboard secundario enfocado en el rendimiento de las líneas comerciales y los vendedores individuales contra sus metas mensuales.

La aplicación también provee interfaces para la gestión de metas y la visualización detallada de datos en tablas con filtros y exportación a Excel.

## 2. Tecnologías y Librerías Clave

*   **Backend**:
    *   **Python**: Lenguaje principal de programación.
    *   **Flask**: Micro-framework web para construir la aplicación.
    *   **xmlrpc.client**: Para la comunicación con la API de Odoo.
    *   **gspread & google-auth**: Para interactuar con la API de Google Sheets.
    *   **Pandas**: Para la manipulación y agregación de datos.
    *   **python-dotenv**: Para la gestión de variables de entorno (credenciales, claves secretas).
    *   **openpyxl**: Para la creación de archivos Excel (`.xlsx`).

*   **Frontend**:
    *   **HTML5 & Jinja2**: Para la estructura y renderizado de las plantillas.
    *   **CSS3**: Para el estilizado, con un diseño inspirado en la interfaz de Odoo.
    *   **JavaScript**: Para la interactividad y la creación de gráficos.
    *   **ECharts & Chart.js**: Librerías de JavaScript para la visualización de datos y gráficos interactivos.
    *   **Tom-Select**: Para la creación de selectores de búsqueda avanzados (en la gestión de equipos).

*   **Fuentes de Datos**:
    *   **Odoo**: El sistema ERP principal de donde se extraen los datos de ventas, pedidos, clientes y productos.
    *   **Google Sheets**: Utilizado como una base de datos simple para almacenar y gestionar las metas de venta y la composición de los equipos comerciales.

## 3. Estructura del Proyecto

*   `app.py`:
    *   **Rol**: Es el corazón de la aplicación.
    *   **Funcionalidad**: Define todas las rutas (URLs), maneja la lógica de negocio, procesa las peticiones del usuario, se comunica con los *managers* de datos (`OdooManager`, `GoogleSheetsManager`), procesa los datos y los pasa a las plantillas de Jinja2 para ser renderizados.

*   `odoo_manager.py`:
    *   **Rol**: Capa de acceso a datos para Odoo (Data Access Layer).
    *   **Funcionalidad**: Encapsula toda la lógica de conexión y consulta al ERP Odoo a través de su API XML-RPC. Contiene métodos para autenticar, obtener líneas de venta, pedidos pendientes, clientes, productos, etc.

*   `google_sheets_manager.py`:
    *   **Rol**: Capa de acceso a datos para Google Sheets.
    *   **Funcionalidad**: Gestiona la conexión con la API de Google Sheets. Se encarga de leer y escribir las metas de venta (por línea y por vendedor) y la configuración de los equipos comerciales.

*   `templates/`:
    *   **Rol**: Capa de presentación (Vistas).
    *   **Contenido**: Archivos HTML con plantillas Jinja2 que definen la estructura visual de cada página (`dashboard_clean.html`, `meta.html`, `login.html`, etc.).

*   `static/`:
    *   **Rol**: Almacén de archivos estáticos.
    *   **Contenido**: Archivos CSS (`style.css`), imágenes y, potencialmente, archivos JavaScript del lado del cliente.

*   `.env`:
    *   **Rol**: Archivo de configuración.
    *   **Contenido**: Almacena credenciales y configuraciones sensibles (URL de Odoo, usuario, contraseña, nombre de la hoja de Google, clave secreta de Flask) de forma segura, sin exponerlas en el código fuente.

*   `conectar_odoo.py`:
    *   **Rol**: Script de utilidad.
    *   **Funcionalidad**: Es un script simple para probar la conexión con Odoo usando las credenciales del archivo `.env`, útil para depuración.

## 4. Flujo de Datos Típico

1.  **Petición del Usuario**: El usuario navega a una URL, por ejemplo, `/dashboard`.
2.  **Enrutamiento de Flask**: `app.py` recibe la petición en la función `dashboard()`.
3.  **Autenticación**: La función verifica si el usuario ha iniciado sesión (revisando la `session` de Flask).
4.  **Recolección de Datos**:
    *   La función `dashboard()` llama a `OdooManager` para obtener los datos de ventas (`get_sales_lines`) y los pedidos pendientes (`get_pending_orders`) del año actual.
    *   También puede llamar a `GoogleSheetsManager` para obtener datos de metas si fuera necesario en esa vista.
5.  **Procesamiento de Datos**:
    *   Dentro de la función `dashboard()`, los datos crudos de Odoo se procesan y agregan usando bucles de Python y, en algunos casos, la librería Pandas.
    *   Se calculan KPIs (total de ventas, brecha comercial), se agrupan ventas por línea, por producto, etc.
6.  **Renderizado de la Plantilla**:
    *   Los datos procesados se pasan como contexto a la plantilla `dashboard_clean.html` a través de la función `render_template()`.
7.  **Visualización en el Cliente**:
    *   El navegador del usuario recibe el HTML.
    *   El código JavaScript dentro de la plantilla toma los datos (inyectados como JSON en variables de JS) y utiliza las librerías ECharts y Chart.js para dibujar los gráficos interactivos.

## 5. Funcionalidades Principales

*   **Autenticación**: Sistema de `login`/`logout` que valida las credenciales del usuario contra la base de datos de usuarios de Odoo.

*   **Dashboard Internacional (`/dashboard`)**:
    *   KPIs clave: Ventas totales, meta, brecha comercial.
    *   Filtro por cliente para visualizar los datos de un cliente específico.
    *   Tabla de ventas y proyecciones por Línea Comercial.
    *   Gráficos de "Top Productos" y "Ventas por Línea Comercial".
    *   Gráfico jerárquico (drill-down) que permite explorar desde Línea Comercial -> Clasificación Farmacológica -> Producto.
    *   Gráfico de avance de facturación por cliente (Bullet Chart).
    *   Exportación de datos de ventas facturadas y pendientes a Excel.

*   **Dashboard Nacional por Línea (`/dashboard_linea`)**:
    *   Filtros por mes y línea comercial.
    *   KPIs de rendimiento de la línea (meta vs. venta, avance, etc.).
    *   Tabla de rendimiento individual de cada vendedor del equipo, comparando su venta con su meta.
    *   Gráficos de "Top Productos" y "Ventas por Forma Farmacéutica" para la línea seleccionada.

*   **Gestión de Metas por Línea (`/meta`)**:
    *   Interfaz para establecer las metas de venta mensuales para cada línea comercial y para E-commerce.
    *   Los datos se guardan en una pestaña específica de Google Sheets.

*   **Gestión de Equipos y Metas por Vendedor (`/metas_vendedor`)**:
    *   Interfaz para asignar vendedores (obtenidos de Odoo) a diferentes equipos comerciales.
    *   Tabla pivotante para asignar metas mensuales (total e IPN) a cada vendedor de cada equipo.
    *   Los datos de equipos y metas individuales se guardan en Google Sheets.

*   **Vistas de Datos Detallados**:
    *   `/sales`: Tabla paginada y con filtros de todas las líneas de facturas de venta internacionales.
    *   `/pending`: Tabla paginada y con filtros de todos los pedidos de venta internacionales pendientes de facturar.