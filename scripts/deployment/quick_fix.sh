#!/bin/bash
# Quick-Fix Script für häufige Deployment-Probleme

echo "🚒 Feuerwehr Dashboard - Quick Fix"
echo "=================================="

# Variablen
PROJECT_NAME="feuerwehr_dashboard"
SERVICE_NAME="feuerwehr-dashboard"
INSTALL_DIR="/opt/${PROJECT_NAME}"
USER="www-data"
GROUP="www-data"

echo "🔧 Führe automatische Reparaturen durch..."
echo ""

# 1. Service stoppen
echo "1️⃣ Stoppe Service..."
sudo systemctl stop "$SERVICE_NAME" 2>/dev/null || echo "Service war bereits gestoppt"

# 2. Berechtigungen korrigieren
echo "2️⃣ Korrigiere Berechtigungen..."
if [ -d "$INSTALL_DIR" ]; then
    sudo chown -R $USER:$GROUP "$INSTALL_DIR"
    sudo chmod -R 755 "$INSTALL_DIR"
    sudo chmod 644 "$INSTALL_DIR"/*.py 2>/dev/null || true
    sudo chmod +x "$INSTALL_DIR"/*.sh 2>/dev/null || true
    echo "✅ Berechtigungen korrigiert"
else
    echo "❌ Installationsverzeichnis nicht gefunden: $INSTALL_DIR"
fi

# 3. Log-Verzeichnis erstellen
echo "3️⃣ Erstelle Log-Verzeichnis..."
sudo mkdir -p "/var/log/$PROJECT_NAME"
sudo chown -R $USER:$GROUP "/var/log/$PROJECT_NAME"
sudo chmod 755 "/var/log/$PROJECT_NAME"
echo "✅ Log-Verzeichnis erstellt"

# 4. Virtual Environment reparieren
echo "4️⃣ Prüfe Virtual Environment..."
if [ -d "$INSTALL_DIR/venv" ]; then
    echo "✅ Virtual Environment existiert"
    
    # Pakete installieren
    echo "Installiere/Update Python-Pakete..."
    cd "$INSTALL_DIR"
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
    echo "✅ Python-Pakete aktualisiert"
else
    echo "🔄 Erstelle Virtual Environment neu..."
    cd "$INSTALL_DIR"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    deactivate
    sudo chown -R $USER:$GROUP venv
    echo "✅ Virtual Environment neu erstellt"
fi

# 5. Service-Datei reparieren/erstellen
echo "5️⃣ Prüfe Service-Datei..."
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
if [ ! -f "$SERVICE_FILE" ]; then
    echo "🔄 Erstelle Service-Datei..."
    cat > /tmp/service_file << EOF
[Unit]
Description=Feuerwehr Dashboard Flask Application
After=network.target

[Service]
Type=simple
User=$USER
Group=$GROUP
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
Environment=FLASK_ENV=production
EnvironmentFile=$INSTALL_DIR/.env.production
ExecStart=$INSTALL_DIR/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 --access-logfile /var/log/$PROJECT_NAME/access.log --error-logfile /var/log/$PROJECT_NAME/error.log wsgi:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$INSTALL_DIR /var/log/$PROJECT_NAME

[Install]
WantedBy=multi-user.target
EOF
    sudo mv /tmp/service_file "$SERVICE_FILE"
    echo "✅ Service-Datei erstellt"
else
    echo "✅ Service-Datei existiert bereits"
fi

# 6. Systemd reload
echo "6️⃣ Lade Systemd-Konfiguration neu..."
sudo systemctl daemon-reload
echo "✅ Systemd-Konfiguration neu geladen"

# 7. Service aktivieren und starten
echo "7️⃣ Aktiviere und starte Service..."
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl start "$SERVICE_NAME"

# 8. Warte und prüfe Status
echo "8️⃣ Prüfe Service-Status..."
sleep 3

if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "✅ Service läuft erfolgreich!"
    echo ""
    echo "📊 Service-Information:"
    systemctl status "$SERVICE_NAME" --no-pager -l
    echo ""
    echo "🌐 Dashboard sollte erreichbar sein unter:"
    echo "http://$(hostname -I | awk '{print $1}'):5000"
    echo ""
    echo "📋 Nützliche Befehle:"
    echo "- Status: sudo systemctl status $SERVICE_NAME"
    echo "- Logs: sudo journalctl -u $SERVICE_NAME -f"
    echo "- Neustart: sudo systemctl restart $SERVICE_NAME"
    echo "- App-Logs: sudo tail -f /var/log/$PROJECT_NAME/app.log"
else
    echo "❌ Service konnte nicht gestartet werden!"
    echo ""
    echo "🔍 Debug-Informationen:"
    systemctl status "$SERVICE_NAME" --no-pager -l
    echo ""
    echo "📋 Letzte Logs:"
    journalctl -u "$SERVICE_NAME" --no-pager -l --lines=10
    echo ""
    echo "🛠️ Manueller Start zum Debugging:"
    echo "cd $INSTALL_DIR"
    echo "source venv/bin/activate"
    echo "python API_backend.py"
fi
