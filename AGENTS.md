## Guía para agentes (AI) y contribuciones

Este repo se usa en varios colegios (multi-institución). La prioridad es **evitar regresiones**, **evitar errores de tenant**, y **reducir conflictos de merge**.

### Principios

- **No tocar producto sin pedirlo**: si el objetivo es refactor/infra (p.ej. modularizar JS o CI), no cambies UX, textos, reglas de negocio ni endpoints.
- **Mantener compatibilidad**: cambios deben ser incrementales. Si no hay bundler, mantener `<script>` simples y ordenados.
- **Multi-tenant primero**:
  - No asumas `colegio_id=1`.
  - En endpoints protegidos usa resolución de institución (p.ej. `resolve_colegio_id`) y filtra por `colegio_id`.
  - Evita filtrar/actualizar registros de otro colegio.

### Reglas de edición (front)

- **Sin bundler** (por ahora): el código corre con variables globales.
- **Al modularizar `static/app.js`**:
  - `app.js` es el **shell**: helpers, router, init, componentes compartidos.
  - Módulos por área (`promocion.js`, `prevencion.js`, etc.) se cargan desde `templates/dashboard.html` respetando dependencias.
  - Si un módulo depende de `api`, `toast`, `openOv`, etc., debe cargarse **después** de `app.js`.
  - Evita introducir nuevas dependencias front sin acuerdo previo.
- **Validación mínima JS**: antes de cerrar un cambio, correr:

```bash
node --check convivencia_v3/static/app.js
node --check convivencia_v3/static/promocion.js
node --check convivencia_v3/static/prevencion.js
```

### Reglas de edición (back)

- **Evitar migraciones innecesarias**: si el cambio no requiere DB, no metas cambios de esquema.
- **Cambios de DB**: deben incluir tests o al menos un caso de prueba de API que cubra el camino principal.

### Pruebas (mínimo)

- Ejecuta la suite:

```bash
cd convivencia_v3
python -m pytest -q
```

### Checklist antes de proponer PR

- [ ] Cambios alineados con el objetivo (refactor/infra vs producto).
- [ ] No hay hardcodes de `colegio_id`.
- [ ] `pytest` pasa.
- [ ] `node --check` pasa en los JS tocados.
- [ ] Se actualizó el template si se agregaron scripts (`dashboard.html`).

