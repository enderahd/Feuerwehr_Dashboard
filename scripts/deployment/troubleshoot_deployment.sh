#!/bin/bash
# Troubleshooting Script für Feuerwehr Dashboard Deployment

echo "🔧 Feuerwehr Dashboard - Troubleshooting"
echo "========================================"

PROJECT_NAME="feuerwehr_dashboard"
INSTALL_DIR="/opt/${PROJECT_NAME}"
SERVICE_NAME="feuerwehr-dashboard"

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo "1. 📋 System-Status überprüfen"
echo "================================"

# Python Service Status
systemctl is-active --quiet $SERVICE_NAME
print_status $? "Python Service ($SERVICE_NAME)"

# Nginx Status
systemctl is-active --quiet nginx
print_status $? "Nginx Service"

# Ports prüfen
echo ""
echo "2. 🌐 Port-Status überprüfen"
echo "============================="

# Port 5001 (Flask App)
if netstat -tuln | grep ":5001" > /dev/null; then
    print_status 0 "Port 5001 (Flask App intern)"
else
    print_status 1 "Port 5001 (Flask App intern) - Service läuft nicht"
fi

# Port 80 (Frontend)
if netstat -tuln | grep ":80" > /dev/null; then
    print_status 0 "Port 80 (Frontend via Nginx)"
else
    print_status 1 "Port 80 (Frontend via Nginx) - Nginx Problem"
fi

# Port 5000 (Backend)
if netstat -tuln | grep ":5000" > /dev/null; then
    print_status 0 "Port 5000 (Backend via Nginx)"
else
    print_status 1 "Port 5000 (Backend via Nginx) - Nginx Problem"
fi

echo ""
echo "3. 📁 Dateien & Verzeichnisse prüfen"
echo "===================================="

# Wichtige Dateien prüfen
files_to_check=(
    "$INSTALL_DIR/API_backend.py"
    "$INSTALL_DIR/.env.production"
    "$INSTALL_DIR/config/feuerwehr-dashboard.service"
    "/etc/nginx/sites-available/$PROJECT_NAME"
    "/etc/nginx/sites-enabled/$PROJECT_NAME"
    "/etc/systemd/system/$SERVICE_NAME.service"
)

for file in "${files_to_check[@]}"; do
    if [ -f "$file" ]; then
        print_status 0 "Datei existiert: $file"
    else
        print_status 1 "Datei fehlt: $file"
    fi
done

# Verzeichnisse prüfen
dirs_to_check=(
    "$INSTALL_DIR"
    "$INSTALL_DIR/static"
    "$INSTALL_DIR/templates"
    "$INSTALL_DIR/pdfs"
    "$INSTALL_DIR/output"
    "/var/log/$PROJECT_NAME"
)

for dir in "${dirs_to_check[@]}"; do
    if [ -d "$dir" ]; then
        print_status 0 "Verzeichnis existiert: $dir"
    else
        print_status 1 "Verzeichnis fehlt: $dir"
    fi
done

echo ""
echo "4. 🔧 Konfiguration prüfen"
echo "=========================="

# Nginx Konfiguration testen
nginx -t > /dev/null 2>&1
print_status $? "Nginx Konfiguration"

# Python Umgebung prüfen
if [ -f "$INSTALL_DIR/venv/bin/python" ]; then
    print_status 0 "Python Virtual Environment"
else
    print_status 1 "Python Virtual Environment fehlt"
fi

# .env.production prüfen
if [ -f "$INSTALL_DIR/.env.production" ]; then
    if grep -q "your_api_key_here" "$INSTALL_DIR/.env.production"; then
        print_warning "OpenWeather API-Key noch nicht gesetzt in .env.production"
    else
        print_status 0 "OpenWeather API-Key ist gesetzt"
    fi
else
    print_status 1 ".env.production Datei fehlt"
fi

echo ""
echo "5. 📋 Log-Analyse"
echo "================="

echo "Letzte Service-Logs:"
echo "-------------------"
journalctl -u $SERVICE_NAME -n 5 --no-pager

echo ""
echo "Nginx Error Log:"
echo "---------------"
if [ -f "/var/log/nginx/error.log" ]; then
    tail -5 /var/log/nginx/error.log
else
    echo "Nginx Error Log nicht gefunden"
fi

echo ""
echo "🛠️  HÄUFIGE LÖSUNGEN"
echo "==================="
echo ""
echo "Problem: Service startet nicht"
echo "Lösung: sudo systemctl restart $SERVICE_NAME"
echo ""
echo "Problem: Nginx Fehler"
echo "Lösung: sudo nginx -t && sudo systemctl restart nginx"
echo ""
echo "Problem: Python Dependencies"
echo "Lösung: cd $INSTALL_DIR && source venv/bin/activate && pip install -r requirements.txt"
echo ""
echo "Problem: Berechtigungen"
echo "Lösung: sudo chown -R www-data:www-data $INSTALL_DIR"
echo ""
echo "Problem: API-Key fehlt"
echo "Lösung: sudo nano $INSTALL_DIR/.env.production"
echo ""
echo "🔄 Service neu starten:"
echo "sudo systemctl daemon-reload"
echo "sudo systemctl restart $SERVICE_NAME"
echo "sudo systemctl restart nginx"
echo ""
echo "📊 Live-Monitoring:"
echo "sudo journalctl -u $SERVICE_NAME -f"
