# Contexto del Proyecto: Dashboard de Ventas Farmacéuticas

## 1. Resumen del Proyecto

Este proyecto es una aplicación web desarrollada en Flask que funciona como un **Dashboard de Ventas** para una empresa farmacéutica. La aplicación se conecta en tiempo real a un sistema ERP (Odoo) y a Google Sheets para visualizar, analizar y gestionar datos de ventas y metas comerciales.

El dashboard está dividido en dos grandes áreas:
1.  **Dashboard de Ventas Internacionales**: El dashboard principal, que muestra KPIs, análisis de ventas por cliente, línea comercial y producto. Integra las metas anuales por cliente para calcular la brecha comercial y el avance.
2.  **Gestión de Metas**: Incluye varias páginas para configurar los objetivos comerciales:
    *   **Metas por Cliente (Internacional)**: Permite definir metas de venta anuales para cada cliente internacional.
    *   **Metas por Línea (Nacional)**: Permite definir metas mensuales para cada línea comercial nacional.

La aplicación también provee interfaces para la visualización detallada de datos de ventas y pedidos en tablas con filtros y la capacidad de exportar a Excel.

## 2. Tecnologías y Librerías Clave

*   **Backend**:
    *   **Python**: Lenguaje principal de programación.
    *   **Flask**: Micro-framework web para construir la aplicación.
    *   **xmlrpc.client**: Para la comunicación con la API de Odoo.
    *   **gspread & google-auth**: Para interactuar con la API de Google Sheets.
    *   **Pandas**: Para la manipulación y agregación de datos.
    *   **python-dotenv**: Para la gestión de variables de entorno (credenciales, claves secretas).

