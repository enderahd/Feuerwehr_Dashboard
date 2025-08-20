#!/bin/bash
# Kompletter Fix und Test für alle bekannten Probleme

echo "🛠️  KOMPLETTER FIX & TEST"
echo "========================="

PROJECT_NAME="feuerwehr_dashboard"
INSTALL_DIR="/opt/${PROJECT_NAME}"
SERVICE_NAME="feuerwehr-dashboard"
LOG_DIR="/var/log/${PROJECT_NAME}"

# Farben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Root-Rechte prüfen
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ Dieses Script muss als root ausgeführt werden (sudo)${NC}"
   exit 1
fi

# Funktion für Status-Ausgabe
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

echo -e "${BLUE}🔄 Phase 1: Services stoppen${NC}"
systemctl stop $SERVICE_NAME 2>/dev/null || echo "Service war bereits gestoppt"
systemctl stop nginx 2>/dev/null || echo "Nginx war bereits gestoppt"

echo -e "${BLUE}📁 Phase 2: Verzeichnisse sicherstellen${NC}"
mkdir -p $INSTALL_DIR/{pdfs,output,static/{css,js,images},templates,config}
mkdir -p $LOG_DIR
print_status $? "Verzeichnisse erstellt"

echo -e "${BLUE}🔧 Phase 3: Berechtigungen korrigieren${NC}"
chown -R www-data:www-data $INSTALL_DIR $LOG_DIR
chmod -R 755 $INSTALL_DIR
chmod 644 $INSTALL_DIR/*.py 2>/dev/null || true
print_status $? "Berechtigungen gesetzt"

echo -e "${BLUE}📝 Phase 4: Nginx-Konfiguration erstellen${NC}"
cat > /etc/nginx/sites-available/$PROJECT_NAME << 'NGINX_EOF'
# Frontend Server (Port 80) - Öffentliches Dashboard
server {
    listen 80;
    server_name _;
    
    root /opt/feuerwehr_dashboard/static;
    index index.html;
    
    # Frontend Route
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API für Frontend
    location /api/public/ {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static Assets
    location /static/ {
        alias /opt/feuerwehr_dashboard/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}

# Backend Server (Port 5000) - Admin Interface
server {
    listen 5000;
    server_name _;
    client_max_body_size 16M;
    
    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
NGINX_EOF

# Site aktivieren
ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Nginx testen
nginx -t
print_status $? "Nginx-Konfiguration"

echo -e "${BLUE}⚙️ Phase 5: Systemd Service erstellen${NC}"
cat > /etc/systemd/system/$SERVICE_NAME.service << 'SERVICE_EOF'
[Unit]
Description=Feuerwehr Dashboard Flask Application
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/feuerwehr_dashboard
Environment=PATH=/opt/feuerwehr_dashboard/venv/bin
Environment=FLASK_ENV=production
EnvironmentFile=/opt/feuerwehr_dashboard/.env.production
ExecStart=/opt/feuerwehr_dashboard/venv/bin/gunicorn --bind 0.0.0.0:5001 --workers 2 --timeout 120 --access-logfile /var/log/feuerwehr_dashboard/access.log --error-logfile /var/log/feuerwehr_dashboard/error.log wsgi:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF

systemctl daemon-reload
systemctl enable $SERVICE_NAME
print_status $? "Service konfiguriert"

echo -e "${BLUE}🔑 Phase 6: .env.production überprüfen${NC}"
if [ -f "$INSTALL_DIR/.env.production" ]; then
    # CSRF sicherstellen dass es auf False steht
    if grep -q "CSRF_ENABLED" "$INSTALL_DIR/.env.production"; then
        sed -i 's/CSRF_ENABLED=.*/CSRF_ENABLED=False/' "$INSTALL_DIR/.env.production"
    else
        echo "CSRF_ENABLED=False" >> "$INSTALL_DIR/.env.production"
    fi
    print_status 0 ".env.production angepasst"
else
    echo -e "${YELLOW}⚠️ .env.production nicht gefunden - erstelle Basis-Konfiguration${NC}"
    cat > "$INSTALL_DIR/.env.production" << 'ENV_EOF'
