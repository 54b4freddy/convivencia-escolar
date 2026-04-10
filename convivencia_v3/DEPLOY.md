# 🚀 Guía de despliegue en servidor (VPS propio)

> **¿Prefieres Railway y GitHub sin servidor Linux?** Usa **[GUIA_GITHUB_Y_RAILWAY.md](./GUIA_GITHUB_Y_RAILWAY.md)**.

## Requisitos

- Servidor Ubuntu 22.04 (VPS desde $6 USD/mes en Hostinger o DigitalOcean)
- Python 3.10+
- Nginx

## Pasos

```bash
# 1. Conectarse al servidor
ssh root@IP_DEL_SERVIDOR

# 2. Instalar dependencias del sistema
apt update && apt upgrade -y
apt install python3 python3-pip python3-venv nginx git -y

# 3. Clonar el repositorio
cd /var/www
git clone https://github.com/TU_USUARIO/convivencia-escolar.git convivencia
cd convivencia

# 4. Entorno virtual
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. Configurar variables
cp .env.example .env
nano .env   # Cambiar SECRET_KEY

# 6. Carpetas necesarias
mkdir -p logs static/uploads

# 7. Inicializar base de datos
python3 -c "from app import init_db; init_db()"

# 8. Servicio systemd
cp convivencia.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable convivencia
systemctl start convivencia

# 9. Nginx
cp nginx.conf /etc/nginx/sites-available/convivencia
ln -s /etc/nginx/sites-available/convivencia /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx
```

## Actualizar después de cambios (git pull)

```bash
cd /var/www/convivencia
git pull
systemctl restart convivencia
```
