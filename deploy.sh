#!/bin/bash
# Deployment Script für Feuerwehr Dashboard auf Raspberry Pi

set -e

echo "🚒 Feuerwehr Dashboard - Raspberry Pi Deployment"
echo "================================================="

# Variablen
PROJECT_NAME="feuerwehr_dashboard"
INSTALL_DIR="/opt/${PROJECT_NAME}"
SERVICE_NAME="feuerwehr-dashboard"
USER="www-data"
GROUP="www-data"

# Root-Rechte prüfen
if [[ $EUID -ne 0 ]]; then
   echo "❌ Dieses Script muss als root ausgeführt werden (sudo)"
   exit 1
fi

# System aktualisieren
echo "📦 System wird aktualisiert..."
apt update && apt upgrade -y

# Python 3 und Abhängigkeiten installieren
echo "🐍 Python 3 und Abhängigkeiten werden installiert..."
apt install -y python3 python3-pip python3-venv nginx supervisor

# Benutzer und Gruppe erstellen (falls nicht vorhanden)
if ! id "$USER" &>/dev/null; then
    echo "👤 Benutzer $USER wird erstellt..."
    useradd --system --shell /bin/false --home $INSTALL_DIR $USER
fi

# Projektverzeichnis erstellen
echo "📁 Projektverzeichnis wird erstellt..."
mkdir -p $INSTALL_DIR
mkdir -p /var/log/$PROJECT_NAME
mkdir -p $INSTALL_DIR/pdfs
mkdir -p $INSTALL_DIR/output

# Dateien kopieren
echo "📄 Projektdateien werden kopiert..."
if [ -d "$(pwd)" ]; then
    cp -r . $INSTALL_DIR/
else
    echo "❌ Projektverzeichnis nicht gefunden. Bitte vom Projektverzeichnis ausführen."
    exit 1
fi

# Virtual Environment erstellen
echo "🔧 Python Virtual Environment wird erstellt..."
cd $INSTALL_DIR
python3 -m venv venv
source venv/bin/activate

# Python-Pakete installieren
echo "📚 Python-Pakete werden installiert..."
pip install --upgrade pip
pip install -r requirements.txt

# Berechtigungen setzen
echo "🔐 Berechtigungen werden gesetzt..."
chown -R $USER:$GROUP $INSTALL_DIR
chown -R $USER:$GROUP /var/log/$PROJECT_NAME
chmod -R 755 $INSTALL_DIR
chmod -R 644 $INSTALL_DIR/*.py
chmod +x $INSTALL_DIR/deploy.sh

# Produktions-Umgebungsdatei erstellen (falls nicht vorhanden)
if [ ! -f "$INSTALL_DIR/.env.production" ]; then
    echo "⚙️ Produktions-Umgebungsdatei wird erstellt..."
    cat > $INSTALL_DIR/.env.production << EOF
# Produktionsumgebung für Raspberry Pi
FLASK_ENV=production
FLASK_DEBUG=False
FLASK_SECRET_KEY=$(openssl rand -hex 32)

# Feuerwehr Dashboard Konfiguration
PASSWORD=admin123
zielverzeichnis=$INSTALL_DIR

# OpenWeather API Konfiguration (BITTE ANPASSEN!)
OPENWEATHER_API_KEY=your_api_key_here

# Server Konfiguration
HOST=0.0.0.0
PORT=5000

# Logging Konfiguration
LOG_LEVEL=INFO
LOG_FILE=/var/log/$PROJECT_NAME/app.log
MAX_LOG_SIZE=10485760
LOG_BACKUP_COUNT=5

# Security
CSRF_ENABLED=True
SESSION_TIMEOUT=3600

# Rate Limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_DEFAULT=100 per hour
RATE_LIMIT_LOGIN=5 per minute
EOF
    echo "⚠️  WICHTIG: Bitte bearbeiten Sie $INSTALL_DIR/.env.production und setzen Sie Ihr OpenWeather API-Key!"
fi

# Systemd Service installieren
echo "⚙️ Systemd Service wird installiert..."
cp $INSTALL_DIR/feuerwehr-dashboard.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable $SERVICE_NAME

# Nginx Konfiguration
echo "🌐 Nginx wird konfiguriert..."
cat > /etc/nginx/sites-available/$PROJECT_NAME << EOF
server {
    listen 80;
    server_name _;

    client_max_body_size 16M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /static {
        alias $INSTALL_DIR/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Nginx Site aktivieren
ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

# Firewall konfigurieren (falls ufw installiert ist)
if command -v ufw &> /dev/null; then
    echo "🔥 Firewall wird konfiguriert..."
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
fi

# Service starten
echo "🚀 Service wird gestartet..."
systemctl start $SERVICE_NAME
systemctl status $SERVICE_NAME

# Startup-Test
echo "🧪 Service-Test..."
sleep 5
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ Service läuft erfolgreich!"
    echo ""
    echo "🎉 Deployment erfolgreich abgeschlossen!"
    echo ""
    echo "📋 Nächste Schritte:"
    echo "1. Bearbeiten Sie $INSTALL_DIR/.env.production"
    echo "2. Setzen Sie Ihren OpenWeather API-Key"
    echo "3. Ändern Sie das Standard-Passwort"
    echo "4. Starten Sie den Service neu: sudo systemctl restart $SERVICE_NAME"
    echo ""
    echo "🌐 Das Dashboard ist erreichbar unter: http://$(hostname -I | awk '{print $1}')"
    echo ""
    echo "📊 Monitoring:"
    echo "- Status: sudo systemctl status $SERVICE_NAME"
    echo "- Logs: sudo journalctl -u $SERVICE_NAME -f"
    echo "- App Logs: sudo tail -f /var/log/$PROJECT_NAME/app.log"
else
    echo "❌ Service konnte nicht gestartet werden!"
    echo "Logs prüfen: sudo journalctl -u $SERVICE_NAME"
    exit 1
fi