FLASK_ENV=production
FLASK_DEBUG=False
FLASK_SECRET_KEY=generated_secret_key_change_me
PASSWORD=test1234
zielverzeichnis=/opt/feuerwehr_dashboard
OPENWEATHER_API_KEY=your_api_key_here
HOST=0.0.0.0
PORT=5001
CSRF_ENABLED=False
RATE_LIMIT_ENABLED=True
ENV_EOF
    print_status 0 ".env.production erstellt"
fi

echo -e "${BLUE}🐍 Phase 7: Python-Umgebung prüfen${NC}"
if [ -d "$INSTALL_DIR/venv" ]; then
    print_status 0 "Virtual Environment vorhanden"
else
    echo "Erstelle Virtual Environment..."
    cd $INSTALL_DIR
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    print_status $? "Virtual Environment erstellt"
fi

echo -e "${BLUE}🚀 Phase 8: Services starten${NC}"
systemctl start nginx
nginx_status=$?
print_status $nginx_status "Nginx gestartet"

systemctl start $SERVICE_NAME
service_status=$?
print_status $service_status "Backend gestartet"

echo -e "${BLUE}⏳ Phase 9: Warten auf Service-Bereitschaft${NC}"
sleep 5

# Port-Tests
echo -e "${BLUE}🌐 Phase 10: Port-Tests${NC}"
if netstat -tuln | grep ":80" > /dev/null; then
    print_status 0 "Port 80 (Frontend) aktiv"
else
    print_status 1 "Port 80 (Frontend) nicht erreichbar"
fi

if netstat -tuln | grep ":5000" > /dev/null; then
    print_status 0 "Port 5000 (Backend) aktiv"
else
    print_status 1 "Port 5000 (Backend) nicht erreichbar"
fi

if netstat -tuln | grep ":5001" > /dev/null; then
    print_status 0 "Port 5001 (Flask intern) aktiv"
else
    print_status 1 "Port 5001 (Flask intern) nicht erreichbar"
fi

# Service-Status
echo -e "${BLUE}📊 Phase 11: Service-Status${NC}"
nginx_active=$(systemctl is-active nginx)
service_active=$(systemctl is-active $SERVICE_NAME)

if [ "$nginx_active" = "active" ]; then
    print_status 0 "Nginx läuft"
else
    print_status 1 "Nginx Problem"
fi

if [ "$service_active" = "active" ]; then
    print_status 0 "Backend läuft"
else
    print_status 1 "Backend Problem"
fi

echo ""
echo -e "${GREEN}🎉 FIX ABGESCHLOSSEN!${NC}"
echo ""

if [ "$nginx_active" = "active" ] && [ "$service_active" = "active" ]; then
    echo -e "${GREEN}✅ ALLES FUNKTIONAL!${NC}"
    echo ""
    echo "🌐 Dashboard-Zugriff:"
    echo "   Frontend: http://$(hostname -I | awk '{print $1}')/"
    echo "   Backend:  http://$(hostname -I | awk '{print $1}'):5000/"
    echo ""
    echo "🔑 Backend-Login:"
    CURRENT_PASSWORD=$(grep "^PASSWORD=" "$INSTALL_DIR/.env.production" | cut -d'=' -f2)
    echo "   Passwort: $CURRENT_PASSWORD"
else
    echo -e "${RED}❌ PROBLEME ERKANNT${NC}"
    echo ""
    echo "🔍 Debug-Befehle:"
    echo "   sudo journalctl -u $SERVICE_NAME -n 20"
    echo "   sudo journalctl -u nginx -n 20"
    echo "   sudo tail -f $LOG_DIR/app.log"
    echo "   sudo nginx -t"
fi

echo ""
echo "📋 Nützliche Befehle:"
echo "   Service neu starten: sudo systemctl restart $SERVICE_NAME"
echo "   Nginx neu starten:   sudo systemctl restart nginx"
echo "   Logs verfolgen:      sudo journalctl -u $SERVICE_NAME -f"
echo "   Konfiguration:       sudo nano $INSTALL_DIR/.env.production"
