h1. Manual de Usuario: Dashboard de Ventas

h2. Introducción

Bienvenido al manual del Dashboard de Ventas. Esta aplicación ha sido diseñada para proporcionar una visión clara y en tiempo real del rendimiento comercial de la empresa, tanto a nivel nacional como internacional.

El sistema se conecta directamente con *Odoo* para obtener datos de ventas y con *Google Sheets* para gestionar las metas comerciales, ofreciendo una herramienta centralizada para el análisis y la toma de decisiones.

h2. Inicio de Sesión

Para acceder al sistema, deberás utilizar las mismas credenciales (usuario y contraseña) que usas para ingresar a Odoo.

{info:title=Credenciales}
Si tienes problemas para acceder, verifica que tu usuario y contraseña de Odoo sean correctos. El sistema valida la autenticación directamente con el ERP.
{info}

h2. Dashboard Internacional (Principal)

Esta es la pantalla principal de la aplicación. Ofrece una vista panorámica de las ventas internacionales del año en curso.

h3. Filtro por Cliente

En la parte superior izquierda, encontrarás un menú desplegable para filtrar todos los datos del dashboard por un cliente específico. Al seleccionar un cliente, todos los KPIs, tablas y gráficos se recalcularán para mostrar únicamente la información de ese cliente. Para ver los datos de todos los clientes, selecciona la opción "Todos los clientes".

h3. KPIs Principales

La fila superior muestra los indicadores clave de rendimiento:
* *Venta Proyectada del Año:* Suma de todo lo facturado en el año más los pedidos pendientes de facturar para el cliente seleccionado (o todos).
* *Meta:* La meta de ventas definida en la sección "Metas por Cliente". Si se selecciona un cliente, muestra la meta de ese cliente. Si no, muestra la suma de las metas de todos los clientes.
* *Brecha Comercial:* La diferencia entre la Venta Proyectada y la Meta.
* *% Avance:* El porcentaje de la meta que se ha alcanzado con la venta facturada.

h3. Análisis por Cliente Seleccionado

Cuando filtras por un cliente específico, el dashboard se transforma para ofrecerte un análisis detallado de ese cliente:

* *Tarjeta de Avance de Facturación:* Aparece una nueva tarjeta en la parte superior que muestra el progreso de facturación de los pedidos de ese cliente. Una barra de progreso con colores de semáforo (rojo, amarillo, verde) te permite evaluar rápidamente su estado.
* *Gráfico de Avance por Pedido:* Justo debajo, verás un gráfico que desglosa el avance de cada pedido individual del cliente. La barra principal representa el valor total original del pedido y la barra interior (bala) muestra cuánto se ha facturado.

{info:title=Ocultamiento de Gráfico General}
Al seleccionar un cliente, el gráfico general "Avance de Facturación por Cliente" se oculta para dar paso a la vista detallada.
{info}

h3. Tabla de Ventas por Línea Comercial

Esta tabla desglosa el rendimiento por cada línea comercial internacional:
* *Venta Total ($):* Lo que ya ha sido facturado para esa línea.
* *Por Facturar ($):* El valor de los pedidos de venta que están confirmados pero aún no se han facturado.
* *% Part.:* Porcentaje de participación de la línea sobre la venta total.
* *Meta:* La meta específica para esa línea, calculada a partir de los datos de "Metas por Cliente".
* *Brecha:* La diferencia entre la proyección (Venta + Por Facturar) y la meta de la línea.
* *% Avance:* El progreso porcentual hacia la meta de la línea.

h3. Gráficos de Análisis

La parte inferior del dashboard contiene varios gráficos para un análisis más profundo:
* *Top Productos Facturados:* Muestra los productos con mayor volumen de venta facturada.
* *Venta Internacional por Línea Comercial:* Un resumen visual de la tabla principal.
* *Análisis Jerárquico de Ventas:* Un potente gráfico "drill-down" que te permite explorar las ventas a través de múltiples niveles. La nueva jerarquía es:
# Clasificación Farmacológica
# Formas Farmacéuticas
# Vía de Administración
# Línea de Producción
# Producto
Al hacer clic en una barra, el gráfico de pastel "Venta por Clasificación Farmacológica" se actualizará para mostrar el desglose del siguiente nivel.
* *Avance de Facturación por Cliente:* Un gráfico de tipo "bullet" que compara lo facturado contra el total de pedidos para cada cliente, mostrando el porcentaje de avance.

h2. Gestión de Metas (por Línea)

Esta sección (accesible desde el Dashboard Nacional) permite establecer las metas de venta mensuales para cada línea comercial nacional y para E-commerce. La interfaz ha sido rediseñada para ser más clara y moderna.

# *Selecciona un mes:* Usa el selector de la parte superior para elegir el mes para el cual deseas definir las metas.
# *Ingresa las metas:* Para cada línea comercial, verás una "tarjeta" individual. Rellena los campos "Meta Total" y "Meta IPN".
# *Visualiza los totales:* Una tarjeta de resumen en la parte inferior muestra la suma total de las metas que has ingresado, actualizándose en tiempo real.
# *Guarda los cambios:* Haz clic en el botón *"Guardar Metas"*. Los datos se almacenarán en Google Sheets.

h2. Gestión de Metas (por Cliente)

Esta sección, accesible desde el menú de navegación del Dashboard Internacional, es donde se definen las metas de venta anuales para cada cliente internacional. Estos datos son la base para los KPIs y la tabla de rendimiento del dashboard.

# *Selecciona un año:* Usa el menú desplegable en la parte superior para elegir el año para el cual deseas ver o editar las metas.
# *Ingresa las metas:* La página muestra una tabla con todos los clientes internacionales. Para cada cliente, puedes ingresar la meta de venta anual en las columnas correspondientes a cada línea comercial (AGROVET, PETMEDICA, AVIVET).
# *Cálculos automáticos:*
## La columna *"Total Cliente ($)"* se actualiza automáticamente a medida que ingresas los números, mostrando la meta total para cada cliente.
## La fila inferior *"Total por Línea"* suma las metas de todos los clientes para cada línea comercial.
## La celda *"Total General"* muestra la suma de todas las metas.
# *Guarda los cambios:* Cuando termines, haz clic en el botón *"Guardar Metas"*. Los datos se almacenarán en Google Sheets y se usarán en el dashboard principal.

{info:title=Persistencia de Datos}
Después de guardar, los valores que ingresaste permanecerán en los campos, permitiéndote continuar editando o verificando sin que se borren.
{info}

h2. Vistas Detalladas

Desde el menú de navegación superior, puedes acceder a vistas de tabla detalladas:

* *Ventas ({{/sales}}):* Muestra una tabla con todas las líneas de facturas de venta internacionales. Incluye filtros por fecha, cliente y un campo de búsqueda general.
* *Pendientes ({{/pending}}):* Muestra una tabla con todos los pedidos de venta internacionales que están pendientes de facturar. También cuenta con filtros similares.

h2. Exportación de Datos

La aplicación permite exportar datos a formato *Excel (.xlsx)* desde varias ubicaciones:

* *Desde el Dashboard Internacional:* En la tabla de "Total por Línea Comercial", encontrarás dos botones:
** {{Exp. Facturado}}: Descarga un detalle de todas las ventas ya facturadas para el cliente seleccionado (o todos si no hay selección).
** {{Exp. Por Facturar}}: Descarga un detalle de todos los pedidos pendientes de facturar.
* *Desde las Vistas Detalladas:* En las páginas {{/sales}} y {{/pending}}, también encontrarás botones para exportar los datos que se están visualizando.