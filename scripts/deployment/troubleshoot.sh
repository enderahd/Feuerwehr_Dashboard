#!/bin/bash
# Troubleshooting Script für Feuerwehr Dashboard

echo "🚒 Feuerwehr Dashboard - Troubleshooting"
echo "========================================"

# Variablen
PROJECT_NAME="feuerwehr_dashboard"
SERVICE_NAME="feuerwehr-dashboard"
INSTALL_DIR="/opt/${PROJECT_NAME}"

echo "📋 Überprüfe System-Status..."
echo ""

# 1. Service-Status
echo "1️⃣ Service-Status:"
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "✅ Service läuft"
    systemctl status "$SERVICE_NAME" --no-pager -l
else
    echo "❌ Service läuft nicht"
    echo "Status-Details:"
    systemctl status "$SERVICE_NAME" --no-pager -l
fi
echo ""

# 2. Service-Datei prüfen
echo "2️⃣ Service-Datei:"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
if [ -f "$SERVICE_FILE" ]; then
    echo "✅ Service-Datei existiert: $SERVICE_FILE"
    echo "Inhalt:"
    cat "$SERVICE_FILE"
else
    echo "❌ Service-Datei fehlt: $SERVICE_FILE"
fi
echo ""

# 3. Installationsverzeichnis prüfen
echo "3️⃣ Installationsverzeichnis:"
if [ -d "$INSTALL_DIR" ]; then
    echo "✅ Verzeichnis existiert: $INSTALL_DIR"
    echo "Inhalt:"
    ls -la "$INSTALL_DIR"
    echo ""
    echo "Python-Dateien:"
    ls -la "$INSTALL_DIR"/*.py 2>/dev/null || echo "Keine Python-Dateien gefunden"
else
    echo "❌ Verzeichnis fehlt: $INSTALL_DIR"
fi
echo ""

# 4. Virtual Environment prüfen
echo "4️⃣ Virtual Environment:"
VENV_DIR="$INSTALL_DIR/venv"
if [ -d "$VENV_DIR" ]; then
    echo "✅ Virtual Environment existiert: $VENV_DIR"
    echo "Python-Version:"
    "$VENV_DIR/bin/python" --version 2>/dev/null || echo "Python nicht verfügbar"
    echo "Installierte Pakete:"
    "$VENV_DIR/bin/pip" list 2>/dev/null | head -10 || echo "pip nicht verfügbar"
else
    echo "❌ Virtual Environment fehlt: $VENV_DIR"
fi
echo ""

# 5. Konfiguration prüfen
echo "5️⃣ Konfiguration:"
CONFIG_FILE="$INSTALL_DIR/.env.production"
if [ -f "$CONFIG_FILE" ]; then
    echo "✅ Konfigurationsdatei existiert: $CONFIG_FILE"
    echo "Inhalt (ohne Passwörter):"
    cat "$CONFIG_FILE" | grep -v "PASSWORD\|SECRET_KEY\|API_KEY" || echo "Datei leer oder nicht lesbar"
else
    echo "❌ Konfigurationsdatei fehlt: $CONFIG_FILE"
fi
echo ""

# 6. Logs prüfen
echo "6️⃣ Service-Logs (letzte 20 Zeilen):"
if journalctl -u "$SERVICE_NAME" --no-pager -l --lines=20 2>/dev/null; then
    echo "✅ Logs abgerufen"
else
    echo "❌ Keine Logs verfügbar oder Service existiert nicht"
fi
echo ""

# 7. Netzwerk prüfen
echo "7️⃣ Netzwerk-Status:"
echo "Port 5000:"
if netstat -tuln | grep -q ":5000 "; then
    echo "✅ Port 5000 ist in Verwendung"
    netstat -tuln | grep ":5000 "
else
    echo "❌ Port 5000 ist nicht in Verwendung"
fi
echo ""

# 8. Berechtigungen prüfen
echo "8️⃣ Berechtigungen:"
if [ -d "$INSTALL_DIR" ]; then
    echo "Verzeichnis-Berechtigungen:"
    ls -ld "$INSTALL_DIR"
    echo "Datei-Berechtigungen (Auswahl):"
    ls -la "$INSTALL_DIR"/*.py 2>/dev/null | head -5 || echo "Keine Python-Dateien gefunden"
fi
echo ""

# 9. Speicherplatz prüfen
echo "9️⃣ Speicherplatz:"
df -h | grep -E "(Filesystem|/$)"
echo ""

# 10. Prozesse prüfen
echo "🔟 Python-Prozesse:"
ps aux | grep -E "(python|gunicorn)" | grep -v grep || echo "Keine Python/Gunicorn-Prozesse gefunden"
echo ""

echo "🎯 Mögliche Lösungsansätze:"
echo ""
echo "📥 Falls Service nicht läuft:"
echo "sudo systemctl start $SERVICE_NAME"
echo "sudo systemctl enable $SERVICE_NAME"
echo ""
echo "🔄 Falls Service-Datei fehlt:"
echo "sudo systemctl daemon-reload"
echo ""
echo "🔧 Manual Start zum Debugging:"
echo "cd $INSTALL_DIR"
echo "source venv/bin/activate"
echo "python API_backend.py"
echo ""
echo "📋 Service-Logs live anzeigen:"
echo "sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "🗂️ App-Logs anzeigen:"
echo "sudo tail -f /var/log/$PROJECT_NAME/app.log"
