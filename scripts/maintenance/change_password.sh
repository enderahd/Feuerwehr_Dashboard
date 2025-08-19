#!/bin/bash
# Script zum Ändern des Passworts in der Produktionsumgebung

echo "🔐 Feuerwehr Dashboard - Passwort ändern"
echo "======================================="

# Variablen
PROJECT_NAME="feuerwehr_dashboard"
SERVICE_NAME="feuerwehr-dashboard"
INSTALL_DIR="/opt/${PROJECT_NAME}"
CONFIG_FILE="$INSTALL_DIR/.env.production"

# Prüfe ob Config-Datei existiert
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Konfigurationsdatei nicht gefunden: $CONFIG_FILE"
    exit 1
fi

echo "📋 Aktuelle Konfiguration:"
echo "=========================="
cat "$CONFIG_FILE" | grep -v "SECRET_KEY\|API_KEY" | head -10

echo ""
echo "🔍 Aktuelles Passwort:"
CURRENT_PASSWORD=$(grep "^PASSWORD=" "$CONFIG_FILE" | cut -d'=' -f2)
echo "PASSWORD=$CURRENT_PASSWORD"

echo ""
echo "Möchten Sie das Passwort ändern? (j/n)"
read -p "> " CHANGE_PASSWORD

if [ "$CHANGE_PASSWORD" = "j" ] || [ "$CHANGE_PASSWORD" = "J" ] || [ "$CHANGE_PASSWORD" = "yes" ] || [ "$CHANGE_PASSWORD" = "y" ]; then
    echo ""
    echo "Geben Sie das neue Passwort ein:"
    read -p "Neues Passwort: " NEW_PASSWORD
    
    if [ -z "$NEW_PASSWORD" ]; then
        echo "❌ Passwort darf nicht leer sein!"
        exit 1
    fi
    
    # Backup erstellen
    echo "💾 Erstelle Backup..."
    sudo cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Passwort ändern
    echo "🔄 Ändere Passwort..."
    sudo sed -i "s/^PASSWORD=.*/PASSWORD=$NEW_PASSWORD/" "$CONFIG_FILE"
    
    echo "✅ Passwort geändert!"
    echo ""
    echo "📋 Neue Konfiguration:"
    NEW_PASSWORD_CHECK=$(grep "^PASSWORD=" "$CONFIG_FILE" | cut -d'=' -f2)
    echo "PASSWORD=$NEW_PASSWORD_CHECK"
    
    # Service neu starten
    echo ""
    echo "🔄 Starte Service neu..."
    sudo systemctl restart "$SERVICE_NAME"
    
    # Status prüfen
    sleep 3
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        echo "✅ Service läuft mit neuem Passwort!"
        echo ""
        echo "🌐 Dashboard-Zugang:"
        echo "URL: http://$(hostname -I | awk '{print $1}'):5000"
        echo "Passwort: $NEW_PASSWORD"
    else
        echo "❌ Service-Start fehlgeschlagen!"
        echo "Wiederherstelle Backup..."
        sudo cp "$CONFIG_FILE.backup."* "$CONFIG_FILE"
        sudo systemctl restart "$SERVICE_NAME"
        echo "Logs prüfen: sudo journalctl -u $SERVICE_NAME -f"
    fi
else
    echo "Passwort nicht geändert."
fi

echo ""
echo "📋 Nützliche Befehle:"
echo "- Service-Status: sudo systemctl status $SERVICE_NAME"
echo "- Logs anzeigen: sudo journalctl -u $SERVICE_NAME -f"
echo "- Service neu starten: sudo systemctl restart $SERVICE_NAME"
echo "- Konfiguration bearbeiten: sudo nano $CONFIG_FILE"
