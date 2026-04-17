# Guía para subir el proyecto a GitHub y desplegarlo en Railway

Esta guía está pensada si es la **primera vez** que usas GitHub y Railway. Al final tendrás una **URL pública (HTTPS)** para abrir la aplicación desde el **móvil**, la **tablet** u otro PC.

---

## Qué vas a conseguir

| Paso | Resultado |
|------|-----------|
| GitHub | Copia de seguridad del código y historial de cambios |
| Railway | Servidor en internet con tu app Flask siempre encendida |
| URL | Algo como `https://tu-app.up.railway.app` — la abres en cualquier navegador |

**Importante:** No subas nunca archivos con contraseñas reales. El archivo `.env` está en `.gitignore` y **no** debe ir a GitHub.

---

## Parte 1 — Preparar la carpeta correcta

El código que despliegas debe ser la carpeta donde está `app.py` (en este proyecto suele llamarse **`convivencia_v3`**).

- Si vas a subir **solo** esa carpeta al repositorio, los pasos de Git los haces **dentro** de `convivencia_v3`.
- Si subes una carpeta **padre** que contiene `convivencia_v3`, en Railway tendrás que indicar **Root Directory** = `convivencia_v3` (lo verás más abajo).

Abre **PowerShell** o **Terminal** en esa carpeta antes de los comandos `git`.

---

## Parte 2 — Crear el repositorio en GitHub

