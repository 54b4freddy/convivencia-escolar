# 🏫 Convivencia Escolar (v7)

Sistema web de gestión disciplinar escolar. Multi-institución, multi-rol.

## 📱 ¿Primera vez con GitHub y Railway?

Lee la guía paso a paso (móvil, URL pública, variables de entorno):

**[→ GUIA_GITHUB_Y_RAILWAY.md](./GUIA_GITHUB_Y_RAILWAY.md)**

---

## Roles del sistema

| Rol | Qué puede hacer |
|-----|----------------|
| **Superadmin** | Gestiona todos los colegios, usuarios y datos globales |
| **Coordinador** | Gestiona su colegio: usuarios, estudiantes, faltas, reportes |
| **Director de grupo** | Ve y anota las faltas de su curso |
| **Orientador** | Consulta todas las faltas y agrega seguimiento psicosocial |
| **Docente** | Registra y consulta sus propias faltas |

## Usuarios de prueba

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| superadmin | super123 | Superadmin |
| admin | admin123 | Coordinador |
| director1 | dir123 | Director (6A) |
| orientador1 | ori123 | Orientador |
| docente1 | doc123 | Docente |

---

## ⚙️ Correr en VS Code (desarrollo local)

### 1. Clonar el repositorio

```bash
git clone https://github.com/TU_USUARIO/convivencia-escolar.git
cd convivencia-escolar
```

### 2. Crear entorno virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
# Copiar la plantilla
cp .env.example .env

# Editar .env y cambiar SECRET_KEY
```

### 5. Inicializar la base de datos

```bash
python -c "from ce_db import init_db; init_db(); print('Base de datos lista')"
```

(También funciona `from app import init_db` porque `app.py` importa `init_db` desde `ce_db`.)

### 6. Ejecutar el servidor de desarrollo

```bash
python app.py
```

Abrir en el navegador: **http://localhost:5000**

**Probar en el móvil en la misma WiFi (solo desarrollo):** en la PC ejecuta el servidor (como arriba); averigua la IP local de la PC (por ejemplo `192.168.1.10`) y en el móvil abre `http://192.168.1.10:5000` (el firewall de Windows debe permitir el puerto 5000). Para uso fuera de casa, usa el despliegue en **Railway** (ver guía).

### Extensiones recomendadas para VS Code

Instala estas extensiones para trabajar mejor con el proyecto:

- **Python** (Microsoft) — soporte para Python
- **Flask Snippets** — atajos para Flask
- **Pylance** — autocompletado inteligente
- **SQLite Viewer** — ver la base de datos visualmente
- **GitLens** — historial de cambios en Git

---

## 🔄 Flujo de trabajo con GitHub

### Primera vez (subir el proyecto)

```bash
# Dentro de la carpeta del proyecto:
git init
git add .
git commit -m "feat: versión inicial convivencia escolar v3"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/convivencia-escolar.git
git push -u origin main
```

### Cada vez que Claude haga una mejora

Después de recibir archivos actualizados de Claude, en VS Code abre la terminal y ejecuta:

```bash
git add .
git commit -m "feat: descripción del cambio que se hizo"
git push
```

### Ver el estado de cambios en VS Code

- En la barra lateral izquierda haz clic en el ícono de **Source Control** (rama de árbol)
- Ahí verás todos los archivos modificados
- Puedes hacer commit y push directamente desde la interfaz gráfica sin usar la terminal

---

## 🚀 Despliegue en la nube (Railway) o VPS

- **Railway + GitHub (recomendado para principiantes):** [GUIA_GITHUB_Y_RAILWAY.md](./GUIA_GITHUB_Y_RAILWAY.md)
- **Servidor propio (Ubuntu, Nginx):** [DEPLOY.md](./DEPLOY.md)

---

## 📁 Estructura del proyecto

```
convivencia_v3/
├── app.py                  ← Servidor Flask (rutas y sesión)
├── ce_db.py, ce_gestion.py, ce_queries.py, …  ← Lógica de datos y reglas
├── requirements.txt
├── .env.example
├── .gitignore
├── railway.json / railway.toml  ← Config despliegue Railway
├── Procfile
├── GUIA_GITHUB_Y_RAILWAY.md    ← Subir a GitHub y desplegar en Railway
├── DEPLOY.md                   ← VPS + Nginx
├── gunicorn.conf.py            ← (opcional) producción con Gunicorn
├── nginx.conf
├── convivencia.service
├── templates/
│   ├── login.html          ← Pantalla de acceso
│   └── dashboard.html      ← Panel principal (toda la UI)
├── static/
│   └── uploads/            ← Evidencias subidas (no se sube a GitHub)
└── logs/                   ← Logs del servidor (no se sube a GitHub)
```

---

## 🛠️ Agregar funciones con Claude

El flujo recomendado es:

1. Pídele a Claude la mejora que quieres
2. Claude entrega los archivos actualizados
3. Reemplaza los archivos en tu carpeta local
4. En VS Code: `git add . → commit → push`
5. Si tienes servidor: `ssh servidor` → `git pull` → `systemctl restart convivencia`

---

## 📦 Versiones

| Versión | Cambios |
|---------|---------|
| v1 | Migración desde Google Apps Script |
| v2 | Roles, módulos, protocolos |
| v3 | Superadmin, Orientador, multi-colegio, timeline de proceso, reportes avanzados |
| v7 | Módulos extraídos, citas acudiente, estados de gestión, conductas de riesgo, etc. |