*   **Frontend**:
    *   **HTML5 & Jinja2**: Para la estructura y renderizado de las plantillas.
    *   **CSS3**: Para el estilizado, con un diseño inspirado en la interfaz de Odoo.
    *   **JavaScript**: Para la interactividad y la creación de gráficos.
    *   **ECharts & Chart.js**: Librerías de JavaScript para la visualización de datos y gráficos interactivos.

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
    *   Filtro por cliente para visualizar los datos de un cliente específico, recalculando todos los KPIs y tablas en función de la selección.
    *   Tabla de ventas y proyecciones por Línea Comercial Internacional (campo `Facturado` muestra monto facturado).
    *   **Gráficos Interactivos**:
        *   **Análisis Jerárquico (Drill-Down)**: Permite explorar las ventas a través de una jerarquía de 5 niveles: Clasificación Farmacológica -> Forma Farmacéutica -> Vía de Administración -> Línea de Producción -> Producto. Características:
            *   **Sincronización bidireccional**: Al navegar entre niveles, el gráfico de pastel "Top Productos por Venta" se actualiza automáticamente mostrando los top 20 productos del nivel actual
            *   **Títulos dinámicos**: El título se actualiza según el nivel de navegación (ej: "Análisis Jerárquico: Ventas por Forma Farmacéutica")
            *   **Ordenamiento inteligente**: Todos los niveles se ordenan automáticamente de mayor a menor por monto de venta
            *   **Filtrado automático**: Excluye productos "No Definido" en todos los niveles
            *   **Normalización de nombres**: 13 productos especiales tienen nombres simplificados para agrupación consistente (ATREVIA 360°, ATREVIA ONE, BIOCAN, SURALAN, EARTHBORN, FORMULA NATURAL, GO NATIVE, GO NATIVE ESSENTIALS, NUTRIBITES, etc.)
            *   **Botón "Volver"**: Permite navegar hacia atrás en la jerarquía
        *   **Top Productos por Venta**: Gráfico de pastel tipo donut (radio 30%-60%) que muestra los top 20 productos con mayor facturación del nivel actual del Análisis Jerárquico. Características:
            *   **Formato donut**: Visualización con anillo central para mejor legibilidad
            *   **Porcentajes visibles**: Labels muestran "Nombre: XX%" directamente en el gráfico
            *   **Tooltip mejorado**: Muestra nombre, monto formateado y porcentaje con hint de interactividad
            *   **Sincronización automática**: Se actualiza al navegar en el gráfico jerárquico
            *   **Título dinámico**: Cambia según el nivel activo (ej: "Top Productos - Forma Farmacéutica: Comprimidos")
            *   **Agrupación por código**: Productos agrupados por `default_code` usando nombres normalizados
        *   **Top Productos Facturados**: Gráfico de barras horizontales que muestra los 7 productos con mayor facturación. Es interactivo y se actualiza al hacer clic en una línea comercial del gráfico de líneas.
        *   **Venta Internacional del Año por Línea Comercial**: Gráfico de barras verticales con meta vs facturado. Al hacer clic en una línea comercial, filtra el gráfico de productos para mostrar solo los top productos de esa línea. Incluye botón "✕ Ver Todos" para resetear el filtro.
        *   **Avance de Facturación por Cliente**: Un gráfico general tipo bullet chart que compara el avance de todos los clientes. Se oculta al seleccionar un cliente específico.
        *   **Panel Ejecutivo - Desempeño por Cliente**: Vista comparativa (barras apiladas horizontales) que muestra Facturado, Pendiente y Meta para todos los clientes cuando no hay filtro. Al hacer clic en una línea comercial del gráfico de líneas, se puede navegar al cliente. Cuando hay un cliente seleccionado, cambia a vista individual compacta con barra única, resumen ejecutivo y KPIs calculados (% Facturado, % Proyectado, Brecha).
    *   **Visualización por Cliente Seleccionado**:
        *   **Tarjeta de Avance**: Al filtrar por un cliente, aparece una tarjeta dedicada con una barra de progreso y colores de semáforo (rojo/amarillo/verde) que muestra su avance de facturación.
        *   **Panel Ejecutivo Individual**: Gráfico compacto ubicado justo después de la tarjeta de avance, mostrando barra apilada (Facturado + Pendiente), línea de meta y panel de resumen con indicadores ejecutivos.
        *   **Gráfico de Avance por Pedido**: Al seleccionar un cliente, se muestra un gráfico detallado con el avance de cada pedido. La barra principal muestra el valor total original del pedido de venta y la barra interior muestra el monto ya facturado. Incluye botón "📦 Productos" que permite alternar a una vista de tabla de productos.
        *   **Tabla de Productos del Cliente**: Vista alternativa al gráfico de pedidos que muestra una tabla detallada con todos los productos del cliente seleccionado. Características:
            *   **Acceso**: Botón "📦 Productos" en el gráfico de Avance por Pedido
            *   **Columnas**: Código, Producto, Línea Comercial, Cantidad, Monto Total, Estado
            *   **Filtros interactivos**:
                *   Estado: Todos / Facturado / Por Facturar (radio buttons, Por Facturar por defecto)
                *   Línea Comercial: selector desplegable dinámico con todas las líneas presentes en los productos del cliente
            *   **Agrupación crítica**: Por código único de producto (`default_code`/`codigo_odoo`) — NUNCA por nombre de producto
            *   **Paginación**: 15 productos por página con controles de navegación (← Anterior / Siguiente →) e información de página actual
            *   **Ordenamiento**: Por monto descendente (facturado/pendiente/total según filtro activo)
            *   **Estados visuales con colores**: Facturado (verde #27ae60), Por Facturar (naranja #e67e22), Mixto (azul #3498db)
            *   **Datos**: Filtra automáticamente por `partner_id` del cliente seleccionado desde `salesDataAll` y `pendingDataAll`
            *   **Navegación**: Botón "✕ Cerrar" para volver al gráfico de pedidos, reset automático a página 1 al cambiar filtros
    *   Exportación de datos de ventas facturadas y pendientes a Excel (usando campo `commercial_line_international_id` unificado).

*   **Vistas de Datos Detallados**:
    *   `/sales`: Tabla paginada y con filtros de todas las líneas de facturas de venta internacionales. Columna "Descripcion" consolidada (sin columna "Medida" separada).
    *   `/pending`: Tabla paginada y con filtros de todos los pedidos de venta internacionales pendientes de facturar. Columna "Descripcion" consolidada (sin columna "Medida" separada).