1. Entra en [https://github.com](https://github.com) e inicia sesión.
2. Arriba a la derecha: **+** → **New repository**.
3. **Repository name:** por ejemplo `convivencia-escolar` (sin espacios).
4. Déjalo en **Public** (o Private si prefieres).
5. **No** marques “Add a README” si ya tienes archivos locales (evita conflictos).
6. Pulsa **Create repository**.

GitHub te mostrará una URL como:

`https://github.com/TU_USUARIO/convivencia-escolar.git`

Cópiala; la usarás en el siguiente paso.

---

## Parte 3 — Subir el código la primera vez (Git)

En la carpeta del proyecto (`convivencia_v3` o la que corresponda):

```powershell
git init
git add .
git commit -m "Primera versión: Convivencia Escolar"
git branch -M main
git remote add origin https://github.com/54b4freddy/convivencia-escolar.git
git push -u origin main
```

- Sustituye la URL por la que te dio GitHub.
- Si pide usuario/contraseña: en GitHub suele usarse un **Personal Access Token** como contraseña (Settings → Developer settings → Personal access tokens). La contraseña de la cuenta a veces ya no sirve para `git push`.

**Actualizar después de cambios:**

```powershell
git add .
git commit -m "Descripción breve del cambio"
git push
```

También puedes usar la pestaña **Source Control** en Cursor/VS Code para hacer *commit* y *push* con botones.

---

## Parte 4 — Railway (despliegue en la nube)

### 4.1 Cuenta y nuevo proyecto

1. Entra en [https://railway.app](https://railway.app) y crea cuenta (puedes usar “Login with GitHub”).
2. **New project** → **Deploy from GitHub repo**.
3. Autoriza a Railway a ver tus repositorios y elige el repo que acabas de crear.

### 4.2 Carpeta raíz del servicio

Si en GitHub el repo **no** es solo `convivencia_v3` sino una carpeta que la contiene:

1. En Railway, abre tu servicio → **Settings**.
2. Busca **Root Directory** y escribe: `convivencia_v3` (o la ruta correcta hasta donde está `app.py`).
3. Guarda y vuelve a desplegar si hace falta.

### 4.3 Base de datos PostgreSQL (recomendado en Railway)

En el mismo **proyecto** de Railway:

1. **+ New** → **Database** → **PostgreSQL**.
2. Cuando esté creada, entra en el plugin Postgres → pestaña **Variables**.
3. Copia el valor de **`DATABASE_URL`** (o usa **Connect** / **Reference Variable** según la interfaz actual).

En tu **servicio web** (el que ejecuta Flask):

1. **Variables** (o **Environment**).
2. Añade variable **`DATABASE_URL`** y pega el mismo valor (o enlázala desde el plugin Postgres si Railway ofrece “Variable Reference”).

Así la app usará PostgreSQL en lugar del archivo SQLite local.

### 4.4 Variables de entorno obligatorias en producción

En el servicio web, en **Variables**, configura al menos:

| Variable | Valor sugerido |
|----------|----------------|
| `APP_ENV` | `production` |
| `SECRET_KEY` | Una cadena larga y aleatoria (ver abajo) |
| `DATABASE_URL` | La que proporciona Railway Postgres (si usas Postgres) |

**Generar `SECRET_KEY` en PowerShell:**

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Copia el resultado y pégalo como valor de `SECRET_KEY` en Railway.

Opcionales:

| Variable | Uso |
|----------|-----|
| `SESSION_COOKIE_SECURE` | Con HTTPS en Railway suele ser `1` (por defecto en producción ya puede aplicarse según el código) |
| `REGISTRATION_OPEN` | `1` solo si necesitas el endpoint legado `/api/registrar-usuario`; por defecto el registro público está cerrado |

### 4.5 Dominio público (URL para el móvil)

1. En el servicio web → **Settings** → **Networking** / **Generate domain**.
2. Railway te asigna algo como `https://xxxx.up.railway.app`.
3. Esa es la dirección que abres en el **móvil** u otro dispositivo (misma WiFi o datos móviles).

### 4.6 Primera base de datos vacía

El archivo `railway.toml` incluye un **`releaseCommand`** que ejecuta `init_db()` al desplegar: crea tablas y, si la BD está vacía, datos de demostración.

Si algo falla, en los **logs** del despliegue verás el error. Asegúrate de que `DATABASE_URL` esté definida **antes** del primer arranque exitoso.

### 4.7 Healthcheck

El proyecto expone `GET /health`. En `railway.json` está configurada la ruta de comprobación de salud para que Railway sepa si la app responde.

---

## Parte 5 — Probar desde el móvil

1. Espera a que el despliegue en Railway esté en verde (**Active** / **Success**).
2. Abre el navegador del móvil y escribe la URL `https://....up.railway.app`.
3. Entra con un usuario de prueba (por ejemplo coordinador `admin` / `admin123` si cargó el seed de demostración).

**Si no carga:** revisa en Railway → **Deployments** → logs del servicio web. Errores frecuentes: falta `SECRET_KEY`, falta `APP_ENV=production`, o `DATABASE_URL` mal enlazada.

---

## Parte 6 — Archivos que ya tiene el proyecto para Railway

- `requirements.txt` — dependencias Python  
- `Procfile` — comando para Gunicorn  
- `railway.json` — arranque y healthcheck  
- `railway.toml` — `releaseCommand` para migrar/inicializar BD  

No necesitas inventar estos desde cero; solo configurar variables en el panel de Railway.

---

## Resumen rápido

1. Crear repo en GitHub.  
2. `git init` → `add` → `commit` → `remote` → `push`.  
3. Railway: proyecto desde GitHub, Postgres opcional pero recomendado.  
4. Variables: `APP_ENV=production`, `SECRET_KEY=...`, `DATABASE_URL=...` (si hay Postgres).  
5. Generar dominio y abrir la URL en el móvil.

Si más adelante quieres un dominio propio (`www.tucolegio.edu.co`), se hace con DNS apuntando a Railway; es un paso extra cuando lo necesites.

---

## Usuarios de prueba (datos demo)

Solo existen tras `init_db()` con base vacía. Cámbialos en producción real.

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| superadmin | super123 | Superadmin |
| admin | admin123 | Coordinador |
| director1 | dir123 | Director (6A) |
| orientador1 | ori123 | Orientador |
| docente1 | doc123 | Docente |

Los acudientes de demo usan el **documento** como usuario y contraseña inicial (según datos sembrados en `ce_db`).
