# Plantilla de Code Review Arquitectónico (Architectural Code Review Template)
## Prompt para Análisis SOLID, Seguridad, Rendimiento y Mantenibilidad (SOLID, Security, Performance & Maintainability Analysis)

> 📋 **Propósito (Purpose)**: Plantilla reutilizable para generar análisis arquitectónico exhaustivo de cualquier proyecto
> 🎯 **Uso (Usage)**: Copiar este documento y adaptar la sección "Configuración del Proyecto" 
> 📅 **Versión (Version)**: 1.0 - Marzo 2026

---

## 🚀 Instrucciones de Uso (Usage Instructions)

### Paso 1: Configurar Proyecto (Step 1: Configure Project)

Edita la sección **"Configuración del Proyecto"** con los datos de tu proyecto:
- Stack tecnológico específico
- Lenguaje y framework principal
- Base de datos utilizada
- Servicios externos integrados
- Archivos principales a analizar

### Paso 2: Copiar Prompt Completo (Step 2: Copy Full Prompt)

Copia todo el contenido desde **"INICIO DEL PROMPT"** hasta **"FIN DEL PROMPT"** y pégalo en tu herramienta de IA.

### Paso 3: Ejecutar Análisis (Step 3: Run Analysis)

La IA generará un documento completo siguiendo la estructura de CODE_REVIEW_SENIOR.md.

---

## ⚙️ Configuración del Proyecto (Project Configuration)

**PERSONALIZA ESTA SECCIÓN ANTES DE USAR EL PROMPT (CUSTOMIZE THIS SECTION BEFORE USING THE PROMPT)**:

```yaml
# Información del Proyecto (Project Information)
nombre_proyecto: "[Nombre de tu proyecto]"
descripcion: "[Descripción breve del proyecto]"

# Stack Tecnológico (Technology Stack)
lenguaje_principal: "[Python/Java/Node.js/etc.]"
framework: "[Flask/Django/Spring/Express/etc.]"
base_datos: "[PostgreSQL/MySQL/MongoDB/etc.]"
servicios_externos: 
  - "[Servicio 1: ej. Google OAuth]"
  - "[Servicio 2: ej. Stripe Payments]"
  - "[Servicio 3: ej. Redis Cache]"

# Archivos Principales (Main Files)
archivos_clave:
  - "[ej. app.py]"
  - "[ej. src/controllers/]"
  - "[ej. models/]"
  - "[ej. services/]"

# Áreas de Enfoque (Focus Areas) - Marca las que apliquen
analisis_completo: true  # false si solo quieres ciertas áreas
areas_especificas:
  - solid: true
  - seguridad_owasp: true
  - rendimiento: true
  - mantenibilidad: true
  - validacion_inputs: true
  - caching: true
```

---

## 📝 INICIO DEL PROMPT (START OF PROMPT)

```markdown
Realiza un Code Review Arquitectónico exhaustivo (exhaustive Architectural Code Review) de este proyecto siguiendo esta estructura bilingüe (bilingual structure).

---

### 🎯 Objetivo del Análisis (Analysis Objective)

Generar documento tipo **CODE_REVIEW_SENIOR.md** con:
- Puntuación numérica (x/10) en cada área (numeric scoring)
- Ejemplos de código específicos con números de línea (specific code examples with line numbers)
- Refactors concretos, NO solo descripciones (concrete refactors, NOT just descriptions)
- Formato bilingüe: **Español (English)** en todos los títulos

---

### 📊 Áreas de Análisis (Analysis Areas)

#### 1️⃣ Principios SOLID (SOLID Principles) — Puntuación /10 cada uno

**Analizar (Analyze)**:

**1.1 Single Responsibility Principle (SRP)**
- ✅/⚠️/❌ Estado actual (Current state)
- Archivos/clases que violan SRP (Files/classes violating SRP)
- Ejemplos de código con líneas exactas (Code examples with exact lines)
- Refactor sugerido con código de ejemplo (Suggested refactor with code example)
- Impacto en mantenibilidad (Impact on maintainability)

**1.2 Open/Closed Principle (OCP)**
- Áreas cerradas a extensión (Areas closed to extension)
- Código que requiere modificación frecuente (Code requiring frequent modification)
- Patrón de diseño recomendado (Recommended design pattern)
- Implementación de ejemplo (Example implementation)

**1.3 Liskov Substitution Principle (LSP)**
- Jerarquías de herencia problemáticas (Problematic inheritance hierarchies)
- Violaciones de contrato (Contract violations)
- Refactor con interfaces abstractas (Refactor with abstract interfaces)

**1.4 Interface Segregation Principle (ISP)**
- Interfaces "gordas" detectadas (Detected "fat" interfaces)
- Métodos no utilizados en implementaciones (Unused methods in implementations)
- Segregación recomendada (Recommended segregation)

**1.5 Dependency Inversion Principle (DIP)**
- Dependencias hardcodeadas (Hardcoded dependencies)
- Acoplamiento fuerte detectado (Strong coupling detected)
- Implementación de inyección de dependencias (Dependency injection implementation)

---

#### 2️⃣ Seguridad OWASP Top 10 (OWASP Top 10 Security) — Puntuación /10 cada categoría

**Analizar (Analyze)**:

**2.1 A01: Broken Authentication (Autenticación Rota)**
- ❌ Problemas identificados (Identified problems):
  - Expiración de sesiones (Session expiration)
  - Configuración de cookies (Cookie configuration)
  - Manejo de tokens (Token handling)
  - MFA ausente (Missing MFA)
- ✅ Implementación recomendada con código (Recommended implementation with code)
- 🧪 Tests de validación sugeridos (Suggested validation tests)

**2.2 A02: Cryptographic Failures (Fallas Criptográficas)**
- Credenciales en texto plano (Plaintext credentials)
- Algoritmos débiles (Weak algorithms)
- Manejo de secrets (Secrets management)
- Solución con vault/encriptación (Vault/encryption solution)

**2.3 A03: Injection (Inyección)**
- SQL Injection: queries vulnerables (vulnerable queries)
- XSS: puntos de entrada sin sanitizar (unsanitized entry points)
- Command Injection: ejecución de comandos (command execution)
- Fix con parametrización/sanitización (Fix with parameterization/sanitization)

**2.4 A04: Insecure Design (Diseño Inseguro)**
- Security headers ausentes (Missing security headers)
- CORS mal configurado (Misconfigured CORS)
- Rate limiting inexistente (Missing rate limiting)
- Implementación de headers completa (Complete headers implementation)

**2.5 A05: Security Misconfiguration (Configuración Insegura)**
- Errores expuestos en producción (Exposed errors in production)
- Servicios innecesarios activos (Unnecessary active services)
- Permisos excesivos (Excessive permissions)
- Hardening recomendado (Recommended hardening)

**2.6 A06: Vulnerable & Outdated Components (Componentes Vulnerables)**
- Auditoría de dependencias (Dependency audit)
- CVEs identificados (Identified CVEs)
- Plan de actualización (Update plan)
- Comando de verificación (Verification command)

**2.7 A07: Identification & Authentication Failures (Fallas de Identificación)**
- Verificación de identidad débil (Weak identity verification)
- Ausencia de MFA (Missing MFA)
- Integración LDAP/SSO recomendada (Recommended LDAP/SSO integration)

**2.8 A08: Software & Data Integrity Failures (Fallas de Integridad)**
- Auditoría de cambios ausente (Missing change audit)
- Versionamiento de datos (Data versioning)
- Implementación de audit log (Audit log implementation)

**2.9 A09: Logging & Monitoring Failures (Fallas de Logging)**
- Estado actual de logging (Current logging state)
- Información faltante en logs (Missing log information)
- Implementación estructurada (Structured implementation)
- Integración con ELK/Datadog (ELK/Datadog integration)

**2.10 A10: Server-Side Request Forgery (SSRF)**
- Validación de URLs (URL validation)
- Whitelist de hosts (Host whitelist)
- Protección contra IPs privadas (Private IP protection)

---

#### 3️⃣ Rendimiento y Optimización (Performance & Optimization) — Puntuación /10 cada aspecto

**3.1 Validación de Inputs (Input Validation)**
- ❌ Problemas detectados (Detected problems):
  - Falta de validación de tipos (Missing type validation)
  - Sin límites de valores (No value limits)
  - Confianza ciega en datos externos (Blind trust in external data)
- ✅ Esquema de validación con Pydantic/Joi/etc (Validation schema)
- 📊 Impacto estimado en seguridad (Estimated security impact)

**3.2 Optimización de Consultas (Query Optimization)**
- N+1 queries identificadas (Identified N+1 queries)
- Falta de paginación (Missing pagination)
- Índices faltantes en BD (Missing DB indexes)
- Llamadas duplicadas (Duplicate calls)
- Solución con caché/eager loading (Cache/eager loading solution)

**3.3 Caching Estratégico (Strategic Caching)**
- Estado actual de caché (Current cache state)
- Oportunidades de cache (Cache opportunities)
- Implementación con Redis/Memcached (Redis/Memcached implementation)
- TTL recomendado por tipo de dato (Recommended TTL per data type)
- Invalidación de cache (Cache invalidation)

**3.4 Manejo de Memoria (Memory Management)**
- Cargas masivas en RAM detectadas (Detected massive RAM loads)
- DataFrames/Arrays sin optimizar (Unoptimized DataFrames/Arrays)
- Streaming recomendado (Recommended streaming)
- Generators vs Lists (Generators vs Lists)

**3.5 Async/Concurrencia (Async/Concurrency)**
- Operaciones bloqueantes (Blocking operations)
- Oportunidades de paralelización (Parallelization opportunities)
- Implementación async/await (Async/await implementation)
- Thread pools para I/O (Thread pools for I/O)

---

#### 4️⃣ Mantenibilidad (Maintainability) — Puntuación /10 cada aspecto

**4.1 Legibilidad del Código (Code Readability)**
- Funciones demasiado largas (Functions too long)
- Complejidad ciclomática alta (High cyclomatic complexity)
- Refactor para claridad (Refactor for clarity)

**4.2 Nomenclatura y Convenciones (Naming & Conventions)**
- Inconsistencias detectadas (Detected inconsistencies)
- Variables poco descriptivas (Non-descriptive variables)
- Guía de estilo recomendada (Recommended style guide)

**4.3 Documentación (Documentation)**
- Docstrings ausentes (Missing docstrings)
- README incompleto (Incomplete README)
- Comentarios de código (Code comments)
- Documentación de API (API documentation)

**4.4 Patrones de Diseño (Design Patterns)**
- Patrones identificados (Identified patterns)
- Anti-patterns detectados (Detected anti-patterns)
- Patrones recomendados (Recommended patterns)
- Ejemplos de implementación (Implementation examples)

**4.5 Tests y Cobertura (Tests & Coverage)**
- Cobertura actual (Current coverage)
- Tests faltantes críticos (Missing critical tests)
- Unit/Integration/E2E ratio
- Mejora de test strategy (Test strategy improvement)

**4.6 Estructura de Archivos (File Structure)**
- Organización actual (Current organization)
- Acoplamiento entre módulos (Module coupling)
- Reestructuración recomendada (Recommended restructuring)

---

#### 5️⃣ Arquitectura (Architecture) — Puntuación /10 cada aspecto

**5.1 Separación de Capas (Layer Separation)**
- Presentación/Negocio/Datos mezclados (Mixed Presentation/Business/Data)
- Capas claramente definidas (Clearly defined layers)
- Refactor a arquitectura limpia (Refactor to clean architecture)

**5.2 Patrones REST/GraphQL (REST/GraphQL Patterns)**
- Adhesión a estándares REST (REST standards adherence)
- Versionamiento de API (API versioning)
- Manejo de errores HTTP (HTTP error handling)
- Documentación OpenAPI/Swagger (OpenAPI/Swagger documentation)

**5.3 Escalabilidad (Scalability)**
- Arquitectura actual: monolito/microservicios (Current architecture)
- Cuellos de botella (Bottlenecks)
- Estado compartido problemático (Problematic shared state)
- Estrategia de escalamiento (Scaling strategy)

**5.4 Manejo de Errores (Error Handling)**
- Try/catch ausentes (Missing try/catch)
- Excepciones genéricas (Generic exceptions)
- Logging de errores (Error logging)
- Estrategia consistente (Consistent strategy)

**5.5 Configuración (Configuration)**
- Environment variables (Variables de entorno)
- Secrets management (Manejo de secretos)
- Config por ambiente (Config per environment)
- Validación de configuración (Configuration validation)

---

### 📋 Formato de Salida Requerido (Required Output Format)

```markdown
# Code Review Arquitectónico — [Nombre Proyecto] (Architectural Code Review — [Project Name])
## Análisis Senior: SOLID, Seguridad, Rendimiento, Mantenibilidad (Senior Analysis: SOLID, Security, Performance, Maintainability)

> 📅 **Última actualización (Last update)**: [fecha]  
> 📊 **Progreso (Progress)**: [X/10]  
> ✅ **Fortalezas (Strengths)**: [lista concisa]  
> 🔴 **Crítico (Critical)**: [lista de issues prioritarios]  
> 🔄 **Siguiente fase (Next phase)**: [roadmap Q1/Q2/Q3]

---

## Resumen Ejecutivo (Executive Summary)

**Puntuación General (Overall Score): X/10**

| Área (Area) | Puntuación (Score) | Estado (Status) | Prioridad (Priority) | Cambios (Changes) |
|-------------|---------------------|-----------------|----------------------|-------------------|
| Principios SOLID (SOLID Principles) | X/10 | ✅⚠️🔴 | Alta/Media/Baja | ⬆️/⬇️/= |
| Seguridad OWASP (OWASP Security) | X/10 | ... | ... | ... |
| Rendimiento (Performance) | X/10 | ... | ... | ... |
| Mantenibilidad (Maintainability) | X/10 | ... | ... | ... |
| Arquitectura (Architecture) | X/10 | ... | ... | ... |

### ✅ Mejoras Implementadas (Implemented Improvements)
[Si es análisis de seguimiento]

### 🔴 Issues Críticos Priorizados (Prioritized Critical Issues)
1. [Issue 1 con severidad y líneas de código]
2. [Issue 2 con severidad y líneas de código]
3. [Issue 3 con severidad y líneas de código]

---

[DESARROLLAR CADA SECCIÓN DETALLADAMENTE CON LA ESTRUCTURA DEFINIDA ARRIBA]
[DEVELOP EACH SECTION IN DETAIL WITH THE STRUCTURE DEFINED ABOVE]

---

## 📈 Roadmap de Implementación (Implementation Roadmap)

### Q1 2026 (Crítico - Critical)
- [ ] [Mejora 1 con código ejemplo]
- [ ] [Mejora 2 con código ejemplo]
- **Impacto estimado (Estimated impact)**: [% mejora]

### Q2 2026 (Alto - High)
- [ ] [Mejora 3]
- [ ] [Mejora 4]
- **Impacto estimado (Estimated impact)**: [% mejora]

### Q3 2026 (Medio - Medium)
- [ ] [Mejora 5]
- [ ] [Mejora 6]
- **Impacto estimado (Estimated impact)**: [% mejora]

---

## 🧪 Validación de Cambios (Change Validation)

### Tests Automáticos (Automated Tests)
```bash
# Seguridad (Security)
pip-audit  # o npm audit
safety check

# Linting
pylint src/  # o eslint src/
flake8 --max-complexity=10

# Tests
pytest --cov=src --cov-report=html
# o jest --coverage

# Performance
pytest tests/performance/ --benchmark
```

### Métricas de Éxito (Success Metrics)
- **Seguridad (Security)**: CVEs: [antes] → 0 (objetivo)
- **Performance**: Response time: [antes]ms → [objetivo]ms
- **Cobertura (Coverage)**: [antes]% → 80%+ (objetivo)
- **Complejidad (Complexity)**: CC: [antes] → <10 (objetivo)

---

## 📚 Referencias y Recursos (References & Resources)

### Documentación Oficial (Official Documentation)
- [Framework]: [link]
- OWASP Top 10 2021: https://owasp.org/Top10/
- [DB]: Best practices

### Herramientas Recomendadas (Recommended Tools)
- **Security**: Bandit, Safety, Snyk
- **Performance**: cProfile, py-spy, Artillery
- **Quality**: SonarQube, CodeClimate
- **Monitoring**: Sentry, Datadog, New Relic

---
```

---

### 🎯 Requisitos Específicos del Prompt (Specific Prompt Requirements)

**IMPORTANTE - INCLUIR EN EL PROMPT (IMPORTANT - INCLUDE IN PROMPT)**:

1. **Ejemplos de Código con Líneas (Code Examples with Lines)**
   ```
   Cada ejemplo DEBE incluir (Each example MUST include):
   - Número de línea exacto (Exact line number)
   - Contexto de 5 líneas antes/después (5 lines context before/after)
   - Fix concreto, NO descripción (Concrete fix, NOT description)
   ```

2. **Cálculo de Impacto (Impact Calculation)**
   ```
   Para optimizaciones, calcular (For optimizations, calculate):
   - % mejora estimada en performance (% estimated performance improvement)
   - Reducción de memoria (Memory reduction)
   - Tiempo de respuesta (Response time)
   ```

3. **Comandos Ejecutables (Executable Commands)**
   ```
   Todos los comandos de validación deben ser (All validation commands must be):
   - Copy-paste ready
   - Con output esperado (With expected output)
   - Multiplataforma si es posible (Cross-platform if possible)
   ```

4. **Priorización Clara (Clear Prioritization)**
   ```
   Cada issue debe tener (Each issue must have):
   - 🔴 Crítico: Seguridad/Performance bloqueante
   - 🟠 Alto: Mantenibilidad/Escalabilidad
   - 🟡 Medio: Refactors deseables
   - 🟢 Bajo: Nice-to-have
   ```

---

## FIN DEL PROMPT (END OF PROMPT)
```

---

## 💡 Tips de Uso (Usage Tips)

### Para Proyectos Nuevos (For New Projects)
```markdown
Enfocarse en (Focus on):
- SOLID (prevenir deuda técnica)
- Seguridad desde diseño (security by design)
- Estructura escalable (scalable structure)
```

### Para Proyectos Legacy (For Legacy Projects)
```markdown
Priorizar (Prioritize):
1. Seguridad OWASP crítica (critical OWASP security)
2. Performance bottlenecks
3. Refactors graduales SOLID (gradual SOLID refactors)
```

### Para Auditorías ISO 27001
```markdown
Énfasis en (Emphasis on):
- A03, A04, A08 OWASP
- Logging & Monitoring completo
- Documentación exhaustiva
- Audit trails
```

---

## 🔄 Versiones y Actualizaciones (Versions & Updates)

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 23/03/2026 | Versión inicial bilingüe |
| ... | ... | ... |

---

## 📞 Soporte (Support)

Para consultas sobre esta plantilla (For questions about this template):
- Issues: [crear issue en repo]
- Docs: [link documentación]
- Ejemplos: Ver CODE_REVIEW_SENIOR.md en este mismo directorio

---

**🎯 Resultado Esperado (Expected Result)**: 
Documento markdown de 50-100 páginas con análisis completo, puntuaciones numéricas, código de ejemplo y roadmap de implementación trimestral.

**⏱️ Tiempo Estimado de Análisis (Estimated Analysis Time)**: 
- Proyecto pequeño (<5K LOC): 10-15 minutos
- Proyecto mediano (5K-20K LOC): 20-30 minutos  
- Proyecto grande (>20K LOC): 40-60 minutos
