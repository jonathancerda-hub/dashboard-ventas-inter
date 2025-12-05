# Copilot instructions for dashboard-ventas-inter

This file contains concise, action-oriented guidance for AI coding agents working on this repository.

Key project facts
- Python Flask web app (single file router `app.py`) that renders dashboards using Jinja2 templates in `templates/`.
- Primary data sources: Odoo via XML-RPC (`odoo_manager.py`) and Google Sheets via `google_sheets_manager.py` (gspread + google-auth).
- Visualizations are client-side with ECharts and Chart.js; templates inject JSON contexts produced in `app.py`.

What to read first (quick onboarding order)
1. `project-context.md` — high level overview of architecture and data flow.
2. `app.py` — entrypoint; contains routes, data aggregation logic, and where chart data are prepared and injected into templates.
3. `odoo_manager.py` — data access layer for Odoo. Understand how `get_sales_lines` and `get_pending_orders` compute `amount_currency`, partner/order identifiers, and filtering by sales channel.
4. `google_sheets_manager.py` — how metas and equipos (teams) are read/written to Google Sheets tabs.
5. `templates/dashboard_clean.html` and `templates/dashboard_linea.html` — how server-side data are rendered and consumed by client JS (ECharts/Chart.js formatters).

Project-specific conventions and patterns
- Data canonical numeric field: prefer `amount_currency` (Odoo) as authoritative monetary value; templates expect integers and US-style formatting (`toLocaleString('en-US')`). See usage in `app.py` and `templates/*`.
- Partner/order identity: many objects come as [id, name] lists from Odoo. Code tries partner lookups with `partner_id`, `partner`, `cliente_id` fallbacks. Preserve ids when possible (avoid matching by name).
- Include orders with zero invoicing: `orders_chart_data` construction in `app.py` intentionally merges sold (facturado) and pending (pendiente) per order — keep that behavior when editing order aggregation logic.
- Currency sign: project displays USD with `$` (templates were updated); avoid introducing `S/` (PEN) labels.
- JS debug statements: many console.* lines were silenced. Avoid reintroducing noisy client logs unless guarded by a debug flag.

Run / debug / local development
- Environment: uses `.env` variables (see top of `app.py` and `conectar_odoo.py`) for Odoo URL/user/pass, Google Sheets name, and `SECRET_KEY`.
- Install dependencies: check `requirements.txt` for pinned libs; create a venv and install via pip.
  Example: `python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt`
- Start server locally (development): `python app.py` (the app uses `app.run(debug=False)` in main). If you need Flask debug mode, change `app.run(debug=True)` temporarily and remember to disable before CI/production.
- Quick Odoo connectivity test: `conectar_odoo.py` uses the same `.env`; run it to validate credentials.

Tests and linting
- No test suite present. For small changes, run a syntax check (`python -m py_compile app.py`) and run a local lint tool if configured.
- After code edits, run `python -m py_compile` over modified files to catch syntax/indentation errors.

Integration points and secrets
- Odoo: XML-RPC endpoints; `odoo_manager.py` performs searches on models like `sale.order.line`, `sale.order`, `account.move.line`. Preserve query domains and team/channel filtering to avoid regressions.
- Google Sheets: depends on `credentials.json` (service account) in workspace root. `GoogleSheetsManager` expects specific worksheet/tab names (teams/metas). Changing sheet structure requires corresponding code updates.

Common fixes the project expects
- When adding charts: prefer server-side aggregation in `app.py` and expose JSON via `render_template(..., orders_chart_data=orders_chart_data)` rather than re-aggregating client-side.
- When handling money: round to integers for chart consumption and format with `toLocaleString('en-US')` + leading `$` in templates.
- When filtering by client/order: pass `partner_id` (int) query param instead of names.
- When aggregating products: ALWAYS use product code (`default_code`/`codigo_odoo`) as unique key, NEVER product name (names can vary for same product).

Files to update with care
- `app.py`: large, monolithic route functions — keep changes minimal and prefer extracting helpers rather than making functions even larger.
- `odoo_manager.py`: encapsulates XML-RPC logic; avoid changing how `amount_currency` or partner ids are derived without inspecting all call sites.
- `templates/*.html`: front-end behavior relies on JSON blobs injected with Jinja `tojson`; keep these injections safe and avoid creating multiple global JS variables with the same name.

Examples (concrete patterns)
- How orders are merged in `app.py`:
  - server groups `facturado_by_pedido` from sales lines and `pendiente_by_pedido` from pending orders then does:
    total = facturado + pendiente
    percent = facturado / total if total > 0 else 0
  - Keep the `order_id` and `partner` fields with ids when possible for click-to-filter actions.

Client-side features (dashboard_clean.html)
- Tabla de Productos del Cliente:
  - Accesible mediante botón "📦 Productos" en gráfico de Avance por Pedido
  - Agrupa productos por código único (`default_code`/`codigo_odoo`) — NUNCA por nombre de producto
  - Filtros: Estado (Todos/Facturado/Por Facturar) + Línea Comercial
  - Paginación automática: 15 productos por página (constante `productosPorPagina`)
  - Datos filtrados por cliente seleccionado (`selectedClienteId`)
  - Función clave: `procesarProductosCliente()` usa `Map` con `productoKey = productoCodigo`
  - Ordenamiento: descendente por monto (total/facturado/pendiente según filtro activo)
  - Reset automático a página 1 al cambiar filtros
- Data sources para productos:
  - `salesDataAll`: datos facturados (campo clave: `amount_currency`)
  - `pendingDataAll`: datos pendientes (campo clave: `total_pendiente`)
  - Ambos arrays contienen TODOS los clientes; filtrado se hace en frontend por `partner_id`

If you modify credentials or Google Sheets interaction
- Do NOT commit real credentials. `credentials.json` in the repo should be a service account key used locally — in CI use secrets or mounted credentials.

What not to change
- Don't change the canonical currency display or the `amount_currency` based computations without a clear migration plan.
- Avoid removing `partner_id`/`order_id` metadata when returning JSON to the templates — it's used for click-to-filter behavior.
- Do NOT change product aggregation logic to use product names — use product codes (`default_code`/`codigo_odoo`) as unique identifiers.
- Pagination constant `productosPorPagina = 15` in `dashboard_clean.html` — only change if explicitly requested.

If you need more context
- Ask for Odoo domain examples and a sample of `sales_data` JSON payload if you need to reproduce aggregation logic locally (I can instrument `odoo_manager.py` to dump limited mock data safely).

---
If this looks good, I will commit this file. Tell me if you want additions (CI steps, deployment, or developer-specific run scripts).