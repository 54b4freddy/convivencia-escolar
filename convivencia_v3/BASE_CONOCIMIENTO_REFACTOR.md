# Base de conocimiento — refactor Flask / multi-colegio (v7)

Ultra-conciso; solo lo acordado o implementado en el hilo de refactor. Sin narrativa.

## Stack y arquitectura

- **Flask** monolito modular: `app.py` = config, cookies, páginas (`/`, `/login`, `/dashboard`), `GET /health`, `register_blueprints(app)`.
- **Blueprints** (`routes/__init__.py`): `auth_api`, `institucion`, `estudiantes`, `faltas` (módulo `faltas.py`, bp interno `faltas_citas`), `senales`, `asistencia`, `catalogo`, `reportes`.
- **Capas**: `ce_db` (SQLite/PG, `init_db`, migraciones ligeras `_migrate_schema`), `ce_queries.fq` (listado faltas por rol/año), `ce_faltas_service`, `ce_pdf`, `ce_export`, `ce_constants` (listas canónicas formularios).
- **`routes/authz.py`**: `login_required`, `roles`, `cu()`, **`resolve_colegio_id(u)`** → `(colegio_id|None, error|None)`; Superadmin **sin** `colegio_id` en sesión debe enviar `colegio_id` (query GET o JSON/form en POST/PATCH/PUT/DELETE); otros roles sin colegio → fallback `1` (compat).

## Multi-colegio (seguridad / datos)

- **`fq(usuario, anio, filtros)`**: usa `usuario["colegio_id"] or 1`. Rutas que listan faltas arman `u_sc = {**u, "colegio_id": tenant_id}` tras `resolve_colegio_id`.
- **Aplicado `resolve_colegio_id`** (o comprobación explícita de fila vs tenant) en: `reportes`, `catalogo`, `asistencia`, `estudiantes`, `faltas` (incl. citas `PATCH /api/citas/<cita_id>`), `senales`, `institucion` (listados/usuarios).
- **`GET /api/colegios`**: solo Superadmin ve todos; resto solo su colegio (sin `colegio_id` en sesión → 403).
- **`POST /api/usuarios`**: Superadmin obliga **`colegio_id` entero** en JSON; Coordinador usa tenant de sesión. **PATCH/DELETE usuario**: Coordinador solo mismo colegio; no toca Superadmin ni asigna rol Superadmin.
- **Login / `GET /api/me`**: `_norm_colegio_id` en `auth_api.py` (entero o `null` en JSON).
- **Índices** (idempotentes en `init_db`, `ce_db.py`): `faltas`, `estudiantes`, `catalogo_faltas`, `senales_atencion`, `asistencia_*`, `citas_acudiente` (por `colegio_id` + campos de filtro frecuentes).

## Estado actual

### Hecho

- Extracción de API desde `app.py` a blueprints por dominio (arriba).
- Reportes/PDF/CSV/cerrar año en `routes/reportes.py` (PDF curso/estudiante/general/acta con reglas por rol; acta verifica `f.colegio_id == tenant`).
- `ce_constants.py` + `@app.context_processor` inyecta `tipos_documento` y `barreras_opciones` en plantillas.
- `templates/dashboard.html`: selects de tipo de documento y barreras generados desde esas listas; fila **`uColegioRow`** + `#uColegioId` para alta de usuario Superadmin multi-institución.
- `static/app.js`: `openNuevoUsr` async carga colegios; `guardarUsuario` usa selector o `CU.colegio_id` / un solo colegio.
- Tests: `tests/test_multitenant.py` (`resolve_colegio_id`, reportes superadmin, coordinador no PATCH usuario otro colegio).

### Pendiente / no verificado en hilo

- Ejecutar **`pytest` completo** al menos una vez tras los últimos cambios (una corrida se interrumpió en el entorno).
- **Roadmap opcional**: `create_app()` factory, caché reportes pesados, paginación listados, más tests API, rate limiting.
- **UX/formularios**: no se acordaron principios nuevos por escrito; el flujo de pasos en “Registrar falta” y overlays **ya existía** en plantillas/JS; solo se alinearon listas canónicas y el selector de institución para superadmin.

## Archivos clave (mapa rápido)

| Área | Ruta |
|------|------|
| App mínima | `app.py` |
| Registro blueprints | `routes/__init__.py` |
| Tenant | `routes/authz.py` (`resolve_colegio_id`) |
| Sesión / me | `routes/auth_api.py` |
| Colegios / usuarios staff | `routes/institucion.py` |
| Constantes UI | `ce_constants.py` |
| Dashboard UI | `templates/dashboard.html`, `static/app.js` |
| Queries faltas | `ce_queries.py` |
| BD + índices | `ce_db.py` (`init_db`) |
| Tests multi-tenant | `tests/test_multitenant.py` |

## Cómo usar este `.md` para trabajar más eficiente

1. **Al abrir un chat nuevo**: pega al inicio *solo* la sección que aplica (p. ej. “Multi-colegio” + “Archivos clave”) o adjunta el archivo con la instrucción: *“Obedece BASE_CONOCIMIENTO_REFACTOR.md; no contradigas lo allí sin preguntar.”*
2. **Al pedir una feature**: indica *“respeta `resolve_colegio_id` y el patrón de blueprints”* + ruta del módulo si ya sabes dónde va.
3. **Antes de merge**: checklist corto — `pytest`, grep de `colegio_id or 1` sin `resolve` en rutas nuevas, Superadmin sin colegio en prueba manual si tocó API.
4. **Mantén el archivo vivo**: tras cada tanda, añade 2–4 bullets en *Estado* o *Archivos*; borra duplicados. Objetivo: **< 120 líneas** para que siga cabiendo en contexto junto con código.